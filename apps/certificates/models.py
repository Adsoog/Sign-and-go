import uuid
from django.db import models
from django.utils import timezone
from apps.workspaces.models import Workspace


class CertificateProfile(models.Model):
    """
    Cryptographic certificate profile stored securely in the vault.
    Private key and certificates are stored encrypted in private storage.
    The user's P12 password is NEVER stored.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="certificate_profiles",
        verbose_name="Espacio de trabajo",
    )
    name = models.CharField("Nombre del perfil", max_length=120, help_text="Ej: Firma Personal, Representante Legal, etc.")
    subject_name = models.CharField("Titular", max_length=255)
    issuer_name = models.CharField("Emisor", max_length=255)
    serial_number = models.CharField("Número de serie", max_length=128)
    fingerprint_sha256 = models.CharField("Huella SHA-256", max_length=64, db_index=True)
    valid_from = models.DateTimeField("Válido desde")
    valid_until = models.DateTimeField("Válido hasta")
    encrypted_file = models.CharField("Ruta cifrada", max_length=255)
    encryption_key_version = models.CharField("Versión de clave", max_length=10, default="v1")
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    last_used_at = models.DateTimeField("Último uso", null=True, blank=True)

    class Meta:
        verbose_name = "Perfil de certificado"
        verbose_name_plural = "Perfiles de certificados"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.clean_subject_name}"

    @property
    def clean_subject_name(self) -> str:
        """Devuelve el nombre limpio del titular sin cadenas técnicas de OIDs."""
        import re
        val = self.subject_name or ""
        # Check if contains commonName=...
        cn_match = re.search(r"commonName=([^,\)]+)", val)
        if cn_match:
            return cn_match.group(1).strip()
        if " (" in val:
            val = val.split(" (")[0]
        if " - " in val:
            val = val.split(" - ")[0]
        if " · " in val:
            val = val.split(" · ")[0]
        return val.strip()

    @property
    def organization_name(self) -> str:
        """Devuelve la organización o empresa asociada si existe."""
        import re
        val = self.subject_name or ""
        match = re.search(r"organizationName=([^,\)]+)", val)
        if match:
            return match.group(1).strip()
        if " - " in val:
            parts = val.split(" - ")
            if len(parts) > 1:
                return parts[1].split("(")[0].strip()
        if " · " in val:
            parts = val.split(" · ")
            if len(parts) > 1:
                return parts[1].split("(")[0].strip()
        return ""

    @property
    def country_code(self) -> str:
        """Devuelve el código de país si existe."""
        import re
        val = self.subject_name or ""
        match = re.search(r"countryName=([^,\)]+)", val)
        if match:
            return match.group(1).strip()
        return ""

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.valid_until

    @property
    def days_until_expiration(self) -> int:
        delta = self.valid_until - timezone.now()
        return max(0, delta.days)

    @property
    def is_expiring_soon(self) -> bool:
        return not self.is_expired and self.days_until_expiration <= 30
