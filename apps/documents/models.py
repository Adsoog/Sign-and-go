import uuid
from django.conf import settings
from django.db import models
from apps.certificates.models import CertificateProfile
from apps.workspaces.models import Workspace


class Document(models.Model):
    """
    Core document model representing original and cryptographically signed PDF files.
    """
    STATUS_UPLOADED = "uploaded"
    STATUS_PREPARING = "preparing"
    STATUS_SIGNING = "signing"
    STATUS_SIGNED = "signed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_UPLOADED, "Subido"),
        (STATUS_PREPARING, "Preparando"),
        (STATUS_SIGNING, "Firmando"),
        (STATUS_SIGNED, "Firmado"),
        (STATUS_FAILED, "Fallido"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Espacio de trabajo",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
        verbose_name="Subido por",
    )
    title = models.CharField("Título del documento", max_length=255)
    original_filename = models.CharField("Nombre de archivo original", max_length=255)
    source_file = models.CharField("Archivo fuente", max_length=255)
    signed_file = models.CharField("Archivo firmado", max_length=255, null=True, blank=True)
    source_sha256 = models.CharField("Hash SHA-256 origen", max_length=64, db_index=True)
    signed_sha256 = models.CharField("Hash SHA-256 firmado", max_length=64, db_index=True, null=True, blank=True)
    file_size = models.PositiveIntegerField("Tamaño en bytes", default=0)
    page_count = models.PositiveIntegerField("Número de páginas", default=1)
    status = models.CharField("Estado", max_length=20, choices=STATUS_CHOICES, default=STATUS_UPLOADED, db_index=True)
    created_at = models.DateTimeField("Subido el", auto_now_add=True, db_index=True)
    signed_at = models.DateTimeField("Firmado el", null=True, blank=True)
    certificate_profile = models.ForeignKey(
        CertificateProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signed_documents",
        verbose_name="Certificado utilizado",
    )
    storage_backend = models.CharField("Backend de almacenamiento", max_length=50, default="local")
    storage_key = models.CharField("Clave de almacenamiento", max_length=255, blank=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_signed(self) -> bool:
        return self.status == self.STATUS_SIGNED and bool(self.signed_file)
