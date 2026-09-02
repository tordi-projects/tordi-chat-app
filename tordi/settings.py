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

# --- SMS / WhatsApp OTP gateway --------------------------------------------
# If Twilio credentials are set (as environment variables), OTP codes are
# sent as a real SMS or WhatsApp message. Otherwise Tordi falls back to
# printing the code to the console, so local development still works
# without a Twilio account. See accounts/views.py -> send_otp_sms().
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')

# For plain SMS: a Twilio phone number, e.g. "+15551234567".
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')

# For WhatsApp delivery instead of SMS: set this to "true" and provide a
# Twilio WhatsApp-enabled number (their sandbox number while testing, e.g.
# "+14155238886"). See README.md for the full walkthrough.
TWILIO_USE_WHATSAPP = os.environ.get('TWILIO_USE_WHATSAPP', 'false').lower() == 'true'
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', '')
