"""
Django settings for live_tracking_map project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
ADMINS = [("admin", "test@test.com")]
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://de23c507c2c14ccba388a15e5dbe1df6@o568590.ingest.sentry.io/5713793",
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "a()!xe(&n4@i(hrd=w*xs&v4f^t&7rw4z4(uz&8&2tuy9216j9"

SERVER_ROOT = "https://airsports.no"
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("MODE") == "dev"
ALLOWED_HOSTS = ["*"]

REDIS_GLOBAL_POSITIONS_KEY = "global_positions"
# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework.authtoken",
    "timezone_field",
    "webpack_loader",
    "bootstrap4",
    "drf_yasg",
    "solo",
    "guardian",
    "django_countries",
    "formtools",
    "phonenumber_field",
    "qr_code",
    "crispy_forms",
    "google_analytics",
    "channels",
    "display.apps.DisplayConfig",
    "firebase.apps.FirebaseConfig",
    "multiselectfield",
]
if os.environ.get("MODE") != "dev":
    INSTALLED_APPS.append("drf_firebase_auth")

PRODUCTION = os.environ.get("MODE") != "dev"


CRISPY_TEMPLATE_PACK = "bootstrap4"
GUARDIAN_MONKEY_PATCH = False
AUTH_USER_MODEL = "display.MyUser"

EMAIL_FROM = os.environ.get("AUTHEMAIL_DEFAULT_EMAIL_FROM") or "tracking@airsports.no"
EMAIL_BCC = os.environ.get("AUTHEMAIL_DEFAULT_EMAIL_BCC") or "tracking@airsports.no"

EMAIL_HOST = os.environ.get("AUTHEMAIL_EMAIL_HOST") or ""
EMAIL_PORT = os.environ.get("AUTHEMAIL_EMAIL_PORT") or 587
EMAIL_HOST_USER = os.environ.get("AUTHEMAIL_EMAIL_HOST_USER") or "<YOUR EMAIL_HOST_USER HERE>"
EMAIL_HOST_PASSWORD = os.environ.get("AUTHEMAIL_EMAIL_HOST_PASSWORD") or "<YOUR EMAIL_HOST_PASSWORD HERE>"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = "tracking@airsports.no"

DRF_FIREBASE_AUTH = {
    "FIREBASE_SERVICE_ACCOUNT_KEY": "/secret/airsports-firebase-admin.json",
    "FIREBASE_AUTH_EMAIL_VERIFICATION": True,
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "live_tracking_map.middleware.HandleKnownExceptionsMiddleware",
    # 'google_analytics.middleware.GoogleAnalyticsMiddleware',
]

ROOT_URLCONF = "live_tracking_map.urls"

CELERY_IMPORTS = "google_analytics.tasks"
LOGOUT_REDIRECT_URL = "/"
LOGIN_REDIRECT_URL = "/"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "live_tracking_map.wsgi.application"

WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "bundles/local/",  # end with slash
        "STATS_FILE": "/webpack-stats-local.json",
    }
}

# AUTH_PASSWORD_VALIDATORS = []

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # this is default
    "guardian.backends.ObjectPermissionBackend",
)

GOOGLE_ANALYTICS = {
    "google_analytics_id": "UA-12923426-5",
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "EXCEPTION_HANDLER": "live_tracking_map.django_exception_handler.exception_handler",
}
if os.environ.get("MODE") != "dev":
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"].append("drf_firebase_auth.authentication.FirebaseAuthentication")
# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

IS_UNIT_TESTING = any(s in sys.argv for s in ("test", "jenkins"))

# if IS_UNIT_TESTING:  # Use sqlite3 when running tests
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         }
#     }
# else:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "tracker",
        "USER": "tracker",
        "PASSWORD": "tracker",
        "HOST": "mysql",
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

STATIC_URL = "/static/"
STATIC_ROOT = "/static"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    "/assets",
]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(name)-15s: %(funcName)-15s %(levelname)-8s %(message)s",
            "datefmt": "%d/%m/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.WatchedFileHandler",
            "filename": "/logs/airports.log",
            "formatter": "standard",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
        "": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": True},
        "celery": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "asyncio": {
            "handlers": ["file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "aioredis": {
            "handlers": ["file", "console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": [
            "/tmp/docker/redis.sock" if PRODUCTION else "redis:6379",
        ],
        "TIMEOUT": None,
        "OPTIONS": {
            "DB": 1,
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "timeout": 20,
            },
            "MAX_CONNECTIONS": 1000,
            "PICKLE_VERSION": -1,
        },
    },
}

# celery
CELERY_BROKER_URL = "redis+socket:///tmp/docker/redis.sock" if PRODUCTION else "redis://redis:6379"
CELERY_RESULT_BACKEND = "redis+socket:///tmp/docker/redis.sock" if PRODUCTION else "redis://redis:6379"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"

ASGI_APPLICATION = "live_tracking_map.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": ["unix:/tmp/docker/redis.sock" if PRODUCTION else ("redis", 6379)],
            "capacity": 100,  # default 100
            "expiry": 30,  # default 60
        },
    }
}
