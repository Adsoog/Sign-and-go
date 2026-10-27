from django.urls import path
from . import views

app_name = "tracking"

urlpatterns = [
    path("pdf/<str:token>/beacon.png", views.pdf_remote_beacon_view, name="beacon"),
    path("document/<uuid:doc_id>/events/", views.document_events_view, name="document_events"),
]
