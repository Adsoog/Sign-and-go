import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.documents.models import Document


class ShareLink(models.Model):
    """
    Public sharing and verification link for a document.
    Stores only the SHA-256 hash of the secret access token.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="share_links",
        verbose_name="Documento",
    )
    token_hash = models.CharField("Hash SHA-256 del token", max_length=64, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_share_links",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    expires_at = models.DateTimeField("Expira el", null=True, blank=True)
    revoked_at = models.DateTimeField("Revocado el", null=True, blank=True)
    allow_preview = models.BooleanField("Permitir previsualización", default=True)
    allow_download = models.BooleanField("Permitir descarga", default=True)

    class Meta:
        verbose_name = "Enlace público"
        verbose_name_plural = "Enlaces públicos"
        ordering = ["-created_at"]

    def __str__(self):
        status = "Revocado" if self.revoked_at else ("Expirado" if self.is_expired else "Activo")
        return f"Enlace ({status}) para '{self.document.title}'"

    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and not self.is_expired
