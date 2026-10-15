from datetime import date

from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.requirement import Requirement


class FreezeAndAdvance:
    """Congela la version de trabajo y crea la sucesora por copy-on-write."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        *,
        document_version: str,
        version_date: date,
        title: str | None = None,
    ) -> Requirement:
        requirement = self._repository.get(requirement_id)
        if title is None:
            current = requirement.current_version()
            title = current.title if current is not None else ""
        updated = requirement.freeze_and_advance(
            document_version=document_version,
            version_date=version_date,
            title=title,
        )
        return self._repository.save(updated)
