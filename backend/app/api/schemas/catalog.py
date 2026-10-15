from __future__ import annotations

from pydantic import BaseModel

from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.enums import SignatureRole


class ChangeTypeResponse(BaseModel):
    id: int | None = None
    codigo: str
    nombre: str
    activo: bool

    @classmethod
    def from_domain(cls, change_type: ChangeType) -> ChangeTypeResponse:
        return cls(
            id=change_type.id,
            codigo=change_type.code,
            nombre=change_type.name,
            activo=change_type.active,
        )


class PositionResponse(BaseModel):
    id: int | None = None
    rol: SignatureRole
    nombre: str
    predeterminado: bool
    activo: bool

    @classmethod
    def from_domain(cls, position: Position) -> PositionResponse:
        return cls(
            id=position.id,
            rol=position.role,
            nombre=position.name,
            predeterminado=position.is_default,
            activo=position.active,
        )
