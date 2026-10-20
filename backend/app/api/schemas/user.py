from pydantic import BaseModel, Field


class UsuarioCreate(BaseModel):
    usuario: str
    nombre: str
    contrasena: str = Field(min_length=8)
    roles: list[str] = Field(default_factory=list)
    activo: bool = True


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    contrasena: str | None = Field(default=None, min_length=8)
    roles: list[str] | None = None
    activo: bool | None = None


class UsuarioResponse(BaseModel):
    id: int
    usuario: str
    nombre: str
    roles: list[str]
    activo: bool
    intentos_fallidos: int = 0
