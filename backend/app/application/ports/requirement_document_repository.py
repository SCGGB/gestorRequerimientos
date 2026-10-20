from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.requirement.document import GeneratedDocument


class RequirementDocumentRepository(ABC):
    @abstractmethod
    def add(self, document: GeneratedDocument, *, actor: str) -> int:
        """Registra un documento generado y devuelve su id (``actor`` en auditoria)."""
        raise NotImplementedError

    @abstractmethod
    def get(self, document_id: int) -> GeneratedDocument:
        """Recupera un documento con su binario para descarga."""
        raise NotImplementedError

    @abstractmethod
    def list_by_requirement(self, requirement_id: int) -> Sequence[GeneratedDocument]:
        """Historico de documentos del requerimiento, sin binario."""
        raise NotImplementedError
