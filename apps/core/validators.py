from django.conf import settings
from django.core.exceptions import ValidationError


def validate_pdf_file(uploaded_file):
    """
    Validates uploaded PDF file:
    1. Size limit
    2. %PDF- magic bytes header
    """
    max_size = getattr(settings, "MAX_DOCUMENT_SIZE_BYTES", 25 * 1024 * 1024)
    if uploaded_file.size > max_size:
        raise ValidationError(
            f"El archivo excede el tamaño máximo permitido de {max_size // (1024 * 1024)} MB."
        )

    # Read the first 1024 bytes to check for %PDF
    orig_pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
    uploaded_file.seek(0)
    header = uploaded_file.read(1024)
    uploaded_file.seek(orig_pos)

    if b"%PDF-" not in header:
        raise ValidationError("El archivo subido no es un PDF válido o está corrupto.")


def validate_certificate_file(uploaded_file):
    """
    Validates uploaded PKCS#12 / PFX certificate file:
    1. Size limit (max 10MB)
    2. Extension check (.p12, .pfx)
    """
    max_size = getattr(settings, "MAX_CERTIFICATE_SIZE_BYTES", 10 * 1024 * 1024)
    if uploaded_file.size > max_size:
        raise ValidationError(
            f"El certificado excede el tamaño máximo permitido de {max_size // (1024 * 1024)} MB."
        )

    name = uploaded_file.name.lower()
    if not (name.endswith(".p12") or name.endswith(".pfx")):
        raise ValidationError("El archivo debe tener extensión .p12 o .pfx.")
