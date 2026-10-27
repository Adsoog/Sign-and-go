import hashlib
import uuid
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from apps.audit.services import log_audit_event
from apps.certificates.models import CertificateProfile
from apps.certificates.services import get_decrypted_certificate_bytes
from apps.core.utils import compute_sha256
from apps.documents.models import Document
from apps.documents.storage import get_document_storage
from apps.sharing.tokens import create_share_link
from .appearance import embed_visual_appearance_in_pdf
from .models import SigningOperation
from .providers.pyhanko_provider import get_signature_provider


def execute_document_signature(
    document: Document,
    certificate_profile: CertificateProfile,
    passphrase: str,
    page_number: int,
    norm_x: float,
    norm_y: float,
    norm_w: float,
    norm_h: float,
    reason: str = "Firmado electrónicamente con Sign & Go",
    location: str = "Sign & Go Vault",
    idempotency_key: str | None = None,
    user=None,
) -> dict:
    """
    Executes the complete cryptographic PDF signing workflow:
    1. Idempotency validation
    2. Decryption of certificate container into RAM (never disk)
    3. Creation of verification token & URL
    4. Visual appearance overlay + QR + interactive PDF link
    5. pyHanko PAdES cryptographic signature application
    6. Post-signing validation & SHA-256 calculation
    7. Storage of immutable signed PDF
    """
    if not idempotency_key:
        idempotency_key = uuid.uuid4().hex

    # Check for existing completed operation with same idempotency key
    existing_op = SigningOperation.objects.filter(idempotency_key=idempotency_key).first()
    if existing_op and existing_op.status == SigningOperation.STATUS_COMPLETED:
        return {
            "success": True,
            "operation_id": str(existing_op.id),
            "status": existing_op.status,
            "summary": existing_op.result_summary,
            "sha256": document.signed_sha256,
        }

    # Register pending operation
    operation, _ = SigningOperation.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "document": document,
            "certificate_profile": certificate_profile,
            "status": SigningOperation.STATUS_PENDING,
            "page_number": page_number,
            "x": norm_x,
            "y": norm_y,
            "width": norm_w,
            "height": norm_h,
            "reason": reason,
            "location": location,
        },
    )

    storage = get_document_storage()
    source_bytes = storage.read_source(document.source_file)

    try:
        # 1. Retrieve decrypted P12 bytes in memory
        p12_bytes = get_decrypted_certificate_bytes(certificate_profile)

        # 2. Generate a public ShareLink for the document verification
        share_link, raw_token = create_share_link(
            document=document,
            created_by=user,
            allow_preview=True,
            allow_download=True,
        )
        base_url = getattr(settings, "SIGNBOX_BASE_URL", "http://localhost:8000").rstrip("/")
        verification_url = f"{base_url}/d/{raw_token}"
        tracking_beacon_url = f"{base_url}/track/pdf/{raw_token}/beacon.png"

        # 3. Embed visual appearance overlay + QR code into the PDF before signing
        signed_date_str = timezone.now().strftime("%d/%m/%Y %H:%M UTC")
        prepared_pdf_bytes, pdf_box = embed_visual_appearance_in_pdf(
            source_pdf_bytes=source_bytes,
            page_number=page_number,
            norm_x=norm_x,
            norm_y=norm_y,
            norm_w=norm_w,
            norm_h=norm_h,
            signer_name=certificate_profile.name,
            subject=certificate_profile.subject_name,
            signed_date_str=signed_date_str,
            verification_url=verification_url,
            tracking_beacon_url=tracking_beacon_url,
        )

        # 4. Cryptographic signing with pyHanko
        sig_provider = get_signature_provider()
        sig_result = sig_provider.sign_pdf(
            pdf_bytes=prepared_pdf_bytes,
            pkcs12_bytes=p12_bytes,
            passphrase=passphrase,
            field_name=f"SignBox_Sig_{uuid.uuid4().hex[:8]}",
            reason=reason,
            location=location,
            page_number=page_number,
            box=pdf_box,
        )

        # 5. Calculate SHA-256 hash of final signed document
        final_signed_bytes = sig_result.signed_pdf_bytes
        final_sha256 = compute_sha256(final_signed_bytes)

        # 6. Save final immutable signed PDF
        signed_storage_filename = storage.save_signed(str(document.id), final_signed_bytes)

        # 7. Update document and operation atomically
        with transaction.atomic():
            document.signed_file = signed_storage_filename
            document.signed_sha256 = final_sha256
            document.signed_at = timezone.now()
            document.status = Document.STATUS_SIGNED
            document.certificate_profile = certificate_profile
            document.save()

            certificate_profile.last_used_at = timezone.now()
            certificate_profile.save(update_fields=["last_used_at"])

            operation.status = SigningOperation.STATUS_COMPLETED
            operation.completed_at = timezone.now()
            operation.result_summary = sig_result.summary
            operation.save()

        log_audit_event(
            workspace=document.workspace,
            actor=user,
            action="document_signed",
            target_type="Document",
            target_id=str(document.id),
            metadata={
                "certificate_id": str(certificate_profile.id),
                "signed_sha256": final_sha256,
                "intact": sig_result.intact,
                "valid": sig_result.valid,
            },
        )

        return {
            "success": True,
            "operation_id": str(operation.id),
            "status": "completed",
            "signed_sha256": final_sha256,
            "verification_url": verification_url,
            "intact": sig_result.intact,
            "valid": sig_result.valid,
            "summary": sig_result.summary,
        }

    except Exception as exc:
        operation.status = SigningOperation.STATUS_FAILED
        operation.safe_error_code = type(exc).__name__
        operation.result_summary = str(exc)[:500]
        operation.completed_at = timezone.now()
        operation.save()

        document.status = Document.STATUS_FAILED
        document.save(update_fields=["status"])

        raise exc
