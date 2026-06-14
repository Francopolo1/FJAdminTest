"""
Session-based HTML authentication views for FJADMIN.

Views
──────────────────────────────────────────────────────────────────────────
LoginView                  GET/POST  /auth/login/
LogoutView                 GET/POST  /auth/logout/
ChangePasswordView         GET/POST  /auth/change-password/    (login required)
PasswordResetRequestView   GET/POST  /auth/password-reset/
PasswordResetDoneView      GET       /auth/password-reset/done/
PasswordResetConfirmView   GET/POST  /auth/password-reset/<uidb64>/<token>/
PasswordResetCompleteView  GET       /auth/password-reset/complete/
ProfileUpdateView          GET/POST  /auth/profile/            (login required)
RegisterView               GET/POST  /auth/register/           (guarded by ALLOW_REGISTRATION)
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    login, logout, update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View

from .forms import (
    LoginForm,
    ChangePasswordForm,
    PasswordResetRequestForm,
    SetNewPasswordForm,
    ProfileUpdateForm,
    RegisterForm,
)


def _next_url(request, fallback=None):
    nxt = request.POST.get("next") or request.GET.get("next") or ""
    if nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return fallback or getattr(settings, "LOGIN_REDIRECT_URL", "/dashboard/")


# ── LoginView ─────────────────────────────────────────────────────────────

class LoginView(View):
    template_name = "core/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return render(request, self.template_name, {"form": LoginForm(request=request)})

    def post(self, request):
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            nxt = request.POST.get("next") or settings.LOGIN_REDIRECT_URL
            messages.success(request, f"Welcome back, {user.full_name}!")
            return redirect(nxt)
        return render(request, self.template_name, {"form": form})



# ── LogoutView ────────────────────────────────────────────────────────────

class LogoutView(View):
    def post(self, request):
        if request.user.is_authenticated:
            messages.info(request, "You have been signed out.")
        logout(request)
        return redirect(getattr(settings, "LOGOUT_REDIRECT_URL", "/auth/login/"))

    def get(self, request):
        return self.post(request)


# ── ChangePasswordView ────────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class ChangePasswordView(View):
    template_name = "core/change_password.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form": ChangePasswordForm(user=request.user)
        })

    def post(self, request):
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            # Re-key the session so the user stays logged in
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect("auth:profile")
        return render(request, self.template_name, {"form": form})


# ── PasswordResetRequestView ──────────────────────────────────────────────

class PasswordResetRequestView(View):
    template_name = "core/password_reset_request.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return render(request, self.template_name, {"form": PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                self._send_reset_email(request, user)
            # Always redirect — never reveal whether email exists
            return redirect("auth:password_reset_done")
        return render(request, self.template_name, {"form": form})

    @staticmethod
    def _send_reset_email(request, user):
        token  = default_token_generator.make_token(user)
        uid    = urlsafe_base64_encode(force_bytes(user.pk))
        scheme = "https" if request.is_secure() else "http"
        link   = f"{scheme}://{request.get_host()}/auth/password-reset/{uid}/{token}/"

        body = render_to_string("core/email/password_reset.txt", {
            "user":         user,
            "link":         link,
            "expiry_hours": getattr(settings, "PASSWORD_RESET_TIMEOUT", 86400) // 3600,
        })
        send_mail(
            subject="Reset your FJADMIN password",
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@fjadmin.local"),
            recipient_list=[user.email],
            fail_silently=False,
        )


# ── PasswordResetDoneView ─────────────────────────────────────────────────

class PasswordResetDoneView(View):
    template_name = "core/password_reset_done.html"

    def get(self, request):
        return render(request, self.template_name)


# ── PasswordResetConfirmView ──────────────────────────────────────────────

class PasswordResetConfirmView(View):
    template_name = "core/password_reset_confirm.html"

    def _resolve(self, uidb64, token):
        from .models import AuthUser
        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = AuthUser.objects.get(pk=uid)
        except Exception:
            return None, False
        return user, default_token_generator.check_token(user, token)

    def get(self, request, uidb64, token):
        user, valid = self._resolve(uidb64, token)
        if not valid:
            return render(request, self.template_name, {"invalid_link": True})
        return render(request, self.template_name, {
            "form": SetNewPasswordForm(user=user),
            "uidb64": uidb64, "token": token,
        })

    def post(self, request, uidb64, token):
        user, valid = self._resolve(uidb64, token)
        if not valid:
            return render(request, self.template_name, {"invalid_link": True})
        form = SetNewPasswordForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Password reset successfully. You can now sign in.")
            return redirect("auth:password_reset_complete")
        return render(request, self.template_name, {
            "form": form, "uidb64": uidb64, "token": token,
        })


# ── PasswordResetCompleteView ─────────────────────────────────────────────

class PasswordResetCompleteView(View):
    template_name = "core/password_reset_complete.html"

    def get(self, request):
        return render(request, self.template_name)


# ── ProfileUpdateView ─────────────────────────────────────────────────────

@method_decorator(login_required, name="dispatch")
class ProfileUpdateView(View):
    template_name = "core/profile.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form": ProfileUpdateForm(user=request.user)
        })

    def post(self, request):
        form = ProfileUpdateForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("auth:profile")
        return render(request, self.template_name, {"form": form})


# ── RegisterView ──────────────────────────────────────────────────────────

class RegisterView(View):
    template_name = "core/register.html"

    def _allowed(self):
        return getattr(settings, "ALLOW_REGISTRATION", False)

    def get(self, request):
        if not self._allowed():
            messages.error(request, "Self-registration is not enabled.")
            return redirect("auth:login")
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        if not self._allowed():
            return redirect("auth:login")
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            if getattr(settings, "REQUIRE_APPROVAL", False):
                user.is_active = False
            user.save()
            if user.is_active:
                login(request, user)
                messages.success(request, f"Welcome, {user.full_name}! Your account has been created.")
                return redirect("/dashboard/")
            else:
                messages.info(request, "Your account is pending approval. You will be notified by email.")
                return redirect("auth:login")
        return render(request, self.template_name, {"form": form})
