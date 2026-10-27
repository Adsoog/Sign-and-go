import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SignatureValidationReport:
    field_name: str
    intact: bool
    valid: bool
    trusted: bool
    signer_name: str
    signing_time: Optional[str]
    summary: str


@dataclass
class ValidationResult:
    has_signatures: bool
    signatures_intact: bool
    signatures_valid: bool
    signatures: List[SignatureValidationReport] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class SignatureExecutionResult:
    signed_pdf_bytes: bytes
    field_name: str
    intact: bool
    valid: bool
    trusted: bool
    summary: str


class BaseSignatureProvider(abc.ABC):
    @abc.abstractmethod
    def sign_pdf(
        self,
        pdf_bytes: bytes,
        pkcs12_bytes: bytes,
        passphrase: str,
        field_name: str,
        reason: str,
        location: str,
        page_number: int,
        box: tuple[float, float, float, float] | None = None,
    ) -> SignatureExecutionResult:
        """Applies cryptographic signature to PDF bytes."""
        pass

    @abc.abstractmethod
    def validate_pdf(self, pdf_bytes: bytes) -> ValidationResult:
        """Validates all cryptographic signatures present in a PDF."""
        pass
