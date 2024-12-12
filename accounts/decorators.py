from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


def verified_email_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_verified:
            resend_link = reverse('accounts:resend_verification')
            warning_message = mark_safe(
                _('Please verify your email before accessing this page. ') +
                f'<a href="{resend_link}" class="resend-link">{_('Resend verification email.')}</a>'
            )
            messages.warning(request, warning_message)
            return redirect('accounts:login')

        return view_func(request, *args, **kwargs)
    return wrapper
