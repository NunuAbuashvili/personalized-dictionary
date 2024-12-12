from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers

from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, UserProfile


class UserSignupSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration that handles password validation and user creation.

    Fields: username, email, password, password confirmation, country.
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
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password2')
        extra_kwargs = {
            'username': {'label': _('Username')},
            'email': {'label': _('Email')},
            'first_name': {'label': _('First Name')},
            'last_name': {'label': _('Last Name')},
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
            print("User already exists:", existing_user)
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
            country=validated_data['country'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
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
    email = serializers.EmailField(source='user.email', read_only=True, label=_('Email Address'))
    first_name = serializers.CharField(source='user.first_name', read_only=True, label=_('First Name'))
    last_name = serializers.CharField(source='user.last_name', read_only=True, label=_('Last Name'))

    class Meta:
        model = UserProfile
        fields = ('id', 'email', 'first_name', 'last_name', 'country', 'date_of_birth', 'image')
