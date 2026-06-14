"""
All authentication and profile forms for the FJADMIN app.

Forms
──────────────────────────────────────────────────────────────────────────
LoginForm               — username + password with remember-me
ChangePasswordForm      — current password + new password x2
PasswordResetRequestForm— email lookup for reset link (no enumeration leak)
SetNewPasswordForm      — new password x2 used after clicking reset link
ProfileUpdateForm       — first_name, last_name, email update
RegisterForm            — new user self-registration (guarded by setting)
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


def _text_widget(placeholder="", autocomplete="off"):
    return forms.TextInput(attrs={
        "class": "input",
        "placeholder": placeholder,
        "autocomplete": autocomplete,
    })


def _email_widget(placeholder="you@example.com"):
    return forms.EmailInput(attrs={
        "class": "input",
        "placeholder": placeholder,
        "autocomplete": "email",
    })


def _pw_widget(placeholder="••••••••", autocomplete="current-password"):
    return forms.PasswordInput(attrs={
        "class": "input",
        "placeholder": placeholder,
        "autocomplete": autocomplete,
    })


# ── LoginForm ─────────────────────────────────────────────────────────────

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=_text_widget("Enter your username", "username"),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=_pw_widget(),
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Keep me signed in for 7 days",
        widget=forms.CheckboxInput(attrs={"class": "checkbox"}),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request    = request
        self._auth_user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get("username", "").strip()
        password = self.cleaned_data.get("password", "")
        if username and password:
            user = authenticate(self.request, username=username, password=password)
            if user is None:
                raise forms.ValidationError(
                    "Invalid username or password.", code="invalid_credentials"
                )
            if not user.is_active:
                raise forms.ValidationError(
                    "This account has been deactivated. Contact your administrator.",
                    code="inactive",
                )
            self._auth_user = user
        return self.cleaned_data

    def get_user(self):
        return self._auth_user


# ── ChangePasswordForm ────────────────────────────────────────────────────

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Current password",
        strip=False,
        widget=_pw_widget("Enter your current password"),
    )
    new_password = forms.CharField(
        label="New password",
        strip=False,
        widget=_pw_widget("At least 8 characters", autocomplete="new-password"),
        help_text="Minimum 8 characters. Cannot be entirely numeric.",
    )
    confirm_password = forms.CharField(
        label="Confirm new password",
        strip=False,
        widget=_pw_widget("Repeat new password", autocomplete="new-password"),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current = self.cleaned_data.get("current_password")
        if self.user and not self.user.check_password(current):
            raise forms.ValidationError(
                "Your current password is incorrect.", code="wrong_password"
            )
        return current

    def clean_new_password(self):
        new_pw = self.cleaned_data.get("new_password")
        if new_pw:
            try:
                validate_password(new_pw, user=self.user)
            except DjangoValidationError as exc:
                raise forms.ValidationError(exc.messages)
        return new_pw

    def clean(self):
        cleaned = super().clean()
        new_pw  = cleaned.get("new_password")
        confirm = cleaned.get("confirm_password")
        if new_pw and confirm and new_pw != confirm:
            self.add_error("confirm_password", "The two passwords do not match.")
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["new_password"])
        self.user.save(update_fields=["password"])
        return self.user


# ── PasswordResetRequestForm ──────────────────────────────────────────────

class PasswordResetRequestForm(forms.Form):
    """
    User enters their email. Always shows the done page regardless of
    whether the email exists — prevents account enumeration.
    """
    email = forms.EmailField(
        label="Email address",
        widget=_email_widget("Enter your account email"),
    )

    def clean_email(self):
        return self.cleaned_data["email"].lower().strip()

    def get_user(self):
        from .models import AuthUser
        try:
            return AuthUser.objects.get(
                email=self.cleaned_data["email"], is_active=True
            )
        except AuthUser.DoesNotExist:
            return None


# ── SetNewPasswordForm ────────────────────────────────────────────────────

class SetNewPasswordForm(forms.Form):
    """Used after clicking the password-reset link in the email."""
    new_password = forms.CharField(
        label="New password",
        strip=False,
        widget=_pw_widget("At least 8 characters", autocomplete="new-password"),
    )
    confirm_password = forms.CharField(
        label="Confirm new password",
        strip=False,
        widget=_pw_widget("Repeat new password", autocomplete="new-password"),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password(self):
        pw = self.cleaned_data.get("new_password")
        if pw:
            try:
                validate_password(pw, user=self.user)
            except DjangoValidationError as exc:
                raise forms.ValidationError(exc.messages)
        return pw

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password") != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "The two passwords do not match.")
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["new_password"])
        self.user.save(update_fields=["password"])
        return self.user


# ── ProfileUpdateForm ─────────────────────────────────────────────────────

class ProfileUpdateForm(forms.Form):
    first_name = forms.CharField(
        label="First name",
        max_length=150,
        widget=_text_widget("Jane", autocomplete="given-name"),
    )
    last_name = forms.CharField(
        label="Last name",
        max_length=150,
        widget=_text_widget("Smith", autocomplete="family-name"),
    )
    email = forms.EmailField(
        label="Email address",
        widget=_email_widget(),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        initial = kwargs.get("initial", {})
        if user and not initial:
            kwargs["initial"] = {
                "first_name": user.first_name,
                "last_name":  user.last_name,
                "email":      user.email,
            }
        super().__init__(*args, **kwargs)

    def clean_email(self):
        from .models import AuthUser
        email = self.cleaned_data["email"].lower().strip()
        qs    = AuthUser.objects.filter(email=email)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("This email is already used by another account.")
        return email

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name  = self.cleaned_data["last_name"].strip()
        self.user.email      = self.cleaned_data["email"]
        self.user.save(update_fields=["first_name", "last_name", "email"])
        return self.user


# ── RegisterForm ──────────────────────────────────────────────────────────

class RegisterForm(forms.Form):
    """
    Self-registration. Enable with ALLOW_REGISTRATION = True in settings.
    New accounts are inactive when REQUIRE_APPROVAL = True.
    """
    first_name = forms.CharField(
        label="First name",
        max_length=150,
        widget=_text_widget("Jane", autocomplete="given-name"),
    )
    last_name = forms.CharField(
        label="Last name",
        max_length=150,
        widget=_text_widget("Smith", autocomplete="family-name"),
    )
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=_text_widget("jsmith", autocomplete="username"),
        help_text="Letters, digits and @/./+/-/_ only.",
    )
    email = forms.EmailField(
        label="Email address",
        widget=_email_widget("jane@example.com"),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=_pw_widget("At least 8 characters", autocomplete="new-password"),
    )
    confirm_password = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=_pw_widget("Repeat password", autocomplete="new-password"),
    )

    def clean_username(self):
        from .models import AuthUser
        username = self.cleaned_data["username"].strip()
        if AuthUser.objects.filter(username=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        from .models import AuthUser
        email = self.cleaned_data["email"].lower().strip()
        if AuthUser.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        pw = self.cleaned_data.get("password")
        if pw:
            try:
                validate_password(pw)
            except DjangoValidationError as exc:
                raise forms.ValidationError(exc.messages)
        return pw

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("confirm_password"):
            self.add_error("confirm_password", "The two passwords do not match.")
        return cleaned

    def save(self):
        from .models import AuthUser
        user = AuthUser(
            username=self.cleaned_data["username"],
            first_name=self.cleaned_data["first_name"].strip(),
            last_name=self.cleaned_data["last_name"].strip(),
            email=self.cleaned_data["email"],
        )
        user.set_password(self.cleaned_data["password"])
        return user
