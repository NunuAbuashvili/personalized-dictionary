from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import Throttled
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.mixins import (DestroyModelMixin, ListModelMixin,
                                   RetrieveModelMixin, UpdateModelMixin)
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from accounts.models import CustomUser, UserProfile
from .permissions import IsUserProfileOrReadOnly
from .serializers import (EmailSerializer, PasswordResetConfirmSerializer,
                          UserProfileSerializer, UserSignupSerializer)
from .utils import send_verification_email, generate_password_reset_token, get_user_from_token


@extend_schema(tags=['Accounts'])
class UserSignupAPIView(CreateAPIView):
    """
    API endpoint for user registration.

    Allows only non-authenticated users to create a new account.
    Sends a verification email after successful registration.
    """
    serializer_class = UserSignupSerializer
    permission_classes = (~IsAuthenticated,)

    def perform_create(self, serializer: UserSignupSerializer):
        """
        Create user and trigger verification email.

        Args:
            serializer (UserSignupSerializer): Validated user data.
        """
        user = serializer.save()
        name = self.request.data.get('first_name')
        subject = 'Verify Your Account'
        send_verification_email(user, name, subject)
        return Response(
            {'message': 'Check your email for verification.'},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['Accounts'])
class VerifyEmailAPIView(GenericAPIView):
    """
    API endpoint to verify user email address.

    Allows non-authenticated users to verify their email
    using a token sent during registration.
    """
    permission_classes = (~IsAuthenticated,)
    serializer_class = None

    def get(self, request: Request) -> Response:
        """
        Verify user email using provided token.

        Args:
            request (Request): HTTP request with token query parameter.

        Returns:
            Response: Status of email verification.
        """
        token = request.query_params.get('token')
        if not token:
            return Response(
                {"error": _("Token is missing.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_user_from_token(token)
        if not user.is_verified:
            user.is_verified = True
            user.save()
            return Response({"message": _("Email verified successfully!")}, status=status.HTTP_200_OK)
        return Response({"message": _("This email is already verified.")}, status=status.HTTP_200_OK)


@extend_schema(tags=['Accounts'])
class ResendVerificationEmailAPIView(APIView):
    """
    API endpoint to resent email verification link.

    Allows non-authenticated users to request a new
    verification email if their account is not verified.
    """
    permission_classes = (~IsAuthenticated,)
    serializer_class = EmailSerializer

    def post(self, request: Request) -> Response:
        """
        Resend verification email to unverified user.

        Args:
            request (Request): HTTP request with user email.

        Returns:
            Response: Status of verification email resend.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            name = user.first_name
            if user.is_verified:
                return Response(
                    {"message": _("This account is already verified.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subject = 'Resend Email Verification'
            send_verification_email(user, name, subject)

            return Response(
                {"message": _("Check your email for verification.")},
                status=status.HTTP_200_OK
            )

        except CustomUser.DoesNotExist:
            return Response(
                {"error": _("This account does not exist.")},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['Accounts'])
class PasswordResetRequestAPIView(APIView):
    """
    API endpoint for initiating password reset.

    Allows non-authenticated users to request a password
    reset link with rate limiting.
    """
    permission_classes = (~IsAuthenticated,)
    serializer_class = EmailSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'password_reset_request'

    def post(self, request: Request) -> Response:
        """
        Generate and send password reset link.

        Args:
            request (Request): HTTP request with user email.

        Returns:
            Response: Status of password reset request.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email)
            reset_token = generate_password_reset_token(user)
            reset_link = f"http://localhost:8000/api/account/reset-password?token={reset_token}"

            convert_to_html_content = render_to_string(
                "accounts/password-reset-email-api.html",
                context={"reset_link": reset_link},
            )
            plain_message = strip_tags(convert_to_html_content)

            email = EmailMultiAlternatives(
                subject='Reset Password',
                body=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[user.email],
            )
            email.attach_alternative(convert_to_html_content, "text/html")
            email.send()
            return Response({"message": "Check your email for password reset link."})

        except CustomUser.DoesNotExist:
            return Response(
                {"error": _("This account does not exist.")},
                status=status.HTTP_400_BAD_REQUEST
            )

    def throttled(self, request: Request, wait: int) -> Throttled:
        """
        Handle rate limit exceeded scenario.

        Args:
            request (Request): HTTP request.
            wait (int): Seconds to wait before next request.

        Returns:
            Throttled: Exception with wait time details.
        """
        raise Throttled(
            detail={"error": _("Too many requests. Please try again in %(wait)d seconds.") % {"wait": wait}}
        )


@extend_schema(tags=['Accounts'])
class PasswordResetConfirmAPIView(APIView):
    """
    API endpoint for confirming password reset.

    Allows non-authenticated users to reset password
    using a valid token with rate limiting.
    """
    permission_classes = (~IsAuthenticated,)
    serializer_class = PasswordResetConfirmSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'password_reset_confirm'

    def post(self, request: Request) -> Response:
        """
        Reset user password using provided token.

        Args:
            request (Request): HTTP request with new password and token.

        Returns:
            Response: Status of password reset.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data['new_password']
        token = request.query_params.get('token')
        user = get_user_from_token(token)
        user.set_password(new_password)
        user.save()
        return Response({"message": _("Password has been successfully changed.")})

    def throttled(self, request: Request, wait: int) -> Throttled:
        """
        Handle rate limit exceeded scenario.

        Args:
            request (Request): HTTP request.
            wait (int): Seconds to wait before next request.

        Raises:
            Throttled: Exception with wait time details.
        """
        raise Throttled(
            detail={"error": _("Too many requests. Please try again in %(wait)d seconds.") % {"wait": wait}}
        )


@extend_schema(tags=['Accounts'])
class UserProfileViewSet(ListModelMixin,
                        RetrieveModelMixin,
                        UpdateModelMixin,
                        DestroyModelMixin,
                        GenericViewSet):
    """
    ViewSet for user profile operations.

    Provides list, retrieve, update, and delete
    functionalities for user profiles with
    specific permission and queryset annotations.
    """
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsUserProfileOrReadOnly)

    def get_queryset(self):
        """Get annotated queryset of user profiles."""
        queryset = UserProfile.objects.select_related(
            'user'
        ).annotate(
            folder_count=Count('user__folders', distinct=True),
            dictionary_count=Count('user__folders__dictionaries', distinct=True),
            entry_count=Count('user__folders__dictionaries__entries', distinct=True),
        ).order_by('-dictionary_count')
        return queryset
