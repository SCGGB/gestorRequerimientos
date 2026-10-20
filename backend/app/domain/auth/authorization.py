from enum import StrEnum

from app.domain.auth.errors import AccessDeniedError
from app.domain.auth.roles import Role
from app.domain.requirement.enums import RequirementStatus, SignatureRole


class Action(StrEnum):
    """Acciones del dominio sujetas a la matriz de autorizacion."""

    READ = "READ"
    REQUIREMENT_WRITE = "REQUIREMENT_WRITE"
    GENERATE_DOCUMENTS = "GENERATE_DOCUMENTS"
    DOWNLOAD_DOCUMENTS = "DOWNLOAD_DOCUMENTS"
    MANAGE_USERS = "MANAGE_USERS"


_ELABORO = Role.ELABORO
_REVISO = Role.REVISO
_AUTORIZO = Role.AUTORIZO
_ADMIN = Role.ADMIN

_ALL_ROLES = frozenset({_ELABORO, _REVISO, _AUTORIZO, _ADMIN})
_EDITORS = frozenset({_ELABORO, _ADMIN})
_AUTHORIZERS = frozenset({_AUTORIZO, _ADMIN})

REQUIRED_ROLES: dict[Action, frozenset[Role]] = {
    Action.READ: _ALL_ROLES,
    Action.REQUIREMENT_WRITE: _EDITORS,
    Action.GENERATE_DOCUMENTS: _AUTHORIZERS,
    Action.DOWNLOAD_DOCUMENTS: _ALL_ROLES,
    Action.MANAGE_USERS: frozenset({_ADMIN}),
}

_TRANSITION_ROLES: dict[RequirementStatus, frozenset[Role]] = {
    RequirementStatus.EN_REVISION: _EDITORS,
    RequirementStatus.VALIDADO: frozenset({_REVISO, _ADMIN}),
    RequirementStatus.APROBADO: _AUTHORIZERS,
    RequirementStatus.GENERADO: _AUTHORIZERS,
    RequirementStatus.CANCELADO: _AUTHORIZERS,
}

_SIGNATURE_ROLES: dict[SignatureRole, frozenset[Role]] = {
    SignatureRole.ELABORO: frozenset({_ELABORO}),
    SignatureRole.REVISO: frozenset({_REVISO}),
    SignatureRole.AUTORIZO: frozenset({_AUTORIZO}),
}


def _matches(roles: frozenset[Role], required: frozenset[Role]) -> bool:
    return bool(roles & required)


def required_roles(action: Action) -> frozenset[Role]:
    """Roles que habilitan una accion (matriz aprobada, sin herencia implicita)."""
    return REQUIRED_ROLES[action]


def ensure_authorized(roles: frozenset[Role], action: Action) -> None:
    """Valida que la union de roles cubra la accion; si no, AccessDeniedError."""
    if not _matches(roles, required_roles(action)):
        raise AccessDeniedError("El usuario no tiene permiso para esta accion.")


def ensure_transition_allowed(
    roles: frozenset[Role], target_status: RequirementStatus
) -> None:
    """Valida el rol que puede ejecutar la transicion hacia el estado destino."""
    required = _TRANSITION_ROLES.get(target_status, frozenset())
    if not _matches(roles, required):
        raise AccessDeniedError(
            "El usuario no tiene permiso para ejecutar esta transicion."
        )


def ensure_signature_allowed(
    roles: frozenset[Role], requested_role: SignatureRole
) -> None:
    """Valida que el rol del usuario corresponda a la firma solicitada (ADMIN nunca firma)."""
    if not _matches(roles, _SIGNATURE_ROLES[requested_role]):
        raise AccessDeniedError(
            "El usuario no tiene permiso para registrar esta firma."
        )
