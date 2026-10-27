from pathlib import Path
import pytest
from django.conf import settings
from apps.certificates.models import CertificateProfile
from apps.certificates.services import (
    extract_p12_metadata,
    generate_self_signed_certificate,
    get_decrypted_certificate_bytes,
    save_certificate_profile,
)
from tests.fixtures.factories import create_sample_p12_bytes, create_test_user_and_workspace


@pytest.mark.django_db
class TestCertificateVault:
    def test_save_and_decrypt_certificate_profile(self):
        user, ws = create_test_user_and_workspace()
        p12_bytes = create_sample_p12_bytes(
            common_name="Juan Perez",
            organization="SignBox Corp",
            password="secretpassword123",
        )

        profile = save_certificate_profile(
            workspace=ws,
            name="Perfil Juan",
            p12_bytes=p12_bytes,
            password="secretpassword123",
        )

        assert profile.name == "Perfil Juan"
        assert "Juan Perez" in profile.subject_name
        assert "SignBox Corp" in profile.subject_name
        assert profile.fingerprint_sha256 is not None
        assert profile.is_active is True

        # Check encryption at rest: raw file on disk is encrypted
        file_path = Path(settings.PRIVATE_STORAGE_ROOT) / "certificates" / profile.encrypted_file
        assert file_path.exists()
        with open(file_path, "rb") as f:
            disk_bytes = f.read()

        # Disk bytes must NOT be equal to raw p12 bytes
        assert disk_bytes != p12_bytes

        # Decrypt in RAM using vault key
        decrypted_p12 = get_decrypted_certificate_bytes(profile)
        assert decrypted_p12 == p12_bytes

        # Confirm password can unlock decrypted bytes
        meta = extract_p12_metadata(decrypted_p12, "secretpassword123")
        assert meta["fingerprint_sha256"] == profile.fingerprint_sha256

    def test_invalid_password_raises_error(self):
        p12_bytes = create_sample_p12_bytes(password="correct_pass")
        with pytest.raises(ValueError, match="Contraseña del certificado incorrecta"):
            extract_p12_metadata(p12_bytes, "WRONG_PASS")

    def test_generate_self_signed_test_certificate(self):
        user, ws = create_test_user_and_workspace()
        profile = generate_self_signed_certificate(
            workspace=ws,
            profile_name="Demo Key",
            common_name="Demo User",
            organization="Demo Org",
            country="ES",
            password="testpass123",
            valid_days=90,
        )

        assert profile.name == "Demo Key"
        assert profile.days_until_expiration > 85
        assert not profile.is_expired
