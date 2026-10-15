from datetime import date

from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion


class CreateRequirement:
    """Crea un requerimiento con su version 1 de trabajo en BORRADOR."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        folio: int,
        title: str,
        change_type_id: int,
        system: str,
        document_version: str,
        version_date: date,
    ) -> Requirement:
        version = RequirementVersion(
            number=1,
            document_version=document_version,
            version_date=version_date,
            title=title,
            change_type_id=change_type_id,
            system=system,
        )
        requirement = Requirement(
            folio=folio,
            status=RequirementStatus.BORRADOR,
            versions=(version,),
        )
        return self._repository.save(requirement)
