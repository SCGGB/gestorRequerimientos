from collections.abc import Sequence


class ApplicationError(Exception):
    """Error base de la capa de aplicacion."""


class RequirementNotFoundError(ApplicationError):
    """No existe el requerimiento solicitado."""


class VersionNotFoundError(ApplicationError):
    """La version no existe o no pertenece al agregado."""


class CollectionItemNotFoundError(ApplicationError):
    """No existe el elemento de coleccion indicado."""


class AttachmentNotFoundError(ApplicationError):
    """No existe el anexo indicado en la version."""


class DuplicateFolioError(ApplicationError):
    """El folio unico ya esta registrado."""


class DataConflictError(ApplicationError):
    """Violacion de integridad (FK/check) distinta de la unicidad de folio."""


class DocumentNotFoundError(ApplicationError):
    """No existe el documento generado solicitado."""


class DocumentGenerationError(ApplicationError):
    """Fallo al renderizar o convertir el documento generado."""

    def __init__(self, message: str = "No fue posible generar el documento.") -> None:
        super().__init__(message)


class DocumentGenerationNotAllowedError(ApplicationError):
    """El estado o las firmas del requerimiento no permiten generar el documento."""

    def __init__(self, message: str, *, issues: Sequence[str] = ()) -> None:
        super().__init__(message)
        self.issues: tuple[str, ...] = tuple(issues)
