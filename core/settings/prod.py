from .base import *  # noqa: F401,F403
import os

# Production-specific settings
DEBUG = False

# Example: read allowed hosts from environment variable (comma-separated)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

# It's highly recommended to set SECRET_KEY and other sensitive values via env vars in production.
# DATABASES can be overridden here for production (Postgres, etc.)

# Secure proxy and SSL settings (adjust depending on deployment)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Additional production-specific hardening can go here
