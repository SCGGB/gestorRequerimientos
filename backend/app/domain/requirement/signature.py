from dataclasses import dataclass

from app.domain.requirement.enums import SignatureRole


@dataclass(frozen=True, slots=True)
class Signature:
    """Firma registrada sobre una version del requerimiento."""

    role: SignatureRole
    name: str
    position: str
    version_id: int | None = None
    position_id: int | None = None
    id: int | None = None
