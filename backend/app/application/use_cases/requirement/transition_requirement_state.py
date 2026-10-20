import logging
from dataclasses import dataclass

from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement._common import principal_roles
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.auth.authorization import ensure_transition_allowed
from app.domain.requirement.enums import RequirementStatus, parse_status
from app.domain.requirement.requirement import allowed_transitions
from app.domain.requirement.validation import ValidationIssue, validate_requirement

logger = logging.getLogger(__name__)

_FORWARD_TRANSITIONS: frozenset[tuple[RequirementStatus, RequirementStatus]] = frozenset(
    {
        (RequirementStatus.BORRADOR, RequirementStatus.EN_REVISION),
        (RequirementStatus.EN_REVISION, RequirementStatus.VALIDADO),
        (RequirementStatus.VALIDADO, RequirementStatus.APROBADO),
        (RequirementStatus.APROBADO, RequirementStatus.GENERADO),
    }
)


@dataclass(frozen=True, slots=True)
class TransitionOutcome:
    """Resultado estructurado de un intento de transicion."""

    previous_status: RequirementStatus
    current_status: RequirementStatus
    is_valid: bool
    errors: tuple[ValidationIssue, ...] = ()


class TransitionRequirementState:
    """Aplica una transicion de estado con control de rol y validacion integral previa."""

    def __init__(self, repository: RequirementRepository, audit: AuditRecorderPort) -> None:
        self._repository = repository
        self._audit = audit

    def execute(
        self,
        requirement_id: int,
        target_state: str,
        *,
        principal: Principal,
        reason: str | None = None,
    ) -> TransitionOutcome:
        target = parse_status(target_state)
        if target is not None:
            # 403 antes de cargar o validar (CA-05): solo body + roles del principal.
            ensure_transition_allowed(principal_roles(principal), target)

        requirement = self._repository.get(requirement_id)
        previous = requirement.status
        if target is None:
            return TransitionOutcome(
                previous_status=previous,
                current_status=previous,
                is_valid=False,
                errors=(
                    ValidationIssue(
                        path="a_estado",
                        code="unknown_target_state",
                        message=f"El estado destino '{target_state}' no es valido.",
                        section="Maquina de estados",
                    ),
                ),
            )

        if target not in allowed_transitions(previous):
            return TransitionOutcome(
                previous_status=previous,
                current_status=previous,
                is_valid=False,
                errors=(
                    ValidationIssue(
                        path="a_estado",
                        code="invalid_transition",
                        message=(
                            "La transicion de "
                            f"{previous.value} a {target.value} no esta permitida."
                        ),
                        section="Maquina de estados",
                    ),
                ),
            )

        if (previous, target) in _FORWARD_TRANSITIONS:
            validation = validate_requirement(requirement, target_state=target)
            if not validation.is_valid:
                return TransitionOutcome(
                    previous_status=previous,
                    current_status=previous,
                    is_valid=False,
                    errors=validation.errors,
                )

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
                    "motivo": reason,
                },
            )
        )
        logger.info(
            "Transicion %s -> %s (requerimiento=%s, motivo=%s, actor=%s)",
            previous.value,
            target.value,
            requirement_id,
            reason,
            principal.user_id,
        )
        return TransitionOutcome(
            previous_status=previous,
            current_status=saved.status,
            is_valid=True,
        )
