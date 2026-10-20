import pytest

from app.domain.auth.authorization import (
    REQUIRED_ROLES,
    Action,
    ensure_authorized,
    ensure_signature_allowed,
    ensure_transition_allowed,
    required_roles,
)
from app.domain.auth.errors import AccessDeniedError
from app.domain.auth.roles import Role
from app.domain.requirement.enums import RequirementStatus, SignatureRole

ALL = frozenset(Role)


def _roles(*roles: Role) -> frozenset[Role]:
    return frozenset(roles)


def test_matrix_is_complete_for_every_action() -> None:
    assert set(REQUIRED_ROLES) == set(Action)


def test_read_allows_every_role() -> None:
    for role in Role:
        ensure_authorized(_roles(role), Action.READ)


def test_requirement_write_requires_elaboro_or_admin() -> None:
    ensure_authorized(_roles(Role.ELABORO), Action.REQUIREMENT_WRITE)
    ensure_authorized(_roles(Role.ADMIN), Action.REQUIREMENT_WRITE)
    for role in (Role.REVISO, Role.AUTORIZO):
        with pytest.raises(AccessDeniedError):
            ensure_authorized(_roles(role), Action.REQUIREMENT_WRITE)


def test_generate_documents_requires_autorizo_or_admin() -> None:
    ensure_authorized(_roles(Role.AUTORIZO), Action.GENERATE_DOCUMENTS)
    ensure_authorized(_roles(Role.ADMIN), Action.GENERATE_DOCUMENTS)
    for role in (Role.ELABORO, Role.REVISO):
        with pytest.raises(AccessDeniedError):
            ensure_authorized(_roles(role), Action.GENERATE_DOCUMENTS)


def test_download_documents_allows_every_role() -> None:
    for role in Role:
        ensure_authorized(_roles(role), Action.DOWNLOAD_DOCUMENTS)


def test_manage_users_requires_admin() -> None:
    ensure_authorized(_roles(Role.ADMIN), Action.MANAGE_USERS)
    for role in (Role.ELABORO, Role.REVISO, Role.AUTORIZO):
        with pytest.raises(AccessDeniedError):
            ensure_authorized(_roles(role), Action.MANAGE_USERS)


def test_union_of_roles_grants_permission() -> None:
    roles = _roles(Role.ELABORO, Role.AUTORIZO)
    ensure_authorized(roles, Action.REQUIREMENT_WRITE)
    ensure_authorized(roles, Action.GENERATE_DOCUMENTS)


def test_no_permission_raises_access_denied() -> None:
    with pytest.raises(AccessDeniedError):
        ensure_authorized(_roles(Role.REVISO), Action.REQUIREMENT_WRITE)


def test_transition_roles_by_target_status() -> None:
    ensure_transition_allowed(_roles(Role.ELABORO), RequirementStatus.EN_REVISION)
    ensure_transition_allowed(_roles(Role.ADMIN), RequirementStatus.EN_REVISION)
    ensure_transition_allowed(_roles(Role.REVISO), RequirementStatus.VALIDADO)
    ensure_transition_allowed(_roles(Role.AUTORIZO), RequirementStatus.APROBADO)
    ensure_transition_allowed(_roles(Role.AUTORIZO), RequirementStatus.GENERADO)
    ensure_transition_allowed(_roles(Role.ADMIN), RequirementStatus.CANCELADO)

    with pytest.raises(AccessDeniedError):
        ensure_transition_allowed(_roles(Role.REVISO), RequirementStatus.EN_REVISION)
    with pytest.raises(AccessDeniedError):
        ensure_transition_allowed(_roles(Role.ELABORO), RequirementStatus.VALIDADO)


def test_signature_only_its_own_role_and_admin_never() -> None:
    ensure_signature_allowed(_roles(Role.ELABORO), SignatureRole.ELABORO)
    ensure_signature_allowed(_roles(Role.REVISO), SignatureRole.REVISO)
    ensure_signature_allowed(_roles(Role.AUTORIZO), SignatureRole.AUTORIZO)

    with pytest.raises(AccessDeniedError):
        ensure_signature_allowed(_roles(Role.ELABORO), SignatureRole.REVISO)
    with pytest.raises(AccessDeniedError):
        ensure_signature_allowed(_roles(Role.AUTORIZO), SignatureRole.ELABORO)
    for signature_role in SignatureRole:
        with pytest.raises(AccessDeniedError):
            ensure_signature_allowed(_roles(Role.ADMIN), signature_role)


def test_required_roles_returns_matrix_value() -> None:
    assert required_roles(Action.MANAGE_USERS) == frozenset({Role.ADMIN})
    assert required_roles(Action.READ) == ALL
