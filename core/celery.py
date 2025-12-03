"""Minimal Celery app factory. If Celery isn't installed this file will still import
but attempting to access `app` will raise ImportError.
"""
from __future__ import annotations
import os

from django.conf import settings

try:
    from celery import Celery
except Exception:
    Celery = None


def make_celery(app_name: str = 'core'):
    if Celery is None:
        raise ImportError('Celery is not installed. Install celery to use background tasks.')

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    celery_app = Celery(app_name)
    celery_app.config_from_object('django.conf:settings', namespace='CELERY')
    celery_app.autodiscover_tasks()
    return celery_app


# create a celery app only if Celery is available
if Celery is not None:
    app = make_celery()  # type: ignore
else:
    app = None

