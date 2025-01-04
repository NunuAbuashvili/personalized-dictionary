from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, UserProfile


class UserSignupSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration that handles password validation and user creation.

    Fields: username, email, password, and password confirmation.
    Ensures passwords match and meet Django's password validation requirements.
    """
    password = serializers.CharField(
        label=_('Password'),
        write_only=True,
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        label=_('Confirm password'),
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'username': {'label': _('Username')},
            'email': {'label': _('Email')},
        }

    def validate(self, data):
        """
        Ensure passwords match and meet Django's password validation requirements.
        """
        password = data.get('password', '')
        password2 = data.get('password2', '')
        email = data.get('email', '')

        # Validate passwords
        validate_password(password)
        if password != password2:
            raise serializers.ValidationError(_("Two password fields do not match."))

        # Check for existing unverified user
        try:
            existing_user = CustomUser.objects.get(email=email)
            if not existing_user.is_verified:
                existing_user.delete()
            else:
                raise serializers.ValidationError(_("A user with this email already exists."))
        except CustomUser.DoesNotExist:
            pass

        return data

    def create(self, validated_data) -> CustomUser:
        """
        Create a new user instance with validated data.
        """
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(_("Two password fields do not match."))
        return data


class UserProfileSerializer(CountryFieldMixin, serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email', label=_('Email Address'), read_only=True)
    first_name = serializers.CharField(source='user.first_name', label=_('First Name'))
    last_name = serializers.CharField(source='user.last_name', label=_('Last Name'))
    folder_count = serializers.IntegerField(read_only=True)
    dictionary_count = serializers.IntegerField(read_only=True)
    entry_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'country', 'date_of_birth', 'image',
            'folder_count', 'dictionary_count', 'entry_count'
        )

    def update(self, instance, validated_data):
        """
        Update a UserProfile instance and its associated CustomUser.
        """
        user_data = validated_data.pop('user', {})

        # Update CustomUser instance
        user = instance.user
        user.username = user_data.get('username', user.username)
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()

        # Update UserProfile instance
        instance.country = validated_data.get('country', instance.country)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.save()

        return instance

    def validate_username(self, value):
        """
        Validate that the username is unique.
        """
        user = self.instance.user if self.instance else None
        if CustomUser.objects.exclude(pk=user.pk if user else None).filter(username=value).exists():
            raise serializers.ValidationError(_("A user with this username already exists."))
        return value
