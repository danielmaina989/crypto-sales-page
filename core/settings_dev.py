from .settings_base import *  # noqa: F401,F403

# Development-specific settings
DEBUG = True

# Allow localhost during development
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Use a simple console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Additional dev-only settings can go here
