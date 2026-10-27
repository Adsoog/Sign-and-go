import datetime
import os
import uuid
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from .encryption import encrypt_data, decrypt_data
from .models import CertificateProfile


def get_certificates_storage_dir() -> Path:
    storage_dir = Path(settings.PRIVATE_STORAGE_ROOT) / "certificates"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def extract_p12_metadata(p12_bytes: bytes, password: str | bytes | None):
    """
    Parses PKCS#12 (.p12 / .pfx) using cryptography.
    Verifies the password and extracts human-readable metadata.
    """
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    elif password is None:
        password_bytes = None
    else:
        password_bytes = password

    try:
        private_key, certificate, additional_certs = serialization.pkcs12.load_key_and_certificates(
            p12_bytes,
            password_bytes,
        )
    except Exception as exc:
        raise ValueError("Contraseña del certificado incorrecta o archivo P12/PFX inválido.") from exc

    if certificate is None:
        raise ValueError("El archivo PKCS#12 no contiene un certificado X.509 válido.")

    if private_key is None:
        raise ValueError("El archivo PKCS#12 no contiene una clave privada utilizable para firmar.")

    # Format Subject de forma limpia y legible en español
    try:
        cn_attrs = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        org_attrs = certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        country_attrs = certificate.subject.get_attributes_for_oid(NameOID.COUNTRY_NAME)

        common_name = cn_attrs[0].value if cn_attrs else ""
        organization = org_attrs[0].value if org_attrs else ""
        country = country_attrs[0].value if country_attrs else ""

        if common_name and organization:
            subject_str = f"{common_name} - {organization}"
            if country:
                subject_str += f" ({country})"
        elif common_name:
            subject_str = common_name
            if country:
                subject_str += f" ({country})"
        elif organization:
            subject_str = organization
        else:
            subject_str = "Certificado Digital"
    except Exception:
        subject_str = str(certificate.subject)

    # Format Issuer
    try:
        issuer_cn = certificate.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
        issuer_str = issuer_cn[0].value if issuer_cn else str(certificate.issuer)
    except Exception:
        issuer_str = str(certificate.issuer)

    serial_number_hex = f"{certificate.serial_number:X}"
    fingerprint_sha256 = certificate.fingerprint(hashes.SHA256()).hex().lower()

    valid_from = certificate.not_valid_before_utc
    valid_until = certificate.not_valid_after_utc

    return {
        "certificate": certificate,
        "private_key": private_key,
        "additional_certs": additional_certs or [],
        "subject_name": subject_str[:250],
        "issuer_name": issuer_str[:250],
        "serial_number": serial_number_hex[:120],
        "fingerprint_sha256": fingerprint_sha256,
        "valid_from": valid_from,
        "valid_until": valid_until,
    }


def save_certificate_profile(workspace, name: str, p12_bytes: bytes, password: str) -> CertificateProfile:
    """
    Validates password, encrypts the P12 container using vault key, saves encrypted file to private storage,
    and registers CertificateProfile in database.
    """
    meta = extract_p12_metadata(p12_bytes, password)

    # Encrypt the raw p12 bytes
    encrypted_bytes = encrypt_data(p12_bytes)

    # Save to disk in private storage
    storage_dir = get_certificates_storage_dir()
    file_id = f"{uuid.uuid4().hex}.enc"
    file_path = storage_dir / file_id

    with open(file_path, "wb") as f:
        f.write(encrypted_bytes)

    profile = CertificateProfile.objects.create(
        workspace=workspace,
        name=name.strip(),
        subject_name=meta["subject_name"],
        issuer_name=meta["issuer_name"],
        serial_number=meta["serial_number"],
        fingerprint_sha256=meta["fingerprint_sha256"],
        valid_from=meta["valid_from"],
        valid_until=meta["valid_until"],
        encrypted_file=file_id,
        encryption_key_version="v1",
        is_active=True,
    )

    return profile


def get_decrypted_certificate_bytes(profile: CertificateProfile) -> bytes:
    """
    Reads the encrypted certificate file from private storage and decrypts it into memory.
    The password is NOT needed for this layer (only the vault master key).
    The resulting bytes are raw PKCS#12, requiring the user's password for signing.
    """
    storage_dir = get_certificates_storage_dir()
    file_path = storage_dir / profile.encrypted_file

    if not file_path.exists():
        raise FileNotFoundError(f"Archivo de certificado cifrado no encontrado: {profile.encrypted_file}")

    with open(file_path, "rb") as f:
        encrypted_bytes = f.read()

    return decrypt_data(encrypted_bytes)


def generate_self_signed_certificate(
    workspace,
    profile_name: str,
    common_name: str,
    organization: str,
    country: str,
    password: str,
    valid_days: int = 365,
) -> CertificateProfile:
    """
    Generates a cryptographically valid self-signed X.509 certificate and private key,
    packages it into PKCS#12, encrypts it, and saves it into the user's vault.
    Useful for testing and demo setups.
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country[:2].upper()),
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
        .not_valid_after(now + datetime.timedelta(days=valid_days))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    p12_bytes = serialization.pkcs12.serialize_key_and_certificates(
        name=profile_name.encode("utf-8"),
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8")),
    )

    return save_certificate_profile(
        workspace=workspace,
        name=profile_name,
        p12_bytes=p12_bytes,
        password=password,
    )
