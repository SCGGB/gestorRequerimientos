from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from app.api.dependencies import (
    get_authenticate_use_case,
    get_current_principal,
    get_logout_use_case,
    get_session_ttl_seconds,
    get_session_use_case,
)
from app.api.openapi import INVALID_CREDENTIALS_RESPONSE, UNAUTHENTICATED_RESPONSE
from app.api.schemas.auth import LoginRequest, LoginResponse, SesionResponse
from app.application.ports.auth import Principal
from app.application.use_cases.auth.get_session import GetSession
from app.application.use_cases.auth.login import AuthenticateUser
from app.application.use_cases.auth.logout import LogoutUser

router = APIRouter(
    prefix="/api/v1",
    tags=["autenticacion"],
    responses={401: UNAUTHENTICATED_RESPONSE},
)


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    responses={401: INVALID_CREDENTIALS_RESPONSE},
)
def login(
    payload: LoginRequest,
    use_case: Annotated[AuthenticateUser, Depends(get_authenticate_use_case)],
    ttl_seconds: Annotated[int, Depends(get_session_ttl_seconds)],
) -> LoginResponse:
    token = use_case.execute(payload.usuario, payload.contrasena)
    return LoginResponse(
        token=token,
        tipo_token="Bearer",
        expira_en=ttl_seconds,
        usuario=payload.usuario,
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[LogoutUser, Depends(get_logout_use_case)],
) -> Response:
    use_case.execute(principal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/sesion", response_model=SesionResponse)
def get_sesion(
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[GetSession, Depends(get_session_use_case)],
) -> SesionResponse:
    user = use_case.execute(principal)
    return SesionResponse(
        id=user.id or 0,
        usuario=user.username,
        nombre=user.name,
        roles=sorted(user.roles),
        activo=bool(user.active),
    )
