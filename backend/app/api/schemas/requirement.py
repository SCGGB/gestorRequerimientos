from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.application.use_cases.requirement.update_version import VersionEdit
from app.domain.requirement.attachment import Attachment
from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.items import Benefit, CollectionItem
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion


class RequirementCreate(BaseModel):
    folio: int
    titulo: str = Field(max_length=300)
    tipo_cambio_id: int
    sistema: str = Field(max_length=200)
    version_documento: str = Field(max_length=20)
    fecha_version: date


class VersionUpdate(BaseModel):
    titulo: str | None = Field(default=None, max_length=300)
    tipo_cambio_id: int | None = None
    sistema: str | None = Field(default=None, max_length=200)
    version_documento: str | None = Field(default=None, max_length=20)
    fecha_version: date | None = None
    necesidad_actual: str | None = None
    contexto_descripcion: str | None = None
    contexto_manejo_errores: str | None = None
    usuarios_permisos: str | None = None
    requisitos_futuros_aplica: bool | None = None
    requisitos_futuros_texto: str | None = None
    campos_dinamicos: dict[str, Any] | None = None

    def to_edit(self) -> VersionEdit:
        return VersionEdit(
            title=self.titulo,
            change_type_id=self.tipo_cambio_id,
            system=self.sistema,
            document_version=self.version_documento,
            version_date=self.fecha_version,
            current_need=self.necesidad_actual,
            context_description=self.contexto_descripcion,
            context_error_handling=self.contexto_manejo_errores,
            users_permissions=self.usuarios_permisos,
            future_requirements_applies=self.requisitos_futuros_aplica,
            future_requirements_text=self.requisitos_futuros_texto,
            dynamic_fields=self.campos_dinamicos,
        )


class NewVersionRequest(BaseModel):
    version_documento: str = Field(max_length=20)
    fecha_version: date
    titulo: str | None = Field(default=None, max_length=300)


class StatusChangeRequest(BaseModel):
    nuevo_estado: RequirementStatus


class SignatureCreate(BaseModel):
    rol: SignatureRole
    nombre: str = Field(max_length=150)
    cargo: str = Field(max_length=150)
    cargo_id: int | None = None


class CollectionItemResponse(BaseModel):
    id: int | None = None
    contenido: str
    orden: int
    activo: bool

    @classmethod
    def from_domain(cls, item: CollectionItem) -> CollectionItemResponse:
        return cls(id=item.id, contenido=item.content, orden=item.order, activo=item.active)


class BenefitResponse(CollectionItemResponse):
    tipo: BenefitKind

    @classmethod
    def from_domain(cls, item: CollectionItem) -> BenefitResponse:
        if not isinstance(item, Benefit):
            raise TypeError("BenefitResponse requiere un Benefit.")
        return cls(
            id=item.id,
            contenido=item.content,
            orden=item.order,
            activo=item.active,
            tipo=item.kind,
        )


class SignatureResponse(BaseModel):
    id: int | None = None
    rol: SignatureRole
    nombre: str
    cargo: str
    cargo_id: int | None = None

    @classmethod
    def from_domain(cls, signature: Signature) -> SignatureResponse:
        return cls(
            id=signature.id,
            rol=signature.role,
            nombre=signature.name,
            cargo=signature.position,
            cargo_id=signature.position_id,
        )


class AttachmentResponse(BaseModel):
    id: int | None = None
    nombre: str
    tipo_mime: str | None = None
    orden: int
    leyenda: str | None = None
    storage_key: str
    activo: bool

    @classmethod
    def from_domain(cls, attachment: Attachment) -> AttachmentResponse:
        return cls(
            id=attachment.id,
            nombre=attachment.name,
            tipo_mime=attachment.mime_type,
            orden=attachment.order,
            leyenda=attachment.caption,
            storage_key=attachment.storage_key,
            activo=attachment.active,
        )


class VersionResponse(BaseModel):
    id: int | None = None
    numero: int
    titulo: str
    tipo_cambio_id: int | None = None
    sistema: str | None = None
    version_documento: str
    fecha_version: date
    necesidad_actual: str | None = None
    contexto_descripcion: str | None = None
    contexto_manejo_errores: str | None = None
    usuarios_permisos: str | None = None
    requisitos_futuros_aplica: bool
    requisitos_futuros_texto: str | None = None
    campos_dinamicos: dict[str, Any] = Field(default_factory=dict)
    congelada: bool
    objetivos: list[CollectionItemResponse] = Field(default_factory=list)
    consideraciones: list[CollectionItemResponse] = Field(default_factory=list)
    beneficios: list[BenefitResponse] = Field(default_factory=list)
    restricciones: list[CollectionItemResponse] = Field(default_factory=list)
    volumetria: list[CollectionItemResponse] = Field(default_factory=list)
    riesgos: list[CollectionItemResponse] = Field(default_factory=list)
    requisitos_futuros: list[CollectionItemResponse] = Field(default_factory=list)
    firmas: list[SignatureResponse] = Field(default_factory=list)
    anexos: list[AttachmentResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, version: RequirementVersion) -> VersionResponse:
        return cls(
            id=version.id,
            numero=version.number,
            titulo=version.title,
            tipo_cambio_id=version.change_type_id,
            sistema=version.system,
            version_documento=version.document_version,
            fecha_version=version.version_date,
            necesidad_actual=version.current_need,
            contexto_descripcion=version.context_description,
            contexto_manejo_errores=version.context_error_handling,
            usuarios_permisos=version.users_permissions,
            requisitos_futuros_aplica=version.future_requirements_applies,
            requisitos_futuros_texto=version.future_requirements_text,
            campos_dinamicos=dict(version.dynamic_fields),
            congelada=version.frozen,
            objetivos=[
                CollectionItemResponse.from_domain(item) for item in version.objectives
            ],
            consideraciones=[
                CollectionItemResponse.from_domain(item) for item in version.considerations
            ],
            beneficios=[BenefitResponse.from_domain(item) for item in version.benefits],
            restricciones=[
                CollectionItemResponse.from_domain(item) for item in version.restrictions
            ],
            volumetria=[
                CollectionItemResponse.from_domain(item) for item in version.volumetry
            ],
            riesgos=[CollectionItemResponse.from_domain(item) for item in version.risks],
            requisitos_futuros=[
                CollectionItemResponse.from_domain(item)
                for item in version.future_requirements_items
            ],
            firmas=[SignatureResponse.from_domain(item) for item in version.signatures],
            anexos=[AttachmentResponse.from_domain(item) for item in version.attachments],
        )


class RequirementResponse(BaseModel):
    id: int
    folio: int
    ticket: str
    estado: RequirementStatus
    version_actual_id: int | None = None
    versiones: list[VersionResponse]

    @classmethod
    def from_domain(cls, requirement: Requirement) -> RequirementResponse:
        return cls(
            id=requirement.id or 0,
            folio=requirement.folio,
            ticket=requirement.ticket,
            estado=requirement.status,
            version_actual_id=requirement.current_version_id,
            versiones=[
                VersionResponse.from_domain(version) for version in requirement.versions
            ],
        )


class RequirementSummary(BaseModel):
    id: int
    folio: int
    ticket: str
    estado: RequirementStatus
    version_actual_id: int | None = None

    @classmethod
    def from_domain(cls, requirement: Requirement) -> RequirementSummary:
        return cls(
            id=requirement.id or 0,
            folio=requirement.folio,
            ticket=requirement.ticket,
            estado=requirement.status,
            version_actual_id=requirement.current_version_id,
        )


class RequirementPage(BaseModel):
    items: list[RequirementSummary]
    total: int
    page: int
    size: int
