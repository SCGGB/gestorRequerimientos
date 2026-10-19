from abc import ABC, abstractmethod


class DocumentConverterPort(ABC):
    @abstractmethod
    def to_pdf(self, docx: bytes) -> bytes:
        """Convierte el DOCX generado al PDF equivalente."""
        raise NotImplementedError
