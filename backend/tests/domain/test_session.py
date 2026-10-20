from datetime import datetime, timedelta

from app.domain.auth.roles import Role
from app.domain.auth.session import SESSION_TTL, Session


def _session(issued_at: datetime) -> Session:
    return Session(
        user_id="ana",
        roles=frozenset({Role.ELABORO}),
        issued_at=issued_at,
        expires_at=issued_at + SESSION_TTL,
    )


def test_session_ttl_is_eight_hours() -> None:
    assert SESSION_TTL == timedelta(hours=8)


def test_session_not_expired_before_expiry() -> None:
    issued = datetime(2026, 10, 20, 8, 0, 0)
    session = _session(issued)
    assert not session.is_expired(issued + timedelta(hours=7))
    assert session.is_expired(issued + timedelta(hours=8))
    assert session.is_expired(issued + timedelta(hours=9))
