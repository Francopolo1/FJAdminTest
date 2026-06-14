from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-secret-key")
DEBUG      = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    # local
    "apps.core",
    "apps.workflows",
    "apps.checklists",
    "apps.compliance",
    "apps.financials",
    "apps.facilities",
    "apps.dashboards",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── SQL Server database ────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME":   config("DB_NAME",     default="FJADMINDBMODEL"),
        "HOST":   config("DB_HOST",     default="JOHNSON_OFFICE"),
        "PORT":   config("DB_PORT",     default="1433"),
        "USER":   config("DB_USER",     default="Mulesoft"),
        "PASSWORD": config("DB_PASSWORD", default="Mulesoft1"),
        "OPTIONS": {
            "driver": "ODBC Driver 17 for SQL Server",
            "extra_params": "TrustServerCertificate=yes",
        },
    }
}

AUTH_USER_MODEL = "core.AuthUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE     = "UTC"
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL          = "/auth/login/"
LOGIN_REDIRECT_URL = "/dashboards/"
LOGOUT_REDIRECT_URL = "/auth/login/"
ALLOW_REGISTRATION   = True   # set True to enable /auth/register/
REQUIRE_APPROVAL     = False   # set True to require admin approval for new accounts
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours
DEFAULT_FROM_EMAIL   = "noreply@fjadmin.local"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
FRONTEND_BASE_URL = "http://localhost:5173"

# ── DRF ───────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "PAGE_SIZE": 20,
}

# ── JWT ───────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME":  "HTTP_AUTHORIZATION",
    "USER_ID_FIELD":     "id",
    "USER_ID_CLAIM":     "user_id",
}

# ── CORS ──────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
""" CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://127.0.0.1:8000"
).split(",") """
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization",
    "content-type", "dnt", "origin", "user-agent",
    "x-csrftoken", "x-requested-with",
]

# ── Celery ────────────────────────────────────────────────────────────────
CELERY_BROKER_URL     = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_TIMEZONE       = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    "escalate-sla-breaches": {
        "task": "apps.workflows.tasks.escalate_sla_breaches",
        "schedule": timedelta(minutes=15),
    },
    "dispatch-pending-notifications": {
        "task": "apps.notifications.tasks.dispatch_pending_notifications",
        "schedule": timedelta(minutes=5),
    },
    "mark-overdue-tasks": {
        "task": "apps.workflows.tasks.mark_overdue_tasks",
        "schedule": timedelta(minutes=15),
    },
}

# ── Box.com (Client Credentials Grant / service account) ────────────────────
BOX_CLIENT_ID       = config("BOX_CLIENT_ID", default="")
BOX_CLIENT_SECRET   = config("BOX_CLIENT_SECRET", default="")
BOX_ENTERPRISE_ID   = config("BOX_ENTERPRISE_ID", default="")
BOX_PARENT_FOLDER_ID = config("BOX_PARENT_FOLDER_ID", default="0")
