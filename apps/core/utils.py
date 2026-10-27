import hashlib
import ipaddress
import secrets
from typing import BinaryIO, Union


def compute_sha256(data_or_file: Union[bytes, BinaryIO]) -> str:
    """
    Computes hex SHA-256 hash of bytes or an open file-like object.
    Preserves file position if file-like object.
    """
    h = hashlib.sha256()
    if isinstance(data_or_file, bytes):
        h.update(data_or_file)
    else:
        orig_pos = 0
        if hasattr(data_or_file, "tell"):
            try:
                orig_pos = data_or_file.tell()
            except Exception:
                orig_pos = 0

        if hasattr(data_or_file, "seek"):
            data_or_file.seek(0)

        for chunk in iter(lambda: data_or_file.read(65536), b""):
            h.update(chunk)

        if hasattr(data_or_file, "seek"):
            data_or_file.seek(orig_pos)

    return h.hexdigest().lower()


def anonymize_ip(ip_str: str | None) -> str:
    """
    Anonymizes IP address for GDPR compliance and privacy.
    IPv4: masks last octet (e.g., 192.168.1.0)
    IPv6: masks last 80 bits
    """
    if not ip_str:
        return "0.0.0.0"
    
    # Strip any port if present
    clean_ip = ip_str.split(":")[0] if "." in ip_str and ":" in ip_str else ip_str
    
    try:
        ip = ipaddress.ip_address(clean_ip)
        if ip.version == 4:
            # Mask last octet
            parts = str(ip).split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        else:
            # Keep first 3 groups (48 bits), mask remainder
            network = ipaddress.ip_network(f"{ip}/48", strict=False)
            return str(network.network_address)
    except Exception:
        return "0.0.0.0"


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically strong URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(raw_token: str) -> str:
    """Hashes a public token with SHA-256 for secure database lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def format_bytes(size: int) -> str:
    """Formats file size into human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024.0
    return f"{size:.1f} TB"
