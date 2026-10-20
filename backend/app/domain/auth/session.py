from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.auth.roles import Role

SESSION_TTL = timedelta(hours=8)


@dataclass(frozen=True, slots=True)
class Session:
    """Sesion autenticada: identidad, roles y expiracion (sin datos de negocio)."""

    user_id: str
    roles: frozenset[Role]
    issued_at: datetime
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at
