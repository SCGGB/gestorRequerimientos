from app.application.errors import VersionNotFoundError
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.validation import ValidationResult, validate_requirement


class ValidateRequirementVersion:
    """Valida una version sin persistir cambios (dry-run)."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        *,
        target_state: RequirementStatus | None = None,
    ) -> ValidationResult:
        requirement = self._repository.get(requirement_id)
        if requirement.version_by_id(version_id) is None:
            raise VersionNotFoundError()
        return validate_requirement(requirement, target_state=target_state)
