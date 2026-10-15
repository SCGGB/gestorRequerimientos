from __future__ import annotations

from pydantic import BaseModel, Field


class AttachmentCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=300)
    tipo_mime: str | None = Field(default=None, max_length=150)
    orden: int | None = None
    leyenda: str | None = None
    storage_key: str = Field(min_length=1, max_length=512)


class AttachmentUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=300)
    tipo_mime: str | None = Field(default=None, max_length=150)
    leyenda: str | None = None
    storage_key: str | None = Field(default=None, min_length=1, max_length=512)
