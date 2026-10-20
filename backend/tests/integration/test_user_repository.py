from __future__ import annotations

from dataclasses import replace

import pytest
from sqlalchemy.engine import Engine

from app.application.errors import UsernameTakenError
from app.domain.auth.roles import Role
from app.domain.auth.user import User
from app.infrastructure.adapters.user_repository import SqlAlchemyUserRepository

pytestmark = pytest.mark.integration


@pytest.fixture()
def repository(migrated_engine: Engine) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(migrated_engine)


def _user(
    username: str,
    *,
    roles: frozenset[Role] = frozenset({Role.ELABORO}),
    failed_attempts: int = 0,
    active: bool = True,
) -> User:
    return User(
        username=username,
        name=f"Usuario {username}",
        password_hash="pbkdf2_sha256$200000$c2FsdA==$aGFzaA==",
        roles=roles,
        active=active,
        failed_attempts=failed_attempts,
    )


def test_round_trip_multi_role_user_with_failed_attempts(
    repository: SqlAlchemyUserRepository,
) -> None:
    saved = repository.save(
        _user(
            "repo-user-1",
            roles=frozenset({Role.ELABORO, Role.ADMIN}),
            failed_attempts=3,
        )
    )

    assert saved.id is not None
    loaded = repository.get(saved.id)
    assert loaded == saved
    assert loaded is not None
    assert loaded.roles == frozenset({Role.ELABORO, Role.ADMIN})
    assert loaded.failed_attempts == 3

    by_username = repository.get_by_username("repo-user-1")
    assert by_username == saved


def test_save_replaces_roles_by_set_difference(
    repository: SqlAlchemyUserRepository,
) -> None:
    saved = repository.save(_user("repo-user-2", roles=frozenset({Role.ELABORO})))
    assert saved.id is not None

    updated = repository.save(
        replace(saved, roles=frozenset({Role.REVISO, Role.AUTORIZO}))
    )

    assert updated.roles == frozenset({Role.REVISO, Role.AUTORIZO})
    reloaded = repository.get(saved.id)
    assert reloaded is not None
    assert reloaded.roles == frozenset({Role.REVISO, Role.AUTORIZO})


def test_deactivation_is_logical(repository: SqlAlchemyUserRepository) -> None:
    saved = repository.save(_user("repo-user-3"))
    assert saved.id is not None

    deactivated = repository.save(replace(saved, active=False, failed_attempts=5))

    assert deactivated.active is False
    assert deactivated.failed_attempts == 5
    assert repository.get(saved.id) is not None


def test_duplicate_username_raises_username_taken(
    repository: SqlAlchemyUserRepository,
) -> None:
    repository.save(_user("repo-duplicate"))

    with pytest.raises(UsernameTakenError):
        repository.save(_user("repo-duplicate", roles=frozenset({Role.REVISO})))


def test_list_all_orders_by_username(repository: SqlAlchemyUserRepository) -> None:
    repository.save(_user("repo-user-b"))
    repository.save(_user("repo-user-a"))

    usernames = [user.username for user in repository.list_all()]
    assert "repo-user-a" in usernames
    assert "repo-user-b" in usernames
    assert usernames == sorted(usernames)
