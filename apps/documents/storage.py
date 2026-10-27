import abc
import os
import uuid
from pathlib import Path
from django.conf import settings


class DocumentStorageInterface(abc.ABC):
    @abc.abstractmethod
    def save_source(self, document_id: str, content: bytes, original_filename: str) -> str:
        pass

    @abc.abstractmethod
    def save_signed(self, document_id: str, content: bytes) -> str:
        pass

    @abc.abstractmethod
    def read_source(self, relative_path: str) -> bytes:
        pass

    @abc.abstractmethod
    def read_signed(self, relative_path: str) -> bytes:
        pass

    @abc.abstractmethod
    def get_source_absolute_path(self, relative_path: str) -> Path:
        pass

    @abc.abstractmethod
    def get_signed_absolute_path(self, relative_path: str) -> Path:
        pass


class LocalDocumentStorage(DocumentStorageInterface):
    """
    Saves documents in private disk storage outside the web root.
    Files are never accessible through direct web server static routes.
    """

    def __init__(self):
        self.root = Path(settings.PRIVATE_STORAGE_ROOT) / "documents"
        self.sources_dir = self.root / "sources"
        self.signed_dir = self.root / "signed"
        self.sources_dir.mkdir(parents=True, exist_ok=True)
        self.signed_dir.mkdir(parents=True, exist_ok=True)

    def save_source(self, document_id: str, content: bytes, original_filename: str) -> str:
        ext = Path(original_filename).suffix or ".pdf"
        filename = f"{document_id}_src{ext}"
        target = self.sources_dir / filename
        with open(target, "wb") as f:
            f.write(content)
        return filename

    def save_signed(self, document_id: str, content: bytes) -> str:
        filename = f"{document_id}_signed.pdf"
        target = self.signed_dir / filename
        with open(target, "wb") as f:
            f.write(content)
        return filename

    def read_source(self, relative_path: str) -> bytes:
        target = self.sources_dir / relative_path
        if not target.exists():
            raise FileNotFoundError(f"Archivo de origen no encontrado: {relative_path}")
        with open(target, "rb") as f:
            return f.read()

    def read_signed(self, relative_path: str) -> bytes:
        target = self.signed_dir / relative_path
        if not target.exists():
            raise FileNotFoundError(f"Archivo firmado no encontrado: {relative_path}")
        with open(target, "rb") as f:
            return f.read()

    def get_source_absolute_path(self, relative_path: str) -> Path:
        return self.sources_dir / relative_path

    def get_signed_absolute_path(self, relative_path: str) -> Path:
        return self.signed_dir / relative_path


def get_document_storage() -> DocumentStorageInterface:
    """Returns configured document storage backend (Local default, Google Drive extensible in V2)."""
    return LocalDocumentStorage()
