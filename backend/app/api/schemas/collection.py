from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.requirement.enums import BenefitKind


class CollectionItemCreate(BaseModel):
    contenido: str = Field(min_length=1)
    orden: int | None = None


class BenefitCreate(CollectionItemCreate):
    tipo: BenefitKind


class CollectionItemUpdate(BaseModel):
    contenido: str = Field(min_length=1)


class ReorderRequest(BaseModel):
    ids: list[int] = Field(min_length=1)
