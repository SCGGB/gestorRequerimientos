from app.application.errors import VersionNotFoundError
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.preview import PreviewDocument, build_preview_document


class BuildPreviewDocument:
    """Compone la vista previa de una version persistida (solo lectura)."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(self, requirement_id: int, version_id: int) -> PreviewDocument:
        requirement = self._repository.get(requirement_id)
        version = requirement.version_by_id(version_id)
        if version is None:
            raise VersionNotFoundError()
        return build_preview_document(requirement, version)
