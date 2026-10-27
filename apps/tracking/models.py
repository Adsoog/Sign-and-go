import uuid
from django.db import models
from django.utils import timezone
from apps.documents.models import Document
from apps.sharing.models import ShareLink


class DocumentEvent(models.Model):
    """
    Chronological activity log for documents (web visits, downloads, and remote PDF requests).
    Strictly preserves raw event types without fabricating inferred opens.
    """
    EVENT_WEB_VISIT = "web_visit"
    EVENT_WEB_PREVIEW = "web_preview"
    EVENT_WEB_DOWNLOAD = "web_download"
    EVENT_PDF_RESOURCE_REQUEST = "pdf_resource_request"
    EVENT_SHARE_LINK_CREATED = "share_link_created"
    EVENT_SHARE_LINK_REVOKED = "share_link_revoked"

    EVENT_TYPE_CHOICES = [
        (EVENT_WEB_VISIT, "Visita web"),
        (EVENT_WEB_PREVIEW, "Previsualización"),
        (EVENT_WEB_DOWNLOAD, "Descarga"),
        (EVENT_PDF_RESOURCE_REQUEST, "Solicitud remota desde PDF"),
        (EVENT_SHARE_LINK_CREATED, "Enlace creado"),
        (EVENT_SHARE_LINK_REVOKED, "Enlace revocado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Documento",
    )
    share_link = models.ForeignKey(
        ShareLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name="Enlace asociado",
    )
    event_type = models.CharField("Tipo de evento", max_length=50, choices=EVENT_TYPE_CHOICES, db_index=True)
    occurred_at = models.DateTimeField("Fecha y hora", default=timezone.now, db_index=True)
    user_agent = models.CharField("User Agent", max_length=255, blank=True)
    ip_anonymized = models.CharField("IP Anonimizada", max_length=45, blank=True)
    request_metadata = models.JSONField("Metadatos de solicitud", default=dict, blank=True)

    class Meta:
        verbose_name = "Evento de documento"
        verbose_name_plural = "Eventos de documentos"
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"[{self.occurred_at.strftime('%Y-%m-%d %H:%M')}] {self.get_event_type_display()} en '{self.document.title}'"
