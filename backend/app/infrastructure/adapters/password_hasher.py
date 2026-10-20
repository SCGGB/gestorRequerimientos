import base64
import hashlib
import hmac
import secrets

from app.application.ports.password_hasher import PasswordHasherPort

_ALGORITHM = "pbkdf2_sha256"
_SALT_BYTES = 16


class Pbkdf2PasswordHasher(PasswordHasherPort):
    """Hashing de contrasenas con PBKDF2-HMAC-SHA256 (stdlib, sin dependencias)."""

    def __init__(self, iterations: int) -> None:
        self._iterations = iterations

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(_SALT_BYTES)
        digest = self._derive(password, salt, self._iterations)
        return "$".join(
            (
                _ALGORITHM,
                str(self._iterations),
                base64.b64encode(salt).decode("ascii"),
                base64.b64encode(digest).decode("ascii"),
            )
        )

    def verify(self, password: str, encoded: str) -> bool:
        parsed = self._parse(encoded)
        if parsed is None:
            return False
        iterations, salt, expected = parsed
        candidate = self._derive(password, salt, iterations)
        return hmac.compare_digest(candidate, expected)

    @staticmethod
    def _derive(password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

    @staticmethod
    def _parse(encoded: str) -> tuple[int, bytes, bytes] | None:
        parts = encoded.split("$")
        if len(parts) != 4 or parts[0] != _ALGORITHM:
            return None
        try:
            iterations = int(parts[1])
            salt = base64.b64decode(parts[2], validate=True)
            digest = base64.b64decode(parts[3], validate=True)
        except (ValueError, TypeError):
            return None
        return iterations, salt, digest
