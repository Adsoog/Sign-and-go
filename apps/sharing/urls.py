from django.urls import path
from . import views

app_name = "sharing"

urlpatterns = [
    path("document/<uuid:doc_id>/create/", views.create_link_view, name="create"),
    path("link/<uuid:link_id>/created/<str:raw_token>/", views.link_created_view, name="link_created"),
    path("link/<uuid:link_id>/revoke/", views.revoke_link_view, name="revoke"),
    path("d/<str:token>/", views.public_verify_view, name="public_verify"),
    path("d/<str:token>/preview/", views.public_stream_pdf_view, name="public_preview"),
    path("d/<str:token>/download/", views.public_download_pdf_view, name="public_download"),
]
