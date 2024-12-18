from django.contrib.auth.views import (
    PasswordResetDoneView,
    PasswordResetCompleteView
)
from django.urls import path, include

from . import views

app_name = 'accounts'


urlpatterns = [
    path('signup/', views.register, name='register'),
    path('signin/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-email/<str:uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='accounts/password-reset-done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(
        template_name='accounts/password-reset-confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(
        template_name='accounts/password-reset-complete.html'
    ),name='password_reset_complete'),
    path('profile/<slug:user_slug>/update/', views.update_profile, name='update_profile'),
    path('profile/<slug:user_slug>/', views.view_user_profile, name='view_profile'),
]
