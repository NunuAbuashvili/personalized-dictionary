from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import Throttled
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.mixins import (ListModelMixin, UpdateModelMixin,
                                   DestroyModelMixin, RetrieveModelMixin)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, UserProfile
from .permissions import IsUserProfileOrReadOnly
from .serializers import (UserSignupSerializer,
                          EmailSerializer,
                          PasswordResetConfirmSerializer,
                          UserProfileSerializer)


def send_verification_email(user, name, subject):
    token = RefreshToken.for_user(user).access_token
    token.set_exp(lifetime=timedelta(minutes=15))
    verification_link = f"https://{current_site.domain}{reverse('accounts:verify_email', kwargs={'uidb64': uidb64, 'token': token})}"

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


def generate_password_reset_token(user):
    token = RefreshToken.for_user(user)
    token.set_exp(lifetime=timedelta(minutes=15))
    return str(token.access_token)


def get_user_from_token(token):
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


@extend_schema(tags=['Accounts'])
class UserSignupAPIView(CreateAPIView):
    """
    API endpoint that allows users to register.
    Only non-authenticated users can access this endpoint.
    """
    serializer_class = UserSignupSerializer
    permission_classes = (~IsAuthenticated,)

    def perform_create(self, serializer):
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
    permission_classes = (~IsAuthenticated,)
    serializer_class = None

    def get(self, request):
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
    permission_classes = (~IsAuthenticated,)
    serializer_class = EmailSerializer

    def post(self, request):
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
    permission_classes = (~IsAuthenticated,)
    serializer_class = EmailSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'password_reset_request'

    def post(self, request):
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

    def throttled(self, request, wait):
        raise Throttled(
            detail={"error": _("Too many requests. Please try again in %(wait)d seconds.") % {"wait": wait}}
        )


@extend_schema(tags=['Accounts'])
class PasswordResetConfirmAPIView(APIView):
    permission_classes = (~IsAuthenticated,)
    serializer_class = PasswordResetConfirmSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'password_reset_confirm'

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data['new_password']
        token = request.query_params.get('token')
        user = get_user_from_token(token)
        user.set_password(new_password)
        user.save()
        return Response({"message": _("Password has been successfully changed.")})

    def throttled(self, request, wait):
        raise Throttled(
            detail={"error": _("Too many requests. Please try again in %(wait)d seconds.") % {"wait": wait}}
        )


@extend_schema(tags=['Accounts'])
class UserProfileViewSet(ListModelMixin,
                        RetrieveModelMixin,
                        UpdateModelMixin,
                        DestroyModelMixin,
                        GenericViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsUserProfileOrReadOnly)

    def get_queryset(self):
        queryset = UserProfile.objects.select_related(
            'user'
        ).annotate(
            folder_count=Count('user__folders', distinct=True),
            dictionary_count=Count('user__folders__dictionaries', distinct=True),
            entry_count=Count('user__folders__dictionaries__entries', distinct=True),
        ).order_by('-dictionary_count')
        return queryset
