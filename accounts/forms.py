from django import forms
from django.contrib.admin.templatetags.admin_list import search_form
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Custom form for user registration extending Django's UserCreationForm.
    """
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')
        placeholders = {
            'username': _('Enter your username'),
            'email': _('Enter your email'),
            'password1': _('Create a password'),
            'password2': _('Confirm a password')
        }

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        placeholders = self.Meta.placeholders

        for field in ['password1', 'password2']:
            self.fields[field].widget.attrs.update({'class': 'password'})

        for name, field in self.fields.items():
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]
            if name in ['password1', 'password2']:
                field.widget.attrs['class'] = 'password'


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that uses email instead of username.
    """
    username = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Enter your email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'password',
        'placeholder': 'Enter your password'
    }))


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with enhanced placeholder."""
    email = forms.EmailField(widget=forms.TextInput(
        attrs={'placeholder': 'Enter your email'})
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Custom password set form with descriptive placeholders."""
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Create a new password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}))


class UserUpdateForm(forms.ModelForm):
    """Form for updating basic user information."""
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name')


class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile details."""
    class Meta:
        model = UserProfile
        fields = ('country', 'date_of_birth', 'image')
        widgets = {
            'country': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        """
        Validate username uniqueness accross all users.

        Raises:
            ValidationError: If username already exists.
        """
        username = self.cleaned_data['username']
        if self.instance and self.instance.id:
            if User.objects.exclude(id=self.instance.user.id).filter(username=username).exists():
                raise forms.ValidationError(_('A user with this username already exists.'))
        return username
