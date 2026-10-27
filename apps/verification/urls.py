from django.urls import path
from . import views

app_name = "verification"

urlpatterns = [
    path("compare/", views.compare_tool_view, name="compare"),
]
