from django.urls import path
from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.certificate_list_view, name="list"),
    path("upload/", views.certificate_upload_view, name="upload"),
    path("generate/", views.certificate_generate_view, name="generate"),
    path("<uuid:pk>/", views.certificate_detail_view, name="detail"),
    path("<uuid:pk>/toggle/", views.certificate_toggle_view, name="toggle"),
    path("<uuid:pk>/delete/", views.certificate_delete_view, name="delete"),
]
