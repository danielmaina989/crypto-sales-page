"""
Base Django settings for the project. This file contains common settings used
by both development and production configuration modules.
"""
from pathlib import Path
import os

# Load .env file (simple loader, no external dependency) if present in project root
BASE_DIR = Path(__file__).resolve().parent.parent
_env_path = BASE_DIR / '.env'
if _env_path.exists():
    try:
        with _env_path.open() as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # don't override existing environment variables
                os.environ.setdefault(key, val)
    except Exception:
        # fail gracefully; settings will fall back to defaults
        pass

# SECURITY
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-y79d$%%1y+6d#=(2uq*5v3j8_kt-lq%!(iw$9=3#0+dy@@hb2p')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes')

# Allow localhost and testserver for programmatic tests
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # local apps
    'frontend',
    'payments',
    'users',
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / 'frontend' / 'static' ]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# MPESA configuration (read from environment or .env)
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
MPESA_ENV = os.getenv('MPESA_ENV', 'sandbox')
MPESA_SIMULATE = os.getenv('MPESA_SIMULATE', '0').lower() in ('1', 'true', 'yes')

# MPESA polling configuration
# M-Pesa sandbox allows ~5 requests per 60 seconds. Set delays and max attempts accordingly.
# Default: 12s delay with 40 attempts = ~480s total window (respects rate limit when spread)
MPESA_POLL_DELAY_SECONDS = int(os.getenv('MPESA_POLL_DELAY_SECONDS', '12'))
MPESA_POLL_MAX_ATTEMPTS = int(os.getenv('MPESA_POLL_MAX_ATTEMPTS', '40'))

# MPESA rate limiting (distributed across all workers)
# M-Pesa sandbox: 5 requests per 60 seconds (with 1 request max burst)
# Use 1.2x safety factor: allow 4 requests per 60 seconds
MPESA_RATE_LIMIT_REQUESTS = int(os.getenv('MPESA_RATE_LIMIT_REQUESTS', '4'))
MPESA_RATE_LIMIT_PERIOD = int(os.getenv('MPESA_RATE_LIMIT_PERIOD', '60'))
