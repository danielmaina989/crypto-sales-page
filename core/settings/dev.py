from .base import *
import os

# Development-specific settings
DEBUG = True

# Allow localhost during development
ALLOWED_HOSTS = ['*']

# Support adding an ngrok host via environment variable for local callback testing
NGROK_HOST = os.getenv('NGROK_HOST')
if NGROK_HOST:
    ALLOWED_HOSTS.append(NGROK_HOST)

# Use a simple console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Additional dev-only settings can go here
