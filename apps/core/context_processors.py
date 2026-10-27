from django.conf import settings


def signbox_globals(request):
    """
    Exposes global variables to all Django templates.
    """
    base_url = getattr(settings, "SIGNANDGO_BASE_URL", getattr(settings, "SIGNBOX_BASE_URL", "http://localhost:8000"))
    return {
        "APP_NAME": "Sign & Go",
        "SIGNBOX_VERSION": "1.0.0",
        "SIGNBOX_BASE_URL": base_url,
        "SIGNANDGO_BASE_URL": base_url,
        "workspace": getattr(request, "workspace", None),
    }
