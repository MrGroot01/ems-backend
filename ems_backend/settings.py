from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY     = os.environ.get('SECRET_KEY', 'ems-super-secret-key')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
DEBUG          = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS  = os.environ.get('ALLOWED_HOSTS', '*').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://ems-backend-5ptz.onrender.com',
    'https://ems-frontend-melon1x12-mrgroot01s-projects.vercel.app',
    'https://ems-frontend.vercel.app',
    'https://ems-pro.vercel.app',
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:8000',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'captcha',        # ← NEW
    'users',
    'employees',
    'attendance',
    'leaves',
    'tasks',
    'payroll',
    'notifications',
    'ai_assistant',
    'courses',    # ← add this
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF     = 'ems_backend.urls'
WSGI_APPLICATION = 'ems_backend.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# ── Database ───────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': None,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES':        ('Bearer',),
}

CORS_ALLOW_ALL_ORIGINS  = True
CORS_ALLOW_CREDENTIALS  = True
CORS_ALLOWED_ORIGINS = [
    'https://ems-backend-5ptz.onrender.com',
    'https://ems-frontend-melon1x12-mrgroot01s-projects.vercel.app',
    'https://ems-frontend.vercel.app',
    'https://ems-pro.vercel.app',
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:8000',
]

LANGUAGE_CODE      = 'en-us'
TIME_ZONE          = 'Asia/Kolkata'
USE_I18N           = True
USE_TZ             = True
STATIC_URL         = '/static/'
STATIC_ROOT        = BASE_DIR / 'staticfiles'
MEDIA_URL          = '/media/'
MEDIA_ROOT         = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Email → Brevo ──────────────────────────────────────────
EMAIL_BACKEND       = os.environ.get(
                        'EMAIL_BACKEND',
                        'django.core.mail.backends.smtp.EmailBackend'
                      )
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp-relay.brevo.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL       = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@emspro.com')
EMAIL_TIMEOUT       = 30

# ── CAPTCHA ────────────────────────────────────────────────
CAPTCHA_LENGTH           = 5
CAPTCHA_FONT_SIZE        = 36
CAPTCHA_IMAGE_SIZE       = (160, 55)
CAPTCHA_BACKGROUND_COLOR = '#f1f5f9'
CAPTCHA_FOREGROUND_COLOR = '#2563eb'
CAPTCHA_NOISE_FUNCTIONS  = (
    'captcha.helpers.noise_arcs',
    'captcha.helpers.noise_dots',
)
CAPTCHA_CHALLENGE_FUNCT  = 'captcha.helpers.random_char_challenge'
CAPTCHA_LETTER_ROTATION  = (-15, 15)

# ── Cache ──────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ems-otp-cache',
        'TIMEOUT':  300,
    }
}

# ── Logging ────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level':    'INFO',
    },
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'