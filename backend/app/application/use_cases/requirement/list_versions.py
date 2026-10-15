from collections.abc import Sequence

from app.application.errors import VersionNotFoundError
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.version import RequirementVersion


class ListVersions:
    """Historico de versiones de un requerimiento, ordenado por numero."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(self, requirement_id: int) -> Sequence[RequirementVersion]:
        requirement = self._repository.get(requirement_id)
        return tuple(sorted(requirement.versions, key=lambda version: version.number))


class GetVersion:
    """Detalle de una version del requerimiento por su id."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(self, requirement_id: int, version_id: int) -> RequirementVersion:
        requirement = self._repository.get(requirement_id)
        version = requirement.version_by_id(version_id)
        if version is None:
            raise VersionNotFoundError()
        return version
