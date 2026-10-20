import base64
import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.application.ports.token_service import TokenServicePort
from app.domain.auth.roles import Role
from app.domain.auth.session import Session

_ALGORITHM = "HS256"


class JwtTokenService(TokenServicePort):
    """Emite y verifica tokens JWT HS256 con la stdlib (sin dependencias)."""

    def __init__(self, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    def issue(self, session: Session) -> str:
        header = {"alg": _ALGORITHM, "typ": "JWT"}
        payload: dict[str, Any] = {
            "sub": session.user_id,
            "roles": sorted(role.value for role in session.roles),
            "iat": int(session.issued_at.timestamp()),
            "exp": int(session.expires_at.timestamp()),
        }
        signing_input = f"{self._encode(header)}.{self._encode(payload)}"
        signature = self._sign(signing_input)
        return f"{signing_input}.{signature}"

    def parse(self, token: str) -> Session | None:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature = parts
        if not hmac.compare_digest(signature, self._sign(f"{header_b64}.{payload_b64}")):
            return None

        header = self._decode(header_b64)
        payload = self._decode(payload_b64)
        if header is None or payload is None:
            return None
        if header.get("alg") != _ALGORITHM:
            return None

        try:
            user_id = payload["sub"]
            issued_at = datetime.fromtimestamp(int(payload["iat"]), tz=UTC)
            expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
            roles = frozenset(Role(value) for value in payload["roles"])
        except (KeyError, TypeError, ValueError):
            return None

        if not isinstance(user_id, str):
            return None
        session = Session(
            user_id=user_id,
            roles=roles,
            issued_at=issued_at,
            expires_at=expires_at,
        )
        if session.is_expired(datetime.now(tz=UTC)):
            return None
        return session

    def _sign(self, signing_input: str) -> str:
        digest = hmac.new(
            self._secret, signing_input.encode("ascii"), hashlib.sha256
        ).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    @staticmethod
    def _encode(data: Mapping[str, Any]) -> str:
        raw = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    @staticmethod
    def _decode(segment: str) -> dict[str, Any] | None:
        padding = "=" * (-len(segment) % 4)
        try:
            raw = base64.urlsafe_b64decode(segment + padding)
            data = json.loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(data, dict):
            return None
        return data
