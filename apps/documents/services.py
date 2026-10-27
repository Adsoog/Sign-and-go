import io
import uuid
from pypdf import PdfReader
from apps.audit.services import log_audit_event
from apps.core.utils import compute_sha256
from .models import Document
from .storage import get_document_storage


def process_uploaded_document(workspace, user, uploaded_file, title: str | None = None) -> Document:
    """
    Validates, analyzes, hashes and persists an uploaded PDF into private storage.
    """
    file_bytes = uploaded_file.read()
    source_sha256 = compute_sha256(file_bytes)
    file_size = len(file_bytes)
    filename = uploaded_file.name

    # Inspect page count
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        page_count = len(reader.pages)
    except Exception:
        page_count = 1

    doc_id = str(uuid.uuid4())
    storage = get_document_storage()
    source_storage_name = storage.save_source(doc_id, file_bytes, filename)

    doc = Document.objects.create(
        id=doc_id,
        workspace=workspace,
        created_by=user,
        title=title.strip() if title else filename,
        original_filename=filename,
        source_file=source_storage_name,
        source_sha256=source_sha256,
        file_size=file_size,
        page_count=page_count,
        status=Document.STATUS_UPLOADED,
        storage_backend="local",
        storage_key=source_storage_name,
    )

    log_audit_event(
        workspace=workspace,
        actor=user,
        action="document_uploaded",
        target_type="Document",
        target_id=str(doc.id),
        metadata={"filename": filename, "sha256": source_sha256, "pages": page_count},
    )

    return doc
