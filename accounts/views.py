from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from .decorators import verified_email_required
from .forms import (CustomUserCreationForm,
                    CustomAuthenticationForm,
                    CustomPasswordResetForm,
                    CustomSetPasswordForm,
                    UserUpdateForm,
                    UserProfileUpdateForm
                    )
from .models import CustomUser, UserProfile


# Verification Email
def send_verification_email(user, name=None):
    subject = 'Verify Your Account'
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = f"http://localhost:8000/{reverse(
        'accounts:verify_email', kwargs={'uidb64': uidb64, 'token': token}
    )}"

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


def get_user_from_token(uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        return None

    if default_token_generator.check_token(user, token):
        return user

    return None


def resend_verification_email(request):
    if not request.user.is_verified:
        send_verification_email(request.user)
        messages.success(request, _('Verification email resent. Please check your inbox.'))
        return redirect('accounts:login')

    messages.error(request, 'Unable to resend verification email.')
    return redirect('accounts:login')


def verify_email(request, uidb64, token):
    user = get_user_from_token(uidb64, token)

    if user:
        if user.is_verified:
            messages.info(request, _('This email is already verified.'))
            return redirect('accounts:login')

        user.is_verified = True
        user.save()
        messages.success(request, _('Your email has been verified. You can now log in.'))
        return redirect('accounts:login')
    else:
        messages.error(request, _('The verification link is invalid or has expired.'))
        return redirect('accounts:login')


# Registration
def register(request: HttpRequest) -> HttpResponse:
    """
    Handle user registration.

    Args:
        request: The HTTP request object.

    Returns
        HttpResponse: Redirect to login page on success or render registration form.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            send_verification_email(
                user,
                name=form.cleaned_data.get('username'),
            )

            messages.success(request, 'Check your email for verification.')
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {"form": form})


# Password Reset
class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password-reset.html'
    html_email_template_name = 'accounts/password-reset-email-django.html'
    email_template_name = 'accounts/password-reset-email-django.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')


# Login
class CustomLoginView(LoginView):
    """
    Extends Django's LoginView to handle user login.
    """
    authentication_form = CustomAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        return reverse_lazy('accounts:view_profile', kwargs={'username': self.request.user.username})


# Update Profile
@login_required
@verified_email_required
def update_profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(request.POST,
                                             request.FILES,
                                             instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Your account has been updated.'))
            return redirect('accounts:view_profile', username=request.user.username)

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileUpdateForm(instance=request.user)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'accounts/profile-update.html', context)


# View Profile
@login_required
@verified_email_required
def view_user_profile(request, username):
    try:
        user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        raise Http404(_('User does not exist'))

    if not request.user.is_authenticated:
        messages.warning(request, _('You must be logged in to view profiles.'))
        return redirect('accounts:login')

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = None

    context = {
        'user': user,
        'profile': profile,
    }

    return render(request, 'accounts/profile.html', context)


# Logout
@login_required
def user_logout(request: HttpRequest) -> HttpResponse:
    """
    Handle user logout.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: Render the logout page.
    """
    logout(request)
    return redirect('accounts:login')