from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.defaultfilters import strip_tags
from django.template.loader import render_to_string
from django.urls import reverse

from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts.models import CustomUser


def send_verification_email(user: CustomUser, name: str, subject: str):
    """
    Send a verification email to the user with a time-limited verification link.

    Args:
        user (CustomUser): The user to send the verification email to.
        name (str): User's first name to personalize the email.
        subject (str): Subject line of the email.

    Note:
        Generates a 15-minute valid verification token and sends an HTML email.
    """
    current_site = 'https://nunu29.pythonanywhere.com/'
    token = RefreshToken.for_user(user).access_token
    token.set_exp(lifetime=timedelta(minutes=15))
    verification_link = f"{current_site}{reverse('accounts:verify_email', kwargs={'uidb64': uidb64, 'token': token})}"

    html_content = render_to_string(
        "accounts/verification-email.html",
        context={"name": name, "verification_link": verification_link},
    )
    plain_message = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def generate_password_reset_token(user: CustomUser) -> str:
    """
    Generate a time-limited access token for password reset.

    Args:
        user (CustomUser): The user requesting password reset.

    Returns:
        str: A 15-minute valid access token.
    """
    token = RefreshToken.for_user(user)
    token.set_exp(lifetime=timedelta(minutes=15))
    return str(token.access_token)


def get_user_from_token(token: str) -> CustomUser:
    """
    Retrieve user from a valid access token.

    Args:
        token (str): Access token to validate.

    Returns:
        CustomUser: User associated with the token.

    Raises:
        Response: HTTP error responses for invalid or expired tokens.
    """
    try:
        payload = AccessToken(token)
        user_id = payload.get('user_id')
        user = CustomUser.objects.get(id=user_id)
        return user
    except (TokenError, InvalidToken):
        return Response(
            {"error": _("The verification link has expired or is invalid. Please request a new one.")},
            status=status.HTTP_400_BAD_REQUEST
        )
    except CustomUser.DoesNotExist:
        return Response(
            {"error": _("This account does not exist.")},
            status=status.HTTP_400_BAD_REQUEST
        )
