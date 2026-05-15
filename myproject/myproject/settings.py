"""
Django settings for myproject project.
"""

from pathlib import Path
import environ, os

# ======================
# Base
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY", default="dev-secret-change-me")

ALLOWED_HOSTS = ["*"]

# =====================================================
# 🔥 FIX: CSRF Trusted Origins (للفتح من الموبايل)
# =====================================================
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://192.168.1.2:8000",   # الـ IP اللي ظهر في اللوج
    "http://192.168.1.9:8000",   # الـ IP الخاص بجهازك
    "https://*.ngrok-free.app",  # عشان لو استخدمت Ngrok للكاميرا
]

# ======================
# Applications
# ======================
INSTALLED_APPS = [
    "daphne",              # لازم أول واحد

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "channels",
    "rest_framework",

    # Local apps
    "accounts.apps.AccountsConfig",
    "core",
    "chat",
    "api",
]

# ======================
# Middleware
# ======================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ======================
# URLs / Templates
# ======================
ROOT_URLCONF = "myproject.urls"

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
                "core.context_processors.asl_sets",
            ],
        },
    },
]

# ======================
# WSGI / ASGI
# ======================
WSGI_APPLICATION = "myproject.wsgi.application"
ASGI_APPLICATION = "myproject.asgi.application"

# ======================
# Database (PostgreSQL)
# ======================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sign_language_dev",
        "USER": "postgres",
        "PASSWORD": "Mm437437*",
        "HOST": "localhost",
        "PORT": 5432,
    }
}

# ======================
# Channels (Redis / Memurai)
# ======================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',            # الكود الجديد للدخول بالإيميل
    'django.contrib.auth.backends.ModelBackend', # الكود الأصلي
]

# ======================
# Auth / Passwords
# ======================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# ======================
# Internationalization
# ======================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ======================
# Static / Media
# ======================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ======================
# Email
# ======================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# إعدادات الإيميل
EMAIL_HOST_USER = 'mohamedalo437@gmail.com' 
EMAIL_HOST_PASSWORD = 'danj tawq uqys peah' 

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER