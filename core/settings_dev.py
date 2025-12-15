from .settings_base import *  # noqa: F401,F403
from urllib.parse import urlparse
import os

# Development-specific settings
DEBUG = True

# Base allowed hosts
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = []

# NGROK integration
NGROK_HOST = os.getenv('NGROK_HOST', '').strip()

if NGROK_HOST:
    # Remove protocol if accidentally included
    parsed = urlparse(NGROK_HOST)
    host = parsed.netloc or parsed.path  # netloc if scheme present, else path
    host = host.strip().rstrip('/')
    if host and host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)
    # CSRF requires https:// prefix
    origin = f'https://{host}'
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Allow common dev tunnel domains (accept any subdomain on these during development)
# Leading-dot entries allow subdomains (e.g. subphrenic-tonda-hipper.ngrok-free.dev)
for dev_tld in ('.ngrok-free.dev', '.ngrok.io'):
    if dev_tld not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(dev_tld)

# Optional: Environment-based extra CSRF origins
_env_csrf = os.getenv('CSRF_TRUSTED_ORIGINS')
if _env_csrf:
    for h in [h.strip() for h in _env_csrf.split(',') if h.strip()]:
        if h not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(h)

# Development convenience: allow wildcard hosts if explicitly enabled via env var
# This avoids DisallowedHost during development when using dynamic tunnels like ngrok.
if os.getenv('DEV_ALLOW_ALL_HOSTS', '').lower() in ('1', 'true'):
    if '*' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('*')

# If DEBUG, print resolved host config to stdout to aid troubleshooting
if DEBUG:
    try:
        print('DEV SETTINGS: ALLOWED_HOSTS=', ALLOWED_HOSTS)
        print('DEV SETTINGS: CSRF_TRUSTED_ORIGINS=', CSRF_TRUSTED_ORIGINS)
    except Exception:
        pass

# Use a simple console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery configuration (optional)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)

# Additional dev-only settings can go here

# After login, redirect to dashboard by default in dev
LOGIN_REDIRECT_URL = '/dashboard/'

# Best-practice: after logout redirect to the login page (named URL 'login')
# Using the view-name here is flexible: Django will resolve it via resolve_url
LOGOUT_REDIRECT_URL = 'login'
