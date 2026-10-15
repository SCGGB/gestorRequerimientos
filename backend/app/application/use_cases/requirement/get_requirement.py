from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.requirement import Requirement


class GetRequirement:
    """Consulta el agregado completo; el adaptador traduce el 404."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(self, requirement_id: int) -> Requirement:
        return self._repository.get(requirement_id)
