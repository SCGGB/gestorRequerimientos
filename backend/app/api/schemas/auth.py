from pydantic import BaseModel


class LoginRequest(BaseModel):
    usuario: str
    contrasena: str


class LoginResponse(BaseModel):
    token: str
    tipo_token: str = "Bearer"
    expira_en: int
    usuario: str


class SesionResponse(BaseModel):
    id: int
    usuario: str
    nombre: str
    roles: list[str]
    activo: bool
