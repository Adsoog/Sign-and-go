import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.certificates.services import save_certificate_profile
from apps.documents.services import process_uploaded_document
from apps.documents.storage import get_document_storage
from apps.signing.services import execute_document_signature
from apps.verification.services import compare_and_verify_pdf
from tests.fixtures.factories import (
    create_sample_p12_bytes,
    create_sample_pdf_bytes,
    create_test_user_and_workspace,
)


@pytest.mark.django_db
class TestDocumentVerificationAndComparison:
    def test_exact_hash_match_and_cryptographic_integrity(self):
        user, ws = create_test_user_and_workspace()
        p12_bytes = create_sample_p12_bytes(password="verifypass")
        cert = save_certificate_profile(ws, "Cert Verify", p12_bytes, "verifypass")

        pdf_bytes = create_sample_pdf_bytes("Verification Target PDF")
        uploaded_file = SimpleUploadedFile("target.pdf", pdf_bytes, content_type="application/pdf")
        doc = process_uploaded_document(ws, user, uploaded_file, "Target")

        result = execute_document_signature(
            document=doc,
            certificate_profile=cert,
            passphrase="verifypass",
            page_number=1,
            norm_x=0.1,
            norm_y=0.7,
            norm_w=0.4,
            norm_h=0.15,
            user=user,
        )

        storage = get_document_storage()
        signed_bytes = storage.read_signed(doc.signed_file)

        # 1. Exact match test
        report = compare_and_verify_pdf(signed_bytes)
        assert report.exact_hash_match is True
        assert report.has_signatures is True
        assert report.signatures_valid is True
        assert report.signatures_intact is True
        assert report.verdict_code == "EXACT_MATCH"

    def test_tampered_pdf_fails_integrity(self):
        user, ws = create_test_user_and_workspace()
        p12_bytes = create_sample_p12_bytes(password="tamperpass")
        cert = save_certificate_profile(ws, "Cert Tamper", p12_bytes, "tamperpass")

        pdf_bytes = create_sample_pdf_bytes("Tamper Target")
        uploaded_file = SimpleUploadedFile("tamper.pdf", pdf_bytes, content_type="application/pdf")
        doc = process_uploaded_document(ws, user, uploaded_file, "Tamper Doc")

        execute_document_signature(
            document=doc,
            certificate_profile=cert,
            passphrase="tamperpass",
            page_number=1,
            norm_x=0.1,
            norm_y=0.7,
            norm_w=0.4,
            norm_h=0.15,
            user=user,
        )

        storage = get_document_storage()
        signed_bytes = storage.read_signed(doc.signed_file)

        # Tamper: alter text in the signed content stream
        assert b"Tamper Target" in signed_bytes
        tampered_bytes = signed_bytes.replace(b"Tamper Target", b"Tamper Alterd")

        report = compare_and_verify_pdf(tampered_bytes, reference_document_id=str(doc.id))
        assert report.exact_hash_match is False
        assert report.has_signatures is True
        assert report.signatures_intact is False
        assert report.verdict_code == "TAMPERED_OR_INVALID"
