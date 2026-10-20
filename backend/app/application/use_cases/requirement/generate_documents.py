from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime

from app.application.errors import (
    DocumentGenerationNotAllowedError,
    VersionNotFoundError,
)
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.document_converter import DocumentConverterPort
from app.application.ports.document_renderer import DocumentRendererPort
from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.requirement.document import (
    MIME_TYPES,
    DocumentFormat,
    GeneratedDocument,
    build_file_name,
)
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.errors import InvalidStateTransitionError
from app.domain.requirement.preview import build_preview_document
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.validation import validate_requirement
from app.domain.requirement.version import RequirementVersion

_GENERATABLE_STATUSES = (RequirementStatus.APROBADO, RequirementStatus.GENERADO)
_FORMATS: tuple[DocumentFormat, ...] = ("DOCX", "PDF")


class GenerateRequirementDocuments:
    """Genera el DOCX y su PDF equivalente desde una version persistida."""

    def __init__(
        self,
        repository: RequirementRepository,
        document_repository: RequirementDocumentRepository,
        renderer: DocumentRendererPort,
        converter: DocumentConverterPort,
        audit: AuditRecorderPort,
        *,
        template_version: str,
    ) -> None:
        self._repository = repository
        self._document_repository = document_repository
        self._renderer = renderer
        self._converter = converter
        self._audit = audit
        self._template_version = template_version

    def execute(
        self,
        requirement_id: int,
        *,
        principal: Principal,
        version_id: int | None = None,
    ) -> Sequence[GeneratedDocument]:
        requirement = self._repository.get(requirement_id)
        version = self._resolve_version(requirement, version_id)
        self._ensure_generatable(requirement)

        preview = build_preview_document(requirement, version)
        docx = self._renderer.render_docx(preview, self._template_version)
        pdf = self._converter.to_pdf(docx)

        generated_at = datetime.now()
        contents: tuple[tuple[DocumentFormat, bytes], ...] = (("DOCX", docx), ("PDF", pdf))
        documents = tuple(
            self._store(
                requirement_id,
                requirement,
                version,
                file_format,
                content,
                generated_at,
                principal.user_id,
            )
            for file_format, content in contents
        )

        if requirement.status is RequirementStatus.APROBADO:
            self._repository.save(
                requirement.change_status(RequirementStatus.GENERADO),
                actor=principal.user_id,
            )
        return documents

    def _store(
        self,
        requirement_id: int,
        requirement: Requirement,
        version: RequirementVersion,
        file_format: DocumentFormat,
        content: bytes,
        generated_at: datetime,
        actor: str,
    ) -> GeneratedDocument:
        if version.id is None:
            raise VersionNotFoundError()
        document = GeneratedDocument(
            requirement_id=requirement_id,
            version_id=version.id,
            format=file_format,
            template_version=self._template_version,
            file_name=build_file_name(requirement.folio, version.document_version, file_format),
            mime_type=MIME_TYPES[file_format],
            size_bytes=len(content),
            generated_at=generated_at,
            generated_by=actor,
            content=content,
        )
        document_id = self._document_repository.add(document, actor=actor)
        self._audit.record(
            AuditEntry(
                entity="REQ_DOCUMENTO",
                entity_id=document_id,
                action=AuditAction.DOCUMENT_GENERATED,
                actor=actor,
                detail={
                    "formato": file_format,
                    "nombre_archivo": document.file_name,
                    "version_id": version.id,
                },
            )
        )
        return replace(document, id=document_id, content=None)

    @staticmethod
    def _resolve_version(
        requirement: Requirement, version_id: int | None
    ) -> RequirementVersion:
        if version_id is None:
            version = requirement.current_version()
        else:
            version = requirement.version_by_id(version_id)
        if version is None:
            raise VersionNotFoundError()
        return version

    @staticmethod
    def _ensure_generatable(requirement: Requirement) -> None:
        if requirement.status not in _GENERATABLE_STATUSES:
            raise InvalidStateTransitionError(
                "La generacion solo esta permitida cuando el requerimiento esta APROBADO."
            )
        validation = validate_requirement(requirement, target_state=RequirementStatus.GENERADO)
        if not validation.is_valid:
            raise DocumentGenerationNotAllowedError(
                "El requerimiento no cumple las precondiciones para generar el documento.",
                issues=[issue.message for issue in validation.errors],
            )
