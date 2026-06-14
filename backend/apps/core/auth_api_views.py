"""
JSON API authentication views for the React SPA.

Views
──────────────────────────────────────────────────────────────────────────
RegisterAPIView              POST  /api/auth/register/
PasswordResetRequestAPIView  POST  /api/auth/password-reset/
PasswordResetConfirmAPIView  POST  /api/auth/password-reset/confirm/
"""

from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AuthUser
from .serializers import (
    AuthUserSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not getattr(settings, "ALLOW_REGISTRATION", False):
            return Response({"detail": "Self-registration is not enabled."}, status=status.HTTP_403_FORBIDDEN)

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if getattr(settings, "REQUIRE_APPROVAL", False):
            user.is_active = False
            user.save()
            return Response(
                {"detail": "Your account has been created and is pending approval."},
                status=status.HTTP_201_CREATED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": AuthUserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = AuthUser.objects.get(email__iexact=email, is_active=True)
        except AuthUser.DoesNotExist:
            user = None

        if user:
            self._send_reset_email(user)

        # Always return 200 — never reveal whether the email exists.
        return Response({"detail": "If an account exists for that email, a reset link has been sent."})

    @staticmethod
    def _send_reset_email(user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        link = f"{settings.FRONTEND_BASE_URL}/reset-password/{uid}/{token}"

        body = render_to_string("core/email/password_reset.txt", {
            "user": user,
            "link": link,
            "expiry_hours": getattr(settings, "PASSWORD_RESET_TIMEOUT", 86400) // 3600,
        })
        send_mail(
            subject="Reset your FJADMIN password",
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@fjadmin.local"),
            recipient_list=[user.email],
            fail_silently=False,
        )


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset successfully. You can now sign in."})
