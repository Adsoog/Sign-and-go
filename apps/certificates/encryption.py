import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from cryptography.fernet import Fernet, InvalidToken


def get_encryption_key() -> bytes:
    """
    Retrieves the vault encryption key from settings.
    Ensures the key is non-empty and correctly formatted.
    """
    key = getattr(settings, "SIGNBOX_ENCRYPTION_KEY", "")
    if not key:
        raise ImproperlyConfigured(
            "SIGNBOX_ENCRYPTION_KEY no está configurada en el entorno. "
            "Es obligatoria para el cifrado seguro de la bóveda de certificados."
        )
    if isinstance(key, str):
        key = key.encode("utf-8")
    return key


def get_fernet_cipher() -> Fernet:
    return Fernet(get_encryption_key())


def encrypt_data(data: bytes) -> bytes:
    """
    Encrypts raw bytes using authenticated symmetric encryption (Fernet / AES-CBC + HMAC-SHA256).
    """
    cipher = get_fernet_cipher()
    return cipher.encrypt(data)


def decrypt_data(encrypted_data: bytes) -> bytes:
    """
    Decrypts authenticated ciphertext back to raw bytes.
    Raises InvalidToken if key is wrong or data was tampered with.
    """
    cipher = get_fernet_cipher()
    try:
        return cipher.decrypt(encrypted_data)
    except InvalidToken as exc:
        raise ValueError("Error al descifrar: clave incorrecta o archivo manipulado.") from exc
