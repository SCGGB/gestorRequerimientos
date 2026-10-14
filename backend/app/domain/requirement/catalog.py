from dataclasses import dataclass

from app.domain.requirement.enums import SignatureRole


@dataclass(frozen=True, slots=True)
class ChangeType:
    """Tipo de cambio del catalogo configurable."""

    code: str
    name: str
    active: bool = True
    id: int | None = None


@dataclass(frozen=True, slots=True)
class Position:
    """Cargo por rol del catalogo configurable."""

    role: SignatureRole
    name: str
    is_default: bool = False
    active: bool = True
    id: int | None = None
