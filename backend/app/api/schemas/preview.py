from __future__ import annotations

from pydantic import BaseModel

from app.domain.requirement.preview import (
    PreviewBlock,
    PreviewBlockType,
    PreviewDocument,
    PreviewFirmas,
    PreviewSection,
    PreviewSigner,
    PreviewVersionRow,
)


class PreviewBlockResponse(BaseModel):
    tipo: PreviewBlockType
    texto: str | None = None
    items: list[str] | None = None

    @classmethod
    def from_domain(cls, block: PreviewBlock) -> PreviewBlockResponse:
        return cls(tipo=block.type, texto=block.text, items=list(block.items) or None)


class PreviewSectionResponse(BaseModel):
    codigo: str
    numero: str
    titulo: str
    bloques: list[PreviewBlockResponse]

    @classmethod
    def from_domain(cls, section: PreviewSection) -> PreviewSectionResponse:
        return cls(
            codigo=section.code,
            numero=section.number,
            titulo=section.title,
            bloques=[
                PreviewBlockResponse.from_domain(block) for block in section.blocks
            ],
        )


class PreviewVersionRowResponse(BaseModel):
    version: str
    fecha: str
    descripcion_cambio: str | None = None
    reviso: str | None = None
    elaboro: str | None = None

    @classmethod
    def from_domain(cls, row: PreviewVersionRow) -> PreviewVersionRowResponse:
        return cls(
            version=row.document_version,
            fecha=row.date,
            descripcion_cambio=row.change_description,
            reviso=row.reviewed_by,
            elaboro=row.prepared_by,
        )


class PreviewSignerResponse(BaseModel):
    nombre: str
    cargo: str | None = None

    @classmethod
    def from_domain(cls, signer: PreviewSigner) -> PreviewSignerResponse:
        return cls(nombre=signer.name, cargo=signer.position)


class PreviewFirmasResponse(BaseModel):
    elaboro: PreviewSignerResponse | None = None
    reviso: PreviewSignerResponse | None = None
    autorizo: PreviewSignerResponse | None = None

    @classmethod
    def from_domain(cls, firmas: PreviewFirmas) -> PreviewFirmasResponse:
        return cls(
            elaboro=(
                PreviewSignerResponse.from_domain(firmas.prepared_by)
                if firmas.prepared_by is not None
                else None
            ),
            reviso=(
                PreviewSignerResponse.from_domain(firmas.reviewed_by)
                if firmas.reviewed_by is not None
                else None
            ),
            autorizo=(
                PreviewSignerResponse.from_domain(firmas.authorized_by)
                if firmas.authorized_by is not None
                else None
            ),
        )


class PreviewDocumentResponse(BaseModel):
    folio: int
    ticket: str
    titulo: str
    version_documento: str
    fecha_version: str
    secciones: list[PreviewSectionResponse]
    control_versiones: list[PreviewVersionRowResponse]
    firmas: PreviewFirmasResponse

    @classmethod
    def from_domain(cls, document: PreviewDocument) -> PreviewDocumentResponse:
        return cls(
            folio=document.folio,
            ticket=document.ticket,
            titulo=document.title,
            version_documento=document.document_version,
            fecha_version=document.version_date,
            secciones=[
                PreviewSectionResponse.from_domain(section)
                for section in document.sections
            ],
            control_versiones=[
                PreviewVersionRowResponse.from_domain(row)
                for row in document.version_control
            ],
            firmas=PreviewFirmasResponse.from_domain(document.signatures),
        )
