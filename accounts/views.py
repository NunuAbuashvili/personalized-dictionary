from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordResetConfirmView,
                                       PasswordResetView)
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from dictionary.models import Language
from leaderboard.models import UserStatistics
from .decorators import verified_email_required
from .forms import (CustomAuthenticationForm, CustomPasswordResetForm,
                    CustomSetPasswordForm, CustomUserCreationForm,
                    UserProfileUpdateForm, UserUpdateForm)
from .models import CustomUser, UserProfile
from .utils import send_verification_email, get_user_from_token


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


def resend_verification_email(request: HttpRequest, user_id: int) -> HttpResponse:
    """
    Resend verification email for unverified user.

    Args:
        request (HttpRequest): The HTTP request object.
        user_id (int): The ID of the user.

    Returns:
        HttpResponse: Redirect with success or error message.
    """
    user = get_object_or_404(CustomUser, id=user_id)

    if not user.is_verified:
        send_verification_email(user)
        messages.success(request, _('Verification email resent. Please check your inbox.'))
        return redirect('accounts:login')

    messages.error(request, 'Unable to resend verification email.')
    return redirect('accounts:login')


def verify_email(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    """
    Verify user email via token.

    Args:
        request (HttpRequest): The HTTP request object.
        uidb64 (str): Base64 encoded user ID.
        token (str): Verification token.

    Returns:
        HttpResponse: Redirect with verification status message.
    """
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


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view with custom form and templates.
    """
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password-reset.html'
    html_email_template_name = 'accounts/password-reset-email-django.html'
    email_template_name = 'accounts/password-reset-email-django.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Custom password reset confirmation view with custom form.
    """
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomLoginView(LoginView):
    """
    Extended login view with email verification check.
    """
    authentication_form = CustomAuthenticationForm
    template_name = 'accounts/login.html'

    def form_valid(self, form: CustomAuthenticationForm) -> HttpResponse:
        """
        Validate login form with email verification check.

        Args:
            form (CustomAuthenticationForm): The login form.

        Returns:
            HttpResponse: Redirect based on verification status.
        """
        user = form.get_user()
        if not user.is_verified:
            resend_link = reverse('accounts:resend_verification', kwargs={'user_id': user.id})
            resend_text = _('Resend verification email.')
            warning_message = mark_safe(
                _('Please verify your email before accessing this page. ') +
                f'<a href="{resend_link}" class="resend-link">{resend_text}</a>'
            )
            messages.warning(self.request, warning_message)
            return redirect('accounts:login')
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Determine login success redirect URL.

        Returns:
            str: URL to redirect after successful login.
        """
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse_lazy(
            'accounts:view_profile', 
            kwargs={'user_slug': self.request.user.slug}
        )


@login_required
@verified_email_required
def update_profile(request: HttpRequest, user_slug: str) -> HttpResponse:
    """
    Update user and profile information.

    Args:
        request (HttpRequest): The HTTP request object.
        user_slug (str): User's unique slug.

    Returns:
        HttpResponse: Profile update form or redirected response.
    """
    user = CustomUser.objects.get(slug=user_slug)
    profile = get_object_or_404(UserProfile, user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileUpdateForm(request.POST,
                                             request.FILES,
                                             instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Your account has been updated.'))
            return redirect('accounts:view_profile', user_slug=user.slug)
        else:
            messages.error(request, _('Please correct the errors below.'))

    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileUpdateForm(instance=profile)

    folder_languages = Language.objects.filter(
            folders__user = user
        ).distinct()

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'MEDIA_URL': settings.MEDIA_URL,
        'folder_languages': folder_languages,
    }

    return render(request, 'accounts/profile-update.html', context)


def view_user_profile(request: HttpRequest, user_slug: str) -> HttpResponse:
    """
    Display user profile details.

    Args:
        request (HttpRequest): The HTTP request object.
        user_slug (str): User's unique slug.

    Returns:
        HttpResponse: Rendered user profile page.
    """
    try:
        page_user = CustomUser.annotate_all_statistics(
            CustomUser.objects.filter(slug=user_slug)
        ).select_related('profile').get(slug=user_slug)
    except CustomUser.DoesNotExist:
        raise Http404(_('User does not exist'))

    try:
        profile = page_user.profile
    except Profile.DoesNotExist:
        profile = None

    folder_languages = Language.objects.filter(
            folders__user = page_user
        ).distinct()
    statistics = UserStatistics.objects.get(user=page_user)

    context = {
        'page_user': page_user,
        'profile': profile,
        'folder_languages': folder_languages,
        'statistics': statistics,
    }

    return render(request, 'accounts/profile.html', context)


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
