import logging
from typing import Any, Dict
from django.utils import timezone
from apps.core.utils import anonymize_ip
from apps.documents.models import Document
from apps.sharing.models import ShareLink
from .models import DocumentEvent

logger = logging.getLogger(__name__)


def extract_client_ip(request) -> str:
    if not request:
        return "0.0.0.0"
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
    return ip


def record_document_event(
    document: Document,
    event_type: str,
    request=None,
    share_link: ShareLink | None = None,
    metadata: Dict[str, Any] | None = None,
) -> DocumentEvent:
    """
    Persists an activity event for a document, anonymizing IP addresses and sanitizing metadata.
    """
    user_agent = ""
    client_ip = "0.0.0.0"

    if request:
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:250]
        client_ip = extract_client_ip(request)

    anonymized_ip = anonymize_ip(client_ip)

    safe_meta = {}
    if metadata:
        for k, v in metadata.items():
            safe_meta[str(k)] = str(v) if not isinstance(v, (int, float, bool)) else v

    try:
        return DocumentEvent.objects.create(
            document=document,
            share_link=share_link,
            event_type=event_type,
            occurred_at=timezone.now(),
            user_agent=user_agent,
            ip_anonymized=anonymized_ip,
            request_metadata=safe_meta,
        )
    except Exception as exc:
        logger.error(f"Failed to record DocumentEvent: {exc}")
        return None
