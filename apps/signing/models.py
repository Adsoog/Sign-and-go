import uuid
from django.db import models
from apps.certificates.models import CertificateProfile
from apps.documents.models import Document


class SigningOperation(models.Model):
    """
    Tracks signature generation attempts with idempotency protection.
    Never stores passwords or private keys.
    """
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_COMPLETED, "Completado"),
        (STATUS_FAILED, "Fallido"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="signing_operations",
        verbose_name="Documento",
    )
    certificate_profile = models.ForeignKey(
        CertificateProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name="signing_operations",
        verbose_name="Certificado",
    )
    status = models.CharField("Estado", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider = models.CharField("Proveedor", max_length=50, default="pyhanko")
    signature_field_name = models.CharField("Campo de firma", max_length=100, default="SignBox_Signature_1")
    page_number = models.PositiveIntegerField("Número de página", default=1)
    
    # Normalized position percentages (0.0 to 1.0)
    x = models.FloatField("Posición X (%)", default=0.1)
    y = models.FloatField("Posición Y (%)", default=0.8)
    width = models.FloatField("Ancho (%)", default=0.35)
    height = models.FloatField("Alto (%)", default=0.15)

    reason = models.CharField("Motivo de firma", max_length=255, default="Firmado electrónicamente con SignBox")
    location = models.CharField("Ubicación", max_length=255, blank=True)
    started_at = models.DateTimeField("Iniciado el", auto_now_add=True)
    completed_at = models.DateTimeField("Completado el", null=True, blank=True)
    result_summary = models.TextField("Resumen del resultado", blank=True)
    safe_error_code = models.CharField("Código de error", max_length=100, blank=True)
    idempotency_key = models.CharField("Clave de idempotencia", max_length=128, unique=True, db_index=True)

    class Meta:
        verbose_name = "Operación de firma"
        verbose_name_plural = "Operaciones de firma"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Operación {self.idempotency_key[:12]} ({self.status}) - Doc: {self.document.title}"
