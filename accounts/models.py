from django_countries.fields import CountryField
from PIL import Image

from typing import Any, Dict

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Count
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user manager for handling user/superuser creation operations.
    Extends Django's BaseUserManager to support email-based authentication.
    """
    def create_user(self,
                    email: str,
                    password: str,
                    **extra_fields: Dict[str, Any]) -> 'CustomUser':
        """
        Create and save a regular user with the given email and password.

        Args:
            email: User's email address
            password: User's password
            **extra_fields: Additional fields for the user model

        Returns:
            CustomUser: The created user instance.

        Raises:
            ValueError: If email is empty.
        """
        if not email:
            raise ValueError(_('The Email field should not be empty.'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self,
                         email: str,
                         password: str,
                         **extra_fields: Dict[str, Any]) -> 'CustomUser':
        """
        Create and save a superuser with the given email and password.

        Args:
            email: Superuser's email address
            password: Superuser's password
            **extra_fields: Additional fields for the user model

        Returns:
            CustomUser: The created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser is not True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser with additional fields.

    Attributes:
        email (EmailField): Unique email address
        date_of_birth (DateField): Date of birth
        country (CountryField): Country of residence
        is_verified (BooleanField): Whether the user is verified
    """
    email = models.EmailField(_('email address'), unique=True)
    is_verified = models.BooleanField(_('email verified'), default=False)
    slug = models.SlugField(_('slug'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.username)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.email

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    @property
    def languages(self):
        return ", ".join(
            language for language in self.folders
            .values_list('language__name', flat=True).distinct()
        )

    @classmethod
    def annotate_all_statistics(cls, queryset):
        return queryset.annotate(
            folder_count=Count('folders', distinct=True),
            dictionary_count=Count('folders__dictionaries', distinct=True),
            entry_count=Count('folders__dictionaries__entries', distinct=True),
        )


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    country = CountryField(verbose_name=_("country"), blank_label=_("Select country"))
    image = models.ImageField(upload_to='profile_images/', default='default.jpeg')

    def __str__(self):
        return f'{self.user.username} Profile'

    class Meta:
        verbose_name = _('User profile')
        verbose_name_plural = _('User profiles')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)
