from .settings_base import *  # noqa: F401,F403

# Development-specific settings
DEBUG = True

# Allow localhost during development
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Support adding an ngrok host via environment variable for local callback testing
NGROK_HOST = os.getenv('NGROK_HOST')
if NGROK_HOST:
    ALLOWED_HOSTS.append(NGROK_HOST)

# Use a simple console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery (optional)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)

# Additional dev-only settings can go here
