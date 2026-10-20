from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from itertools import count

import pytest

from app.application.errors import (
    SelfDeactivationError,
    UsernameTakenError,
)
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.password_hasher import PasswordHasherPort
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.users import CreateUser, ListUsers, UpdateUser
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.auth.roles import Role
from app.domain.auth.user import User

ADMIN = Principal(user_id="admin", roles=frozenset({"ADMIN"}))


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._ids = count(1)

    def get_by_username(self, username: str) -> User | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def list_all(self) -> Sequence[User]:
        return tuple(sorted(self._users.values(), key=lambda u: u.username))

    def save(self, user: User) -> User:
        for existing in self._users.values():
            if existing.username == user.username and existing.id != user.id:
                raise UsernameTakenError()
        assigned = replace(user, id=next(self._ids)) if user.id is None else user
        self._users[assigned.id] = assigned
        return assigned


class FakePasswordHasher(PasswordHasherPort):
    def hash(self, password: str) -> str:
        return f"fake${password}"

    def verify(self, password: str, encoded: str) -> bool:
        return encoded == f"fake${password}"


class FakeAuditRecorder(AuditRecorderPort):
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


def _create_case(
    repository: FakeUserRepository, audit: FakeAuditRecorder
) -> CreateUser:
    return CreateUser(repository, FakePasswordHasher(), audit)


def _update_case(
    repository: FakeUserRepository, audit: FakeAuditRecorder
) -> UpdateUser:
    return UpdateUser(repository, FakePasswordHasher(), audit)


def _seed_user(repository: FakeUserRepository, username: str = "ana") -> User:
    saved = repository.save(
        User(
            username=username,
            name=f"Usuario {username}",
            password_hash="fake$secreto123",
            roles=frozenset({Role.ELABORO}),
            failed_attempts=3,
        )
    )
    assert saved.id is not None
    return saved


def test_create_user_hashes_password_and_audits() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()

    created = _create_case(repository, audit).execute(
        ADMIN,
        usuario="luis",
        nombre="Luis",
        contrasena="clave1234",
        roles=frozenset({Role.REVISO}),
    )

    assert created.id is not None
    assert created.password_hash == "fake$clave1234"
    assert created.roles == frozenset({Role.REVISO})
    assert created.active is True

    entry = audit.entries[0]
    assert entry.action == AuditAction.USER_CREATE
    assert entry.actor == "admin"
    assert entry.entity_id == created.id
    assert entry.detail is not None
    assert entry.detail["usuario"] == "luis"
    assert entry.detail["roles"] == ["REVISO"]


def test_create_duplicate_username_raises() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()
    case = _create_case(repository, audit)
    case.execute(
        ADMIN,
        usuario="luis",
        nombre="Luis",
        contrasena="clave1234",
        roles=frozenset({Role.REVISO}),
    )

    with pytest.raises(UsernameTakenError):
        case.execute(
            ADMIN,
            usuario="luis",
            nombre="Luis 2",
            contrasena="clave1234",
            roles=frozenset({Role.ELABORO}),
        )


def test_update_resets_failed_attempts_and_audits_changes() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()
    user = _seed_user(repository)

    updated = _update_case(repository, audit).execute(
        ADMIN, user.id, nombre="Ana Editada"  # type: ignore[arg-type]
    )

    assert updated.name == "Ana Editada"
    assert updated.failed_attempts == 0
    entry = audit.entries[0]
    assert entry.action == AuditAction.USER_UPDATE
    assert entry.detail is not None
    assert entry.detail["cambios"]["nombre"] == "Ana Editada"
    assert entry.detail["cambios"]["intentos_fallidos"] == 0


def test_update_changes_password_and_never_audits_it() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()
    user = _seed_user(repository)

    updated = _update_case(repository, audit).execute(
        ADMIN, user.id, contrasena="nueva1234"  # type: ignore[arg-type]
    )

    assert updated.password_hash == "fake$nueva1234"
    entry = audit.entries[0]
    assert entry.detail is not None
    assert entry.detail["cambios"]["contrasena"] == "cambiada"


def test_update_replaces_roles() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()
    user = _seed_user(repository)

    updated = _update_case(repository, audit).execute(
        ADMIN,
        user.id,  # type: ignore[arg-type]
        roles=frozenset({Role.ELABORO, Role.ADMIN}),
    )

    assert updated.roles == frozenset({Role.ELABORO, Role.ADMIN})


def test_self_deactivation_is_rejected() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()
    user = _seed_user(repository, username="admin")

    with pytest.raises(SelfDeactivationError):
        _update_case(repository, audit).execute(
            ADMIN, user.id, activo=False  # type: ignore[arg-type]
        )

    stored = repository.get(user.id)  # type: ignore[arg-type]
    assert stored is not None
    assert stored.active is True
    assert audit.entries == []


def test_deactivating_another_user_is_allowed() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()
    user = _seed_user(repository, username="ana")

    updated = _update_case(repository, audit).execute(
        ADMIN, user.id, activo=False  # type: ignore[arg-type]
    )

    assert updated.active is False


def test_list_users_returns_all() -> None:
    repository = FakeUserRepository()
    _seed_user(repository, username="bruno")
    _seed_user(repository, username="ana")

    users = ListUsers(repository).execute()

    assert [user.username for user in users] == ["ana", "bruno"]
