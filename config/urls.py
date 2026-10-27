"""
SignBox URL Configuration
"""
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import include, path
from django.views.generic import RedirectView


def root_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return render(request, "landing.html")


urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/images/favicon.svg", permanent=True)),
    path("", root_view, name="landing"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.workspaces.urls")),
    path("certificates/", include("apps.certificates.urls")),
    path("documents/", include("apps.documents.urls")),
    path("signing/", include("apps.signing.urls")),
    path("track/", include("apps.tracking.urls")),
    path("verify/", include("apps.verification.urls")),
    # Public sharing & verification routes (/d/<token>/, etc.)
    path("", include("apps.sharing.urls")),
]
