from dataclasses import dataclass
from datetime import datetime
from typing import Literal

DocumentFormat = Literal["DOCX", "PDF"]

MIME_TYPES: dict[DocumentFormat, str] = {
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "PDF": "application/pdf",
}

_EXTENSIONS: dict[DocumentFormat, str] = {"DOCX": "docx", "PDF": "pdf"}


@dataclass(frozen=True, slots=True)
class GeneratedDocument:
    """Documento generado con sus metadatos y, opcionalmente, el binario."""

    requirement_id: int
    version_id: int
    format: DocumentFormat
    template_version: str
    file_name: str
    mime_type: str
    size_bytes: int
    generated_at: datetime
    generated_by: str
    content: bytes | None = None
    id: int | None = None


def build_file_name(
    folio: int, document_version: str, file_format: DocumentFormat
) -> str:
    """Nombre de archivo ``T#<folio>-v<version>.<ext>`` (RF-19)."""
    return f"T#{folio}-v{document_version}.{_EXTENSIONS[file_format]}"
