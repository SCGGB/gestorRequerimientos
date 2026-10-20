from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement._common import principal_roles
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.auth.authorization import ensure_transition_allowed
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.requirement import Requirement


class ChangeStatus:
    """Aplica una transicion de estado permitida del dominio (endpoint legacy ``/estado``)."""

    def __init__(self, repository: RequirementRepository, audit: AuditRecorderPort) -> None:
        self._repository = repository
        self._audit = audit

    def execute(
        self,
        requirement_id: int,
        target: RequirementStatus,
        *,
        principal: Principal,
    ) -> Requirement:
        # Mismo criterio que /transicionar: 403 de rol antes de cargar o persistir.
        ensure_transition_allowed(principal_roles(principal), target)
        requirement = self._repository.get(requirement_id)
        previous = requirement.status
        saved = self._repository.save(
            requirement.change_status(target), actor=principal.user_id
        )
        self._audit.record(
            AuditEntry(
                entity="REQ_REQUERIMIENTO",
                entity_id=requirement_id,
                action=AuditAction.STATE_TRANSITION,
                actor=principal.user_id,
                detail={
                    "estado_anterior": previous.value,
                    "estado_actual": target.value,
                },
            )
        )
        return saved
