from collections.abc import Sequence

from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.document import GeneratedDocument


class ListRequirementDocuments:
    """Historico de documentos generados de un requerimiento (sin binario)."""

    def __init__(
        self,
        repository: RequirementRepository,
        document_repository: RequirementDocumentRepository,
    ) -> None:
        self._repository = repository
        self._document_repository = document_repository

    def execute(self, requirement_id: int) -> Sequence[GeneratedDocument]:
        self._repository.get(requirement_id)
        return self._document_repository.list_by_requirement(requirement_id)
