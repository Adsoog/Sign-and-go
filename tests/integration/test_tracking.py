import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from apps.documents.services import process_uploaded_document
from apps.sharing.tokens import create_share_link
from apps.tracking.models import DocumentEvent
from tests.fixtures.factories import create_sample_pdf_bytes, create_test_user_and_workspace


@pytest.mark.django_db
class TestTrackingAndEvents:
    def test_web_visit_and_download_events(self, client):
        user, ws = create_test_user_and_workspace()
        pdf_bytes = create_sample_pdf_bytes("Tracked Doc")
        uploaded_file = SimpleUploadedFile("track.pdf", pdf_bytes, content_type="application/pdf")
        doc = process_uploaded_document(ws, user, uploaded_file, "Tracked Doc")

        link, token = create_share_link(doc, user)

        # 1. Web visit
        verify_url = reverse("sharing:public_verify", kwargs={"token": token})
        res = client.get(verify_url, HTTP_USER_AGENT="Mozilla/5.0 TestBrowser", REMOTE_ADDR="203.0.113.42")
        assert res.status_code == 200

        event_visit = DocumentEvent.objects.filter(document=doc, event_type=DocumentEvent.EVENT_WEB_VISIT).first()
        assert event_visit is not None
        assert event_visit.ip_anonymized == "203.0.113.0"
        assert "TestBrowser" in event_visit.user_agent

        # 2. Remote PDF beacon request
        beacon_url = reverse("tracking:beacon", kwargs={"token": token})
        res_beacon = client.get(beacon_url, HTTP_USER_AGENT="AdobeAcrobat/24.0", REMOTE_ADDR="198.51.100.99")
        assert res_beacon.status_code == 200
        assert res_beacon["Content-Type"] == "image/png"

        event_beacon = DocumentEvent.objects.filter(document=doc, event_type=DocumentEvent.EVENT_PDF_RESOURCE_REQUEST).first()
        assert event_beacon is not None
        assert event_beacon.ip_anonymized == "198.51.100.0"
        assert "AdobeAcrobat" in event_beacon.user_agent
