from abc import ABC, abstractmethod

from app.domain.requirement.preview import PreviewDocument


class DocumentRendererPort(ABC):
    @abstractmethod
    def render_docx(self, document: PreviewDocument, template_version: str) -> bytes:
        """Renderiza el DOCX desde el contenido normalizado de la vista previa."""
        raise NotImplementedError
