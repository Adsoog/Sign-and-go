from django.core.exceptions import PermissionDenied
from .models import Workspace


def get_user_workspace(user):
    """
    Retrieves or creates the primary workspace for a given user.
    """
    if not user or not user.is_authenticated:
        return None

    workspace = Workspace.objects.filter(owner=user).first()
    if not workspace:
        workspace_name = f"Espacio de {user.get_short_name()}"
        workspace = Workspace.objects.create(
            owner=user,
            name=workspace_name,
        )
    return workspace


def check_workspace_access(request, target_workspace):
    """
    Ensures that the request user has ownership / access to the target workspace.
    Raises PermissionDenied if not authorized.
    """
    if not request.user.is_authenticated:
        raise PermissionDenied("Debe iniciar sesión para acceder a este espacio.")

    if target_workspace.owner_id != request.user.id and not request.user.is_staff:
        raise PermissionDenied("Acceso no autorizado al espacio de trabajo.")
    return True
