class DomainError(Exception):
    """Error base del dominio del requerimiento."""


class InvalidStateTransitionError(DomainError):
    """Transicion de estado no permitida."""


class AuthorizationNotOnCurrentVersionError(DomainError):
    """La firma Autorizo solo se registra en la version vigente."""


class MultipleWorkingVersionsError(DomainError):
    """Solo puede existir una version de trabajo (no congelada) por requerimiento."""


class InvalidFolioError(DomainError):
    """El folio del requerimiento no es valido."""
