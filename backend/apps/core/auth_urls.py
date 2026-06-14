from django.urls import path
from .auth_views import (
    LoginView,
    LogoutView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    ProfileUpdateView,
    RegisterView,
)

app_name = "auth"

urlpatterns = [
    # Session auth
    path("login/",  LoginView.as_view(),  name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Profile (login required)
    path("profile/",         ProfileUpdateView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    # Password reset (4-step public flow)
    path("password-reset/",
         PasswordResetRequestView.as_view(),  name="password_reset"),
    path("password-reset/done/",
         PasswordResetDoneView.as_view(),     name="password_reset_done"),
    path("password-reset/<str:uidb64>/<str:token>/",
         PasswordResetConfirmView.as_view(),  name="password_reset_confirm"),
    path("password-reset/complete/",
         PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Optional self-registration
    path("register/", RegisterView.as_view(), name="register"),
]
