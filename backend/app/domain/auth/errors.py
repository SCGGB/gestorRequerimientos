from app.domain.requirement.errors import DomainError


class AccessDeniedError(DomainError):
    """El usuario autenticado no tiene permiso para la accion solicitada."""
