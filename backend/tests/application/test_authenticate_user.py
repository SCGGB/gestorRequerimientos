from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from itertools import count

import pytest

from app.application.errors import (
    AccountLockedError,
    InvalidCredentialsError,
    UsernameTakenError,
)
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.password_hasher import PasswordHasherPort
from app.application.ports.token_service import TokenServicePort
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.auth import AuthenticateUser
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.auth.roles import Role
from app.domain.auth.session import Session
from app.domain.auth.user import User

TTL_HOURS = 8
MAX_ATTEMPTS = 5


class FakeUserRepository(UserRepository):
    def __init__(self, users: Sequence[User] = ()) -> None:
        self._users: dict[int, User] = {}
        self._ids = count(1)
        for user in users:
            self.save(user)

    def get_by_username(self, username: str) -> User | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def list_all(self) -> Sequence[User]:
        return tuple(self._users.values())

    def save(self, user: User) -> User:
        for existing in self._users.values():
            if existing.username == user.username and existing.id != user.id:
                raise UsernameTakenError()
        assigned = replace(user, id=next(self._ids)) if user.id is None else user
        self._users[assigned.id] = assigned
        return assigned


class FakePasswordHasher(PasswordHasherPort):
    """Hash trivial para pruebas: el 'hash' es la clave en claro con prefijo."""

    def hash(self, password: str) -> str:
        return f"fake${password}"

    def verify(self, password: str, encoded: str) -> bool:
        return encoded == f"fake${password}"


class FakeTokenService(TokenServicePort):
    def __init__(self) -> None:
        self.issued: list[Session] = []

    def issue(self, session: Session) -> str:
        self.issued.append(session)
        return f"token-{session.user_id}"

    def parse(self, token: str) -> Session | None:
        return None


class FakeAuditRecorder(AuditRecorderPort):
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


def _user(
    username: str = "ana",
    *,
    roles: frozenset[Role] = frozenset({Role.ELABORO}),
    failed_attempts: int = 0,
    active: bool = True,
    password: str = "secreto123",
) -> User:
    return User(
        username=username,
        name=f"Usuario {username}",
        password_hash=f"fake${password}",
        roles=roles,
        active=active,
        failed_attempts=failed_attempts,
    )


def _use_case(
    repository: UserRepository,
    audit: FakeAuditRecorder,
    hasher: PasswordHasherPort | None = None,
    tokens: TokenServicePort | None = None,
) -> tuple[AuthenticateUser, FakeTokenService]:
    token_service = tokens or FakeTokenService()
    case = AuthenticateUser(
        repository,
        hasher or FakePasswordHasher(),
        token_service,
        audit,
        session_ttl_hours=TTL_HOURS,
        max_failed_attempts=MAX_ATTEMPTS,
    )
    assert isinstance(token_service, FakeTokenService)
    return case, token_service


def test_success_issues_token_with_roles_and_eight_hours() -> None:
    repository = FakeUserRepository(
        [_user(roles=frozenset({Role.ELABORO, Role.ADMIN}))]
    )
    audit = FakeAuditRecorder()
    case, tokens = _use_case(repository, audit)

    token = case.execute("ana", "secreto123")

    assert token == "token-ana"
    session = tokens.issued[0]
    assert session.user_id == "ana"
    assert session.roles == frozenset({Role.ELABORO, Role.ADMIN})
    ttl = session.expires_at - session.issued_at
    assert ttl.total_seconds() == TTL_HOURS * 3600

    assert len(audit.entries) == 1
    entry = audit.entries[0]
    assert entry.action == AuditAction.LOGIN_SUCCESS
    assert entry.actor == "ana"


def test_success_resets_failed_attempts() -> None:
    repository = FakeUserRepository([_user(failed_attempts=4)])
    audit = FakeAuditRecorder()
    case, _ = _use_case(repository, audit)

    case.execute("ana", "secreto123")

    stored = repository.get_by_username("ana")
    assert stored is not None
    assert stored.failed_attempts == 0


def test_unknown_user_gets_unique_error_and_is_audited() -> None:
    repository = FakeUserRepository()
    audit = FakeAuditRecorder()
    case, _ = _use_case(repository, audit)

    with pytest.raises(InvalidCredentialsError) as exc_info:
        case.execute("fantasma", "secreto123")

    assert str(exc_info.value) == "Usuario o contrasena incorrectos."
    assert audit.entries[0].action == AuditAction.LOGIN_FAILED
    assert audit.entries[0].actor == "fantasma"


def test_wrong_password_increments_and_persists_attempts() -> None:
    repository = FakeUserRepository([_user(failed_attempts=1)])
    audit = FakeAuditRecorder()
    case, _ = _use_case(repository, audit)

    with pytest.raises(InvalidCredentialsError):
        case.execute("ana", "mala")

    stored = repository.get_by_username("ana")
    assert stored is not None
    assert stored.failed_attempts == 2
    assert audit.entries[0].action == AuditAction.LOGIN_FAILED
    assert audit.entries[0].detail is not None
    assert audit.entries[0].detail["intentos"] == 2


def test_locked_account_raises_account_locked_without_verifying() -> None:
    repository = FakeUserRepository([_user(failed_attempts=MAX_ATTEMPTS)])
    audit = FakeAuditRecorder()
    case, _ = _use_case(repository, audit)

    with pytest.raises(AccountLockedError):
        case.execute("ana", "secreto123")

    assert audit.entries[0].action == AuditAction.LOGIN_BLOCKED


def test_inactive_user_is_rejected_without_revealing() -> None:
    repository = FakeUserRepository([_user(active=False)])
    audit = FakeAuditRecorder()
    case, _ = _use_case(repository, audit)

    with pytest.raises(InvalidCredentialsError) as exc_info:
        case.execute("ana", "secreto123")

    assert str(exc_info.value) == "Usuario o contrasena incorrectos."


def test_inactive_locked_user_shows_blocked_before_inactive() -> None:
    repository = FakeUserRepository(
        [_user(active=False, failed_attempts=MAX_ATTEMPTS)]
    )
    audit = FakeAuditRecorder()
    case, _ = _use_case(repository, audit)

    with pytest.raises(AccountLockedError):
        case.execute("ana", "secreto123")
