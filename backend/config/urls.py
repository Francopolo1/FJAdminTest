from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.static import serve as serve_static
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import cache_control
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from apps.core.serializers import EmailTokenObtainPairView
from apps.core.auth_api_views import (
    PasswordResetConfirmAPIView,
    PasswordResetRequestAPIView,
    RegisterAPIView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Root redirect
    path("", RedirectView.as_view(url="/dashboards/", permanent=False)),
    path("accounts/profile/", RedirectView.as_view(url="/dashboards/", permanent=False)),
    # Session HTML auth
    path("auth/", include("apps.core.auth_urls", namespace="auth")),
    # JWT API
    path("api/auth/login/",   EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(),         name="token_refresh"),
    path("api/auth/logout/",  TokenBlacklistView.as_view(),        name="token_blacklist"),
    path("api/auth/register/", RegisterAPIView.as_view(), name="api_register"),
    path("api/auth/password-reset/", PasswordResetRequestAPIView.as_view(), name="api_password_reset"),
    path("api/auth/password-reset/confirm/", PasswordResetConfirmAPIView.as_view(), name="api_password_reset_confirm"),
    # REST API
    path("api/core/",        include("apps.core.urls")),
    path("api/workflows/",   include("apps.workflows.urls")),
    path("api/checklists/",  include("apps.checklists.urls")),
    path("api/compliance/",  include("apps.compliance.urls")),
    path("api/financials/",  include("apps.financials.urls")),
    #path("api/facilities/",  include("apps.facilities.urls")),
    # HTML dashboards
    path("dashboards/",       include("apps.dashboards.urls", namespace="dashboards")),
]

if settings.DEBUG:
    media_serve = cache_control(no_store=True)(xframe_options_exempt(serve_static))
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            media_serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
