import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Workspace(models.Model):
    """
    Private workspace isolating tenant resources (certificates, documents, events).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_workspaces",
        verbose_name="Propietario",
    )
    name = models.CharField("Nombre del espacio", max_length=100)
    slug = models.SlugField("Identificador (slug)", max_length=120, unique=True, db_index=True)
    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    class Meta:
        verbose_name = "Espacio de trabajo"
        verbose_name_plural = "Espacios de trabajo"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.owner.email})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "workspace"
            candidate = base_slug
            counter = 1
            while Workspace.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)
