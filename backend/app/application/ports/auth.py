from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Principal:
    """Identidad autenticada; punto de extension de SPEC-008 (sin enforcement aqui)."""

    user_id: str
    roles: frozenset[str] = frozenset()


class AuthProvider(ABC):
    @abstractmethod
    def current_principal(self) -> Principal | None:
        pass
