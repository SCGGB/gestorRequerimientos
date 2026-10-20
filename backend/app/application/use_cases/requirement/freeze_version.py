from datetime import date

from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.requirement.requirement import Requirement


class FreezeAndAdvance:
    """Congela la version de trabajo y crea la sucesora por copy-on-write."""

    def __init__(self, repository: RequirementRepository, audit: AuditRecorderPort) -> None:
        self._repository = repository
        self._audit = audit

    def execute(
        self,
        requirement_id: int,
        *,
        principal: Principal,
        document_version: str,
        version_date: date,
        title: str | None = None,
    ) -> Requirement:
        requirement = self._repository.get(requirement_id)
        frozen = requirement.current_version()
        if title is None:
            title = frozen.title if frozen is not None else ""
        updated = requirement.freeze_and_advance(
            document_version=document_version,
            version_date=version_date,
            title=title,
        )
        saved = self._repository.save(updated, actor=principal.user_id)
        self._audit.record(
            AuditEntry(
                entity="REQ_VERSION",
                entity_id=frozen.id if frozen is not None else None,
                action=AuditAction.VERSION_FREEZE,
                actor=principal.user_id,
                detail={
                    "numero_version": frozen.number if frozen is not None else None,
                    "version_documento": document_version,
                },
            )
        )
        return saved
