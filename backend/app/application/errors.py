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
