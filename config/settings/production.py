"""
Production settings for Sign & Go.
Configured for deployment on http://signandgo.amostudio.online (and HTTPS).
"""
import os
from .base import *  # noqa: F403

DEBUG = False

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Allow iframe previews of PDFs within the same origin (signandgo.amostudio.online)
X_FRAME_OPTIONS = "SAMEORIGIN"

# Trust proxy header when running behind Nginx / Cloudflare / Traefik
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SSL & HTTPS redirects (Can be enabled once SSL certificate is active)
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False").lower() in ("true", "1", "yes")
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")

# HSTS settings (active only when SECURE_SSL_REDIRECT is True)
if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0

