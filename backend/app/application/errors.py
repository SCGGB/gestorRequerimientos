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


class UsernameTakenError(ApplicationError):
    """El nombre de usuario ya esta registrado."""

    def __init__(self, message: str = "El nombre de usuario ya esta registrado.") -> None:
        super().__init__(message)


class NotAuthenticatedError(ApplicationError):
    """No hay sesion valida (sin token, token invalido/expirado o usuario inactivo)."""

    def __init__(self, message: str = "Se requiere autenticacion.") -> None:
        super().__init__(message)


class InvalidCredentialsError(ApplicationError):
    """Credenciales invalidas; el mensaje unico no revela existencia de la cuenta."""

    def __init__(
        self, message: str = "Usuario o contrasena incorrectos."
    ) -> None:
        super().__init__(message)


class AccountLockedError(ApplicationError):
    """La cuenta alcanzo el maximo de intentos fallidos."""

    def __init__(
        self,
        message: str = (
            "La cuenta esta bloqueada por intentos fallidos. "
            "Contacte al administrador."
        ),
    ) -> None:
        super().__init__(message)


class UserNotFoundError(ApplicationError):
    """No existe el usuario solicitado."""

    def __init__(self, message: str = "No existe el usuario solicitado.") -> None:
        super().__init__(message)


class SelfDeactivationError(ApplicationError):
    """Un usuario no puede desactivarse a si mismo."""

    def __init__(
        self, message: str = "Un usuario no puede desactivarse a si mismo."
    ) -> None:
        super().__init__(message)
