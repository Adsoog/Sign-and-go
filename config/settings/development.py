"""
Development settings for SignBox.
"""
from .base import *  # noqa: F403

DEBUG = True

# Disable strict password validation in development if desired for testing speed
AUTH_PASSWORD_VALIDATORS = []

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
