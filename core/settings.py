"""
Django settings for core project.

This file now acts as a compatibility shim that imports the development
settings by default. Production deployments should set DJANGO_SETTINGS_MODULE
to `core.settings_prod` or otherwise import the correct module.
"""

from .settings_dev import *
