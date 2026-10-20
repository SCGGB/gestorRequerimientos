from app.application.errors import DocumentNotFoundError
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.requirement.document import GeneratedDocument


class GetRequirementDocument:
    """Recupera un documento del requerimiento con su binario para descarga."""

    def __init__(
        self,
        repository: RequirementRepository,
        document_repository: RequirementDocumentRepository,
        audit: AuditRecorderPort,
    ) -> None:
        self._repository = repository
        self._document_repository = document_repository
        self._audit = audit

    def execute(
        self,
        requirement_id: int,
        document_id: int,
        *,
        principal: Principal,
    ) -> GeneratedDocument:
        self._repository.get(requirement_id)
        document = self._document_repository.get(document_id)
        if document.requirement_id != requirement_id:
            raise DocumentNotFoundError()
        self._audit.record(
            AuditEntry(
                entity="REQ_DOCUMENTO",
                entity_id=document.id,
                action=AuditAction.DOCUMENT_DOWNLOADED,
                actor=principal.user_id,
                detail={"nombre_archivo": document.file_name},
            )
        )
        return document
