from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain.requirement.document import DocumentFormat, GeneratedDocument


class GenerateDocumentsRequest(BaseModel):
    version_id: int | None = None


class GeneratedDocumentResponse(BaseModel):
    id: int
    formato: DocumentFormat
    version_id: int
    plantilla_version: str
    nombre_archivo: str
    mime_type: str
    tamano_bytes: int
    generado_at: datetime
    generado_by: str

    @classmethod
    def from_domain(cls, document: GeneratedDocument) -> GeneratedDocumentResponse:
        if document.id is None:
            raise ValueError("El documento debe estar persistido para serializarse.")
        return cls(
            id=document.id,
            formato=document.format,
            version_id=document.version_id,
            plantilla_version=document.template_version,
            nombre_archivo=document.file_name,
            mime_type=document.mime_type,
            tamano_bytes=document.size_bytes,
            generado_at=document.generated_at,
            generado_by=document.generated_by,
        )
