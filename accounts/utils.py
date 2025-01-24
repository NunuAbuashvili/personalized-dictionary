from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from accounts.models import CustomUser


def send_verification_email(user: CustomUser, name=None):
    """
    Send email verification link to user.

    Args:
        user (CustomUser): User to send verification email to.
        name (str, optional): Name to use in email. Defaults to username.
    """
    current_site = 'https://nunu29.pythonanywhere.com/'
    subject = 'Verify Your Account'
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

    verification_link = f"{current_site}{reverse('accounts:verify_email', kwargs={'uidb64': uidb64, 'token': token})}"

    html_content = render_to_string(
        "accounts/verification-email.html",
        context={
            "name": name or user.username,
            "verification_link": verification_link
        },
    )
    plain_message = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        to=(user.email,),
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def get_user_from_token(uidb64: str, token: str) -> CustomUser:
    """
    Retrieve user from verification token.

    Args:
        uidb64 (str): Base64 encoded user ID.
        token (str): Verification token.

    Returns:
        CustomUser of None: CustomUser instance if token is valid, else None.
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        return None

    if default_token_generator.check_token(user, token):
        return user

    return None
