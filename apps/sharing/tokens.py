import datetime
from django.utils import timezone
from apps.core.utils import generate_secure_token, hash_token
from apps.documents.models import Document
from apps.tracking.models import DocumentEvent
from apps.tracking.services import record_document_event
from .models import ShareLink


def create_share_link(
    document: Document,
    created_by=None,
    expires_in_days: int | None = None,
    allow_preview: bool = True,
    allow_download: bool = True,
) -> tuple[ShareLink, str]:
    """
    Creates a new ShareLink with a high-entropy secret token.
    Only the SHA-256 hash is saved to the database.
    Returns (ShareLink, raw_token).
    """
    raw_token = generate_secure_token(32)
    token_hash = hash_token(raw_token)

    expires_at = None
    if expires_in_days:
        expires_at = timezone.now() + datetime.timedelta(days=int(expires_in_days))

    link = ShareLink.objects.create(
        document=document,
        token_hash=token_hash,
        created_by=created_by if created_by and created_by.is_authenticated else None,
        expires_at=expires_at,
        allow_preview=allow_preview,
        allow_download=allow_download,
    )

    record_document_event(
        document=document,
        share_link=link,
        event_type=DocumentEvent.EVENT_SHARE_LINK_CREATED if hasattr(DocumentEvent, 'EVENT_SHARE_LINK_CREATED') else "share_link_created",
        metadata={"link_id": str(link.id), "expires_at": expires_at.isoformat() if expires_at else None},
    )

    return link, raw_token


def resolve_share_link(raw_token: str) -> ShareLink | None:
    """
    Finds a ShareLink by token or token hash.
    Returns the ShareLink instance if found (regardless of expired/revoked state,
    so views can display an informative state instead of generic 404).
    Supports:
    1. Direct match on SHA-256 hash of raw_token.
    2. Direct match on token_hash (if raw_token was stored or hashed).
    3. Prefix match on token_hash (for links rendered with hash prefix).
    """
    if not raw_token:
        return None
    token_str = raw_token.strip()

    # 1. Match by SHA-256 hash
    token_hash = hash_token(token_str)
    link = ShareLink.objects.select_related("document", "document__certificate_profile").filter(token_hash=token_hash).first()
    if link:
        return link

    # 2. Direct match on token_hash
    link = ShareLink.objects.select_related("document", "document__certificate_profile").filter(token_hash=token_str).first()
    if link:
        return link

    # 3. Prefix match on token_hash (e.g. 16-char prefix)
    if len(token_str) >= 12:
        link = ShareLink.objects.select_related("document", "document__certificate_profile").filter(token_hash__startswith=token_str).first()
        if link:
            return link

    return None


def revoke_share_link(link: ShareLink, actor=None) -> None:
    """Revokes an active share link."""
    link.revoked_at = timezone.now()
    link.save(update_fields=["revoked_at"])
    record_document_event(
        document=link.document,
        share_link=link,
        event_type="share_link_revoked",
        metadata={"revoked_by": actor.email if actor and actor.is_authenticated else "Sistema"},
    )
