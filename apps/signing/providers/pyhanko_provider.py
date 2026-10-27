import io
import logging
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.stamp import NoOpStampStyle

from .base import (
    BaseSignatureProvider,
    SignatureExecutionResult,
    SignatureValidationReport,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class PyHankoSignatureProvider(BaseSignatureProvider):
    """
    Cryptographic PDF signing and validation implementation based on pyHanko.
    Follows PAdES (PDF Advanced Electronic Signatures) standards.
    """

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
        passphrase_bytes = passphrase.encode("utf-8") if isinstance(passphrase, str) else passphrase

        try:
            signer = signers.SimpleSigner.load_pkcs12_data(
                pkcs12_bytes,
                other_certs=(),
                passphrase=passphrase_bytes,
            )
        except Exception as exc:
            raise ValueError(f"Error al desbloquear el certificado: contraseña incorrecta o formato incompatible.") from exc

        pdf_stream = io.BytesIO(pdf_bytes)
        writer = IncrementalPdfFileWriter(pdf_stream)

        # Append formal signature field to target page if box provided
        target_page_idx = max(0, page_number - 1)
        if box:
            fields.append_signature_field(
                writer,
                fields.SigFieldSpec(
                    sig_field_name=field_name,
                    on_page=target_page_idx,
                    box=(int(box[0]), int(box[1]), int(box[2]), int(box[3])),
                ),
            )

        meta = signers.PdfSignatureMetadata(
            field_name=field_name,
            reason=reason or "Firma digital verificada",
            location=location or "",
        )

        out_buf = io.BytesIO()
        pdf_signer = signers.PdfSigner(
            meta,
            signer=signer,
            stamp_style=NoOpStampStyle(),
        )
        pdf_signer.sign_pdf(writer, output=out_buf)
        out_buf.seek(0)
        signed_bytes = out_buf.getvalue()

        # Immediate cryptographic post-signature validation
        val_result = self.validate_pdf(signed_bytes)
        intact = val_result.signatures_intact
        valid = val_result.signatures_valid
        trusted = any(s.trusted for s in val_result.signatures) if val_result.signatures else False
        summary = (
            f"Firma criptográfica aplicada con éxito. "
            f"Integridad del PDF: {'Preservada' if intact else 'Comprometida'}, "
            f"Validez matemática: {'Válida' if valid else 'Inválida'}."
        )

        return SignatureExecutionResult(
            signed_pdf_bytes=signed_bytes,
            field_name=field_name,
            intact=intact,
            valid=valid,
            trusted=trusted,
            summary=summary,
        )

    def validate_pdf(self, pdf_bytes: bytes) -> ValidationResult:
        try:
            reader = PdfFileReader(io.BytesIO(pdf_bytes))
            embedded_sigs = reader.embedded_signatures
        except Exception as exc:
            return ValidationResult(
                has_signatures=False,
                signatures_intact=False,
                signatures_valid=False,
                error_message=f"No se pudo leer la estructura PDF: {str(exc)}",
            )

        if not embedded_sigs:
            return ValidationResult(
                has_signatures=False,
                signatures_intact=False,
                signatures_valid=False,
                signatures=[],
            )

        reports = []
        all_intact = True
        all_valid = True

        for sig in embedded_sigs:
            try:
                status = validate_pdf_signature(sig)
                intact = bool(status.intact)
                valid = bool(status.valid)
                trusted = bool(getattr(status, "bottom_line", False))

                # Extract signer info
                signer_name = "Desconocido"
                try:
                    if hasattr(status, "signing_cert") and status.signing_cert:
                        signer_name = status.signing_cert.subject.human_friendly
                except Exception:
                    pass

                signing_time = None
                try:
                    if hasattr(status, "signer_reported_dt") and status.signer_reported_dt:
                        signing_time = status.signer_reported_dt.isoformat()
                except Exception:
                    pass

                if not intact:
                    all_intact = False
                if not valid:
                    all_valid = False

                reports.append(
                    SignatureValidationReport(
                        field_name=sig.field_name or "Signature",
                        intact=intact,
                        valid=valid,
                        trusted=trusted,
                        signer_name=signer_name,
                        signing_time=signing_time,
                        summary=str(status.summary()),
                    )
                )
            except Exception as e:
                logger.warning(f"Signature evaluation error on {sig.field_name}: {e}")
                reports.append(
                    SignatureValidationReport(
                        field_name=sig.field_name or "Signature",
                        intact=False,
                        valid=False,
                        trusted=False,
                        signer_name="Error de análisis",
                        signing_time=None,
                        summary=f"Error al validar firma: {str(e)}",
                    )
                )
                all_intact = False
                all_valid = False

        return ValidationResult(
            has_signatures=True,
            signatures_intact=all_intact,
            signatures_valid=all_valid,
            signatures=reports,
        )


def get_signature_provider() -> BaseSignatureProvider:
    return PyHankoSignatureProvider()
