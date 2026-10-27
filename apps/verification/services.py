from dataclasses import dataclass
from typing import List, Optional
from apps.core.utils import compute_sha256
from apps.documents.models import Document
from apps.signing.providers.base import SignatureValidationReport
from apps.signing.providers.pyhanko_provider import get_signature_provider


@dataclass
class VerificationComparisonReport:
    uploaded_sha256: str
    exact_hash_match: bool
    matched_document: Optional[Document]
    has_signatures: bool
    signatures_intact: bool
    signatures_valid: bool
    signatures: List[SignatureValidationReport]
    verdict_code: str
    verdict_title: str
    verdict_description: str
    verdict_badge_class: str


def compare_and_verify_pdf(
    uploaded_pdf_bytes: bytes,
    reference_document_id: str | None = None,
) -> VerificationComparisonReport:
    """
    Compares an uploaded PDF against the vault archive and performs cryptographic verification.
    Distinguishes:
    1. Coincidencia exacta con el documento archivado.
    2. Firma criptográfica válida.
    3. Archivo diferente al documento archivado.
    4. Firma inválida o integridad comprometida.
    5. Estado inconcluso.
    """
    uploaded_sha256 = compute_sha256(uploaded_pdf_bytes)

    # Find matching archived document
    matched_doc = None
    if reference_document_id:
        matched_doc = Document.objects.filter(pk=reference_document_id).first()
    else:
        # Search by signed_sha256 or source_sha256
        matched_doc = Document.objects.filter(signed_sha256=uploaded_sha256).first()
        if not matched_doc:
            matched_doc = Document.objects.filter(source_sha256=uploaded_sha256).first()

    exact_hash_match = False
    if matched_doc and matched_doc.signed_sha256 == uploaded_sha256:
        exact_hash_match = True

    # Cryptographic signature validation with pyHanko
    provider = get_signature_provider()
    val_result = provider.validate_pdf(uploaded_pdf_bytes)

    has_sigs = val_result.has_signatures
    intact = val_result.signatures_intact
    valid = val_result.signatures_valid
    error_msg = val_result.error_message

    # Handle the 5 distinct product specification verdicts
    if error_msg:
        code = "INCONCLUSIVE"
        title = "Estado inconcluso (Estructura dañada)"
        desc = f"No fue posible interpretar completamente el archivo PDF: {error_msg}. La integridad no puede ser garantizada."
        badge = "warning"
    elif exact_hash_match and has_sigs and intact and valid:
        code = "EXACT_MATCH"
        title = "Coincidencia exacta con el documento archivado"
        desc = (
            "El archivo recibido es idéntico byte a byte al documento firmado archivado en la bóveda. "
            "Su firma criptográfica es matemáticamente válida y la integridad está intacta."
        )
        badge = "success"
    elif has_sigs and (not intact or not valid):
        code = "TAMPERED_OR_INVALID"
        title = "Firma inválida o integridad comprometida"
        desc = (
            "Se detectaron firmas digitales en el documento, pero han sido alteradas o invalidadas tras su aplicación. "
            "El documento no es auténtico o fue modificado indebidamente."
        )
        badge = "danger"
    elif has_sigs and intact and valid:
        code = "VALID_SIGNATURE"
        title = "Firma criptográfica válida"
        desc = (
            "El documento contiene firmas digitales matemáticamente válidas e intactas. "
            + ("Sin embargo, su huella SHA-256 difiere del documento archivado de referencia." if (matched_doc and not exact_hash_match) else "")
        )
        badge = "info"
    elif matched_doc and not exact_hash_match:
        code = "DIFFERENT_DOCUMENT"
        title = "Archivo diferente al documento archivado"
        desc = "La huella digital SHA-256 del archivo no coincide con el documento archivado de referencia y no contiene firmas válidas."
        badge = "secondary"
    else:
        code = "NO_SIGNATURES"
        title = "Sin firmas digitales"
        desc = "El archivo analizado no contiene firmas digitales PAdES registradas ni coincide con la bóveda."
        badge = "secondary"

    return VerificationComparisonReport(
        uploaded_sha256=uploaded_sha256,
        exact_hash_match=exact_hash_match,
        matched_document=matched_doc,
        has_signatures=has_sigs,
        signatures_intact=intact,
        signatures_valid=valid,
        signatures=val_result.signatures,
        verdict_code=code,
        verdict_title=title,
        verdict_description=desc,
        verdict_badge_class=badge,
    )
