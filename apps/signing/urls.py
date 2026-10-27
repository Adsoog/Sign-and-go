from django.urls import path
from . import views

app_name = "signing"

urlpatterns = [
    path("<uuid:doc_id>/editor/", views.signing_editor_view, name="editor"),
    path("<uuid:doc_id>/execute/", views.signing_execute_view, name="execute"),
    path("<uuid:doc_id>/history/", views.signing_history_view, name="history"),
]
