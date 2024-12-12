from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.urls import path, include

from . import views


app_name = 'accounts_api'

router = routers.DefaultRouter()
router.register(r'profile', views.UserProfileViewSet, basename='profile')


urlpatterns = [
    path('', include(router.urls)),
    path('signup/', views.UserSignupAPIView.as_view(), name='signup'),
    path('verify-email/', views.VerifyEmailAPIView.as_view(), name='verify_email'),
    path('resend-verification-email', views.ResendVerificationEmailAPIView.as_view(), name='resend_verification_email'),
    path('reset-password-request', views.PasswordResetRequestAPIView.as_view(), name='reset_password_request'),
    path('reset-password', views.PasswordResetConfirmAPIView.as_view(), name='reset_password'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
