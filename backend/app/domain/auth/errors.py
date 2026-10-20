class AuthDomainError(Exception):
    """Error base del dominio de autenticacion."""


class AccessDeniedError(AuthDomainError):
    """El usuario autenticado no tiene permiso para la accion solicitada."""
