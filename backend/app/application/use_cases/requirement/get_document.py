from app.application.errors import DocumentNotFoundError
from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.document import GeneratedDocument


class GetRequirementDocument:
    """Recupera un documento del requerimiento con su binario para descarga."""

    def __init__(
        self,
        repository: RequirementRepository,
        document_repository: RequirementDocumentRepository,
    ) -> None:
        self._repository = repository
        self._document_repository = document_repository

    def execute(self, requirement_id: int, document_id: int) -> GeneratedDocument:
        self._repository.get(requirement_id)
        document = self._document_repository.get(document_id)
        if document.requirement_id != requirement_id:
            raise DocumentNotFoundError()
        return document
