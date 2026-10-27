from pathlib import Path
import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.certificates.services import save_certificate_profile
from apps.core.utils import compute_sha256
from apps.documents.models import Document
from apps.documents.services import process_uploaded_document
from apps.signing.services import execute_document_signature
from tests.fixtures.factories import (
    create_sample_p12_bytes,
    create_sample_pdf_bytes,
    create_test_user_and_workspace,
)


@pytest.mark.django_db
class TestSigningFlow:
    def test_complete_cryptographic_signing_flow(self):
        user, ws = create_test_user_and_workspace()

        # 1. Setup certificate
        p12_bytes = create_sample_p12_bytes(
            common_name="Signer Alpha",
            organization="SignBox Test Org",
            password="signpass123",
        )
        cert = save_certificate_profile(ws, "Cert Alpha", p12_bytes, "signpass123")

        # 2. Setup document
        pdf_bytes = create_sample_pdf_bytes("Important Contract")
        uploaded_file = SimpleUploadedFile("contract.pdf", pdf_bytes, content_type="application/pdf")
        doc = process_uploaded_document(ws, user, uploaded_file, "Important Contract")

        assert doc.status == Document.STATUS_UPLOADED
        assert doc.signed_file is None

        # 3. Execute signature
        result = execute_document_signature(
            document=doc,
            certificate_profile=cert,
            passphrase="signpass123",
            page_number=1,
            norm_x=0.1,
            norm_y=0.7,
            norm_w=0.4,
            norm_h=0.15,
            reason="Aprobado y verificado",
            location="Madrid",
            user=user,
        )

        assert result["success"] is True
        assert result["intact"] is True
        assert result["valid"] is True
        assert "verification_url" in result

        # 4. Check DB updates
        doc.refresh_from_db()
        assert doc.status == Document.STATUS_SIGNED
        assert doc.signed_file is not None
        assert doc.signed_sha256 == result["signed_sha256"]

        # 5. Check file on disk matches stored SHA-256
        signed_path = Path(settings.PRIVATE_STORAGE_ROOT) / "documents" / "signed" / doc.signed_file
        assert signed_path.exists()
        with open(signed_path, "rb") as f:
            disk_signed_bytes = f.read()

        assert compute_sha256(disk_signed_bytes) == doc.signed_sha256

    def test_signing_with_incorrect_password_fails(self):
        user, ws = create_test_user_and_workspace()
        p12_bytes = create_sample_p12_bytes(password="correct_secret")
        cert = save_certificate_profile(ws, "Cert Beta", p12_bytes, "correct_secret")

        pdf_bytes = create_sample_pdf_bytes("Doc Beta")
        uploaded_file = SimpleUploadedFile("beta.pdf", pdf_bytes, content_type="application/pdf")
        doc = process_uploaded_document(ws, user, uploaded_file, "Doc Beta")

        with pytest.raises(ValueError, match="contraseña incorrecta"):
            execute_document_signature(
                document=doc,
                certificate_profile=cert,
                passphrase="WRONG_PASSWORD",
                page_number=1,
                norm_x=0.1,
                norm_y=0.7,
                norm_w=0.4,
                norm_h=0.15,
                user=user,
            )

        doc.refresh_from_db()
        assert doc.status == Document.STATUS_FAILED
        assert doc.signed_file is None
