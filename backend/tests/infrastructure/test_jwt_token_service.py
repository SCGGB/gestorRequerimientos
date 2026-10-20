from datetime import UTC, datetime, timedelta

from app.domain.auth.roles import Role
from app.domain.auth.session import SESSION_TTL, Session
from app.infrastructure.adapters.jwt_token_service import JwtTokenService

SECRET = "test-secret"


def _service() -> JwtTokenService:
    return JwtTokenService(SECRET)


def _session(*, ttl: timedelta = SESSION_TTL) -> Session:
    issued = datetime.now(tz=UTC)
    return Session(
        user_id="ana",
        roles=frozenset({Role.ELABORO, Role.REVISO}),
        issued_at=issued,
        expires_at=issued + ttl,
    )


def test_issue_and_parse_round_trip() -> None:
    service = _service()
    session = _session()
    token = service.issue(session)
    parsed = service.parse(token)
    assert parsed is not None
    assert parsed.user_id == "ana"
    assert parsed.roles == frozenset({Role.ELABORO, Role.REVISO})
    assert parsed.expires_at - parsed.issued_at == SESSION_TTL


def test_parse_rejects_tampered_signature() -> None:
    service = _service()
    token = service.issue(_session())
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[:-1]}A"
    assert service.parse(tampered) is None


def test_parse_rejects_other_secret() -> None:
    token = _service().issue(_session())
    assert JwtTokenService("otro-secret").parse(token) is None


def test_parse_rejects_expired_token() -> None:
    service = _service()
    token = service.issue(_session(ttl=timedelta(seconds=-1)))
    assert service.parse(token) is None


def test_parse_rejects_alg_none() -> None:
    service = _service()
    token = service.issue(_session())
    _header, payload, _ = token.split(".")
    none_header = JwtTokenService._encode({"alg": "none", "typ": "JWT"})
    none_token = f"{none_header}.{payload}."
    assert service.parse(none_token) is None


def test_parse_rejects_malformed_token() -> None:
    service = _service()
    assert service.parse("no-es-un-token") is None
