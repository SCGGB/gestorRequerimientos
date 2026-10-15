from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.requirement import Requirement


class ChangeStatus:
    """Aplica una transicion de estado permitida del dominio."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        target: RequirementStatus,
    ) -> Requirement:
        requirement = self._repository.get(requirement_id)
        return self._repository.save(requirement.change_status(target))
