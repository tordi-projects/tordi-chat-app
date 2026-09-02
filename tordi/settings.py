import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file if python-dotenv is installed and the file exists.
# This lets you keep Twilio credentials (or any secret) out of settings.py
# entirely — put them in a .env file at the project root instead, and
# never commit that file (see .env.example).
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

# SECURITY WARNING: change this before deploying to production!
SECRET_KEY = 'django-insecure-CHANGE-ME-BEFORE-DEPLOYING'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'chat',
    'status',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tordi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tordi.wsgi.application'

# Real-time-ish chat: the room page polls a JSON endpoint every couple of
# seconds instead of using WebSockets. This is intentional — it means
# Tordi runs on plain WSGI hosting (PythonAnywhere, most shared hosts,
# etc.) with zero extra infrastructure. See chat/views.py: poll_messages.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'inbox'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- SMS / WhatsApp gateway (optional, not used by the core login flow) ---
# Registration/login now happens by email (see below). Twilio is left wired
# up here only in case you want to add real SMS features later (e.g.
# verifying a linked phone number, or notification texts).
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')
TWILIO_USE_WHATSAPP = os.environ.get('TWILIO_USE_WHATSAPP', 'false').lower() == 'true'
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', '')

# --- Email (used for account verification/login codes) ---------------------
# Defaults to printing emails to the console, so registration/login work
# out of the box in dev with zero setup. Set EMAIL_HOST_USER (and the
# other EMAIL_* vars below) to send real email — see .env.example and the
# README for a Gmail/SendGrid walkthrough. If EMAIL_HOST_USER is present,
# Tordi automatically switches to the real SMTP backend.
_default_email_backend = (
    'django.core.mail.backends.smtp.EmailBackend'
    if os.environ.get('EMAIL_HOST_USER')
    else 'django.core.mail.backends.console.EmailBackend'
)
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', _default_email_backend)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Tordi <no-reply@tordi.app>')
