from django.utils.deprecation import MiddlewareMixin
from .permissions import get_user_workspace


class WorkspaceMiddleware(MiddlewareMixin):
    """
    Attaches the current active workspace to the request object.
    Accessible throughout views, services and templates via request.workspace.
    """

    def process_request(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            # Look up or initialize user's primary workspace
            request.workspace = get_user_workspace(request.user)
        else:
            request.workspace = None
