import uuid
from django.conf import settings
from django.db import models
from apps.workspaces.models import Workspace


class AuditLog(models.Model):
    """
    Append-only security audit log for sensitive operations.
    Strictly prohibits recording passwords, private keys, or raw secret payloads.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        verbose_name="Espacio de trabajo",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
        verbose_name="Usuario",
    )
    action = models.CharField("Acción", max_length=100, db_index=True)
    target_type = models.CharField("Tipo de entidad", max_length=100)
    target_id = models.CharField("ID de entidad", max_length=100, db_index=True)
    created_at = models.DateTimeField("Fecha y hora", auto_now_add=True, db_index=True)
    metadata = models.JSONField("Metadatos", default=dict, blank=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-created_at"]

    def __str__(self):
        actor_email = self.actor.email if self.actor else "Sistema"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {actor_email} -> {self.action} ({self.target_type})"
