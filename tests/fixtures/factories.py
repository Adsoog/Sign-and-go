import datetime
import io
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from reportlab.pdfgen import canvas
from apps.accounts.models import User
from apps.workspaces.models import Workspace
from apps.workspaces.permissions import get_user_workspace
from apps.certificates.services import save_certificate_profile
from apps.documents.services import process_uploaded_document


def create_test_user_and_workspace(email="user@example.com", password="Password123!"):
    user = User.objects.create_user(email=email, password=password, full_name="Test User")
    workspace = get_user_workspace(user)
    return user, workspace


def create_sample_pdf_bytes(title="Test PDF Document") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, title)
    c.drawString(100, 700, "SignBox automated test page.")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def create_sample_p12_bytes(
    common_name="Signer Test",
    organization="SignBox Test Lab",
    password="testpassword",
) -> bytes:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    p12_bytes = serialization.pkcs12.serialize_key_and_certificates(
        name=b"test_cert",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8")),
    )
    return p12_bytes
