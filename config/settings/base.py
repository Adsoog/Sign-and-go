"""
Django settings for SignBox project.
Base settings shared by development and production.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file automatically
env_path = BASE_DIR / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-signbox-default-dev-key-change-in-production-123456789"
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

PROJECT_APPS = [
    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.workspaces.apps.WorkspacesConfig",
    "apps.certificates.apps.CertificatesConfig",
    "apps.documents.apps.DocumentsConfig",
    "apps.signing.apps.SigningConfig",
    "apps.sharing.apps.SharingConfig",
    "apps.tracking.apps.TrackingConfig",
    "apps.verification.apps.VerificationConfig",
    "apps.audit.apps.AuditConfig",
]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "apps.workspaces.middleware.WorkspaceMiddleware",
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
                "apps.core.context_processors.signbox_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database
# Default: Clean, fast SQLite for local development. Supports PostgreSQL via DATABASE_URL.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")

if DATABASE_URL.startswith("sqlite"):
    sqlite_path = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    if not sqlite_path or sqlite_path == ":memory:":
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / sqlite_path,
            }
        }
else:
    # Basic URL parsing for postgresql://user:password@host:port/dbname
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "",
            "PORT": parsed.port or 5432,
        }
    }

# Custom User Model (Defined before first migration)
AUTH_USER_MODEL = "accounts.User"

# Authentication redirects
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "es-es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media & Private Storage (Private files NEVER served directly via nginx/apache)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_STORAGE_ROOT = BASE_DIR / "private_storage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# SignBox Specific Security & Storage Settings
SIGNBOX_ENCRYPTION_KEY = os.environ.get(
    "SIGNBOX_ENCRYPTION_KEY",
    "_MUoKJwLLy2tWngwS9ycJhB26l_04W89DOjQacBty0k="
)
SIGNBOX_BASE_URL = os.environ.get("SIGNBOX_BASE_URL", "http://localhost:8000").rstrip("/")

# Upload limits
MAX_DOCUMENT_SIZE_BYTES = int(os.environ.get("MAX_DOCUMENT_SIZE_BYTES", 25 * 1024 * 1024))      # 25 MB
MAX_CERTIFICATE_SIZE_BYTES = int(os.environ.get("MAX_CERTIFICATE_SIZE_BYTES", 10 * 1024 * 1024)) # 10 MB

# Ensure local storage directories exist
os.makedirs(PRIVATE_STORAGE_ROOT / "certificates", exist_ok=True)
os.makedirs(PRIVATE_STORAGE_ROOT / "documents" / "sources", exist_ok=True)
os.makedirs(PRIVATE_STORAGE_ROOT / "documents" / "signed", exist_ok=True)
