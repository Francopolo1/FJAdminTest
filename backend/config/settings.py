from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-secret-key")
DEBUG      = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = ["*"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    "https://*.up.railway.app",
]
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
    "anymail",
    # local
    "apps.core",
    "apps.workflows",
    "apps.checklists",
    "apps.compliance",
    "apps.financials",
    "apps.facilities",
    "apps.dashboards",
    "apps.notifications",
    "apps.enforcement",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
DATABASE_URL = config("DATABASE_URL", default="")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600),
    }
else:
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

# ── Media storage ──────────────────────────────────────────────────────────────
# Set R2_* env vars to store uploads in Cloudflare R2 (S3-compatible).
# Without them, files fall back to the local filesystem (dev only).
R2_ACCOUNT_ID        = config("R2_ACCOUNT_ID",        default="")
R2_ACCESS_KEY_ID     = config("R2_ACCESS_KEY_ID",     default="")
R2_SECRET_ACCESS_KEY = config("R2_SECRET_ACCESS_KEY", default="")
R2_BUCKET_NAME       = config("R2_BUCKET_NAME",       default="")
R2_PUBLIC_URL        = config("R2_PUBLIC_URL",        default="")  # e.g. https://pub-xxxx.r2.dev or custom domain

_use_r2 = all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_PUBLIC_URL])

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage" if _use_r2 else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if _use_r2:
    AWS_ACCESS_KEY_ID       = R2_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY   = R2_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = R2_BUCKET_NAME
    AWS_S3_ENDPOINT_URL     = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    AWS_S3_REGION_NAME      = "auto"   # required by R2
    AWS_S3_SIGNATURE_VERSION = "s3v4"  # required by R2
    AWS_S3_CUSTOM_DOMAIN    = R2_PUBLIC_URL.replace("https://", "").replace("http://", "").rstrip("/")
    AWS_S3_FILE_OVERWRITE   = False
    AWS_DEFAULT_ACL         = None     # R2 uses bucket-level public access, not per-object ACLs
    AWS_QUERYSTRING_AUTH    = False    # public bucket — no signed URLs needed
    MEDIA_URL  = R2_PUBLIC_URL.rstrip("/") + "/"
    MEDIA_ROOT = BASE_DIR / "media"  # unused when R2 active, kept for local fallback
else:
    MEDIA_URL  = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL          = "/auth/login/"
LOGIN_REDIRECT_URL = "/dashboards/"
LOGOUT_REDIRECT_URL = "/auth/login/"
ALLOW_REGISTRATION   = True   # set True to enable /auth/register/
REQUIRE_APPROVAL     = False   # set True to require admin approval for new accounts
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours
DEFAULT_FROM_EMAIL   = config("DEFAULT_FROM_EMAIL", default="noreply@fjadmin.local")
FRONTEND_BASE_URL    = config("FRONTEND_BASE_URL", default="http://localhost:5173")

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST       = config("EMAIL_HOST", default="")
EMAIL_PORT       = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER  = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS    = config("EMAIL_USE_TLS", default=True, cast=bool)

ANYMAIL = {
    "RESEND_API_KEY": config("RESEND_API_KEY", default=""),
}

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
