from app.application.errors import VersionNotFoundError
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import parse_status
from app.domain.requirement.validation import (
    ValidationIssue,
    ValidationResult,
    validate_requirement,
)


class ValidateRequirementVersion:
    """Valida una version sin persistir cambios (dry-run)."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        *,
        target_state: str | None = None,
    ) -> ValidationResult:
        requirement = self._repository.get(requirement_id)
        if requirement.version_by_id(version_id) is None:
            raise VersionNotFoundError()

        if target_state is None:
            return validate_requirement(requirement)

        target = parse_status(target_state)
        if target is None:
            return ValidationResult(
                errors=(
                    ValidationIssue(
                        path="a_estado",
                        code="unknown_target_state",
                        message=f"El estado destino '{target_state}' no es valido.",
                        section="Maquina de estados",
                    ),
                )
            )
        return validate_requirement(requirement, target_state=target)
