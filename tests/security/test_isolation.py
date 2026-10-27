import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from apps.certificates.services import save_certificate_profile
from apps.documents.services import process_uploaded_document
from apps.sharing.tokens import create_share_link, revoke_share_link
from tests.fixtures.factories import (
    create_sample_p12_bytes,
    create_sample_pdf_bytes,
    create_test_user_and_workspace,
)


@pytest.mark.django_db
class TestWorkspaceIsolation:
    def test_user_cannot_list_documents_of_another_workspace(self, client):
        user_a, ws_a = create_test_user_and_workspace(email="alice@example.com")
        user_b, ws_b = create_test_user_and_workspace(email="bob@example.com")

        pdf_bytes = create_sample_pdf_bytes("Alice Secret Document")
        uploaded_file = SimpleUploadedFile("alice.pdf", pdf_bytes, content_type="application/pdf")
        doc_a = process_uploaded_document(ws_a, user_a, uploaded_file, "Alice Contract")

        # Bob logs in
        client.force_login(user_b)
        res = client.get(reverse("documents:list"))
        assert res.status_code == 200
        # Bob cannot see Alice's document in the list
        assert doc_a.title not in res.content.decode("utf-8")

    def test_user_cannot_download_another_users_document(self, client):
        user_a, ws_a = create_test_user_and_workspace(email="alice2@example.com")
        user_b, ws_b = create_test_user_and_workspace(email="bob2@example.com")

        pdf_bytes = create_sample_pdf_bytes("Alice Secret File")
        uploaded_file = SimpleUploadedFile("alice2.pdf", pdf_bytes, content_type="application/pdf")
        doc_a = process_uploaded_document(ws_a, user_a, uploaded_file, "Alice Confidential")

        # Bob logs in and tries to download Alice's private file
        client.force_login(user_b)
        download_url = reverse("documents:download", kwargs={"pk": doc_a.id, "file_type": "source"})
        res = client.get(download_url)
        assert res.status_code == 404

    def test_certificates_are_strictly_isolated_by_workspace(self, client):
        user_a, ws_a = create_test_user_and_workspace(email="alice_cert@example.com")
        user_b, ws_b = create_test_user_and_workspace(email="bob_cert@example.com")

        p12 = create_sample_p12_bytes("Alice Cert", password="pass")
        cert_a = save_certificate_profile(ws_a, "Cert Alice", p12, "pass")

        client.force_login(user_b)
        res = client.get(reverse("certificates:list"))
        assert res.status_code == 200
        assert "Cert Alice" not in res.content.decode("utf-8")

        # Bob tries to access Alice's cert detail
        detail_res = client.get(reverse("certificates:detail", kwargs={"pk": cert_a.id}))
        assert detail_res.status_code == 404

    def test_revoked_share_link_denies_access(self, client):
        user_a, ws_a = create_test_user_and_workspace(email="alice_share@example.com")
        pdf_bytes = create_sample_pdf_bytes("Shared Doc")
        uploaded_file = SimpleUploadedFile("doc.pdf", pdf_bytes, content_type="application/pdf")
        doc = process_uploaded_document(ws_a, user_a, uploaded_file, "Shared Doc")

        link, raw_token = create_share_link(doc, user_a)
        verify_url = reverse("sharing:public_verify", kwargs={"token": raw_token})

        # Initially active
        res = client.get(verify_url)
        assert res.status_code == 200

        # Revoke link
        revoke_share_link(link, actor=user_a)
        res_after = client.get(verify_url)
        assert res_after.status_code == 410  # GONE / Revoked
