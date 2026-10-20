from dataclasses import dataclass, replace

from app.domain.auth.roles import Role


class UserLockedError(Exception):
    """El usuario alcanzo el maximo de intentos fallidos de acceso."""


class InactiveUserError(Exception):
    """El usuario esta dado de baja o desactivado."""


class SelfDeactivationError(Exception):
    """Un usuario no puede desactivarse a si mismo."""


@dataclass(frozen=True, slots=True)
class User:
    """Usuario local administrado por la aplicacion (ADR-003)."""

    username: str
    name: str
    password_hash: str
    roles: frozenset[Role] = frozenset()
    active: bool = True
    failed_attempts: int = 0
    id: int | None = None

    def is_locked(self, max_attempts: int) -> bool:
        return self.failed_attempts >= max_attempts

    def record_failed_attempt(self) -> "User":
        return replace(self, failed_attempts=self.failed_attempts + 1)

    def reset_failed_attempts(self) -> "User":
        return replace(self, failed_attempts=0)

    def ensure_active(self) -> None:
        if not self.active:
            raise InactiveUserError("El usuario esta inactivo.")

    def ensure_can_be_deactivated_by(self, actor_username: str) -> None:
        if self.username == actor_username:
            raise SelfDeactivationError(
                "Un usuario no puede desactivarse a si mismo."
            )
