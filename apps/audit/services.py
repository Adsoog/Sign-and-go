import logging
from typing import Any, Dict
from apps.workspaces.models import Workspace
from .models import AuditLog

logger = logging.getLogger(__name__)


def sanitize_audit_metadata(metadata: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Cleans metadata to prevent inadvertent logging of sensitive keywords.
    """
    if not metadata:
        return {}

    sanitized = {}
    forbidden_keys = {"password", "secret", "private_key", "p12", "pfx", "token", "encryption_key"}
    for k, v in metadata.items():
        if any(fk in k.lower() for fk in forbidden_keys):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = str(v) if not isinstance(v, (str, int, float, bool, list, dict)) else v

    return sanitized


def log_audit_event(
    workspace: Workspace,
    actor,
    action: str,
    target_type: str,
    target_id: str,
    metadata: Dict[str, Any] | None = None,
) -> AuditLog:
    """
    Creates an append-only audit log entry.
    """
    safe_meta = sanitize_audit_metadata(metadata)
    try:
        return AuditLog.objects.create(
            workspace=workspace,
            actor=actor if actor and actor.is_authenticated else None,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=safe_meta,
        )
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        return None
