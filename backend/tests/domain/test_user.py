import pytest

from app.domain.auth.roles import Role
from app.domain.auth.user import (
    InactiveUserError,
    SelfDeactivationError,
    User,
)

MAX_ATTEMPTS = 5


def _user(**overrides: object) -> User:
    defaults: dict[str, object] = {
        "username": "ana",
        "name": "Ana",
        "password_hash": "pbkdf2_sha256$1$s$h",
        "roles": frozenset({Role.ELABORO}),
        "active": True,
        "failed_attempts": 0,
        "id": 1,
    }
    defaults.update(overrides)
    return User(**defaults)  # type: ignore[arg-type]


def test_lock_after_max_attempts() -> None:
    user = _user(failed_attempts=MAX_ATTEMPTS - 1)
    assert not user.is_locked(MAX_ATTEMPTS)

    user = user.record_failed_attempt()
    assert user.failed_attempts == MAX_ATTEMPTS
    assert user.is_locked(MAX_ATTEMPTS)


def test_record_failed_attempt_returns_new_user() -> None:
    user = _user()
    updated = user.record_failed_attempt()
    assert user.failed_attempts == 0
    assert updated.failed_attempts == 1


def test_reset_failed_attempts() -> None:
    user = _user(failed_attempts=4).reset_failed_attempts()
    assert user.failed_attempts == 0
    assert not user.is_locked(MAX_ATTEMPTS)


def test_ensure_active_rejects_inactive_user() -> None:
    _user(active=True).ensure_active()
    with pytest.raises(InactiveUserError):
        _user(active=False).ensure_active()


def test_self_deactivation_is_rejected() -> None:
    user = _user(username="ana")
    with pytest.raises(SelfDeactivationError):
        user.ensure_can_be_deactivated_by("ana")


def test_deactivation_by_another_user_is_allowed() -> None:
    user = _user(username="ana")
    user.ensure_can_be_deactivated_by("admin")
