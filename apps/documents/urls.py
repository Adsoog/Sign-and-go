from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    path("", views.document_list_view, name="list"),
    path("upload/", views.document_upload_view, name="upload"),
    path("<uuid:pk>/", views.document_detail_view, name="detail"),
    path("<uuid:pk>/download/<str:file_type>/", views.document_download_view, name="download"),
    path("<uuid:pk>/file/<str:file_type>/", views.document_view_file, name="view_file"),
    path("<uuid:pk>/delete/", views.document_delete_view, name="delete"),
]
