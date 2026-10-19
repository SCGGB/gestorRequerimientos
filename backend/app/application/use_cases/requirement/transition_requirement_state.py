import logging
from dataclasses import dataclass

from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import RequirementStatus
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
    """Aplica una transicion de estado con validacion integral previa."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        target_state: str,
        *,
        reason: str | None = None,
        actor_id: int | None = None,
    ) -> TransitionOutcome:
        requirement = self._repository.get(requirement_id)
        previous = requirement.status
        target = self._parse_target(target_state)
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

        saved = self._repository.save(requirement.change_status(target))
        logger.info(
            "Transicion %s -> %s (requerimiento=%s, motivo=%s, actor_id=%s)",
            previous.value,
            target.value,
            requirement_id,
            reason,
            actor_id,
        )
        return TransitionOutcome(
            previous_status=previous,
            current_status=saved.status,
            is_valid=True,
        )

    @staticmethod
    def _parse_target(target_state: str) -> RequirementStatus | None:
        try:
            return RequirementStatus(target_state)
        except ValueError:
            return None
