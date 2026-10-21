from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_create_user_use_case,
    get_current_principal,
    get_list_users_use_case,
    get_update_user_use_case,
    require_action,
)
from app.api.openapi import (
    FORBIDDEN_RESPONSE,
    UNAUTHENTICATED_RESPONSE,
    conflict_response,
    not_found_response,
)
from app.api.schemas.user import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.application.errors import UserNotFoundError
from app.application.ports.auth import Principal
from app.application.use_cases.users.create_user import CreateUser
from app.application.use_cases.users.list_users import ListUsers
from app.application.use_cases.users.update_user import UpdateUser
from app.domain.auth.authorization import Action
from app.domain.auth.roles import Role

USER_NOT_FOUND = not_found_response("user_not_found", "El usuario no existe.")
USERNAME_TAKEN = conflict_response("username_taken", "El nombre de usuario ya existe.")
SELF_DEACTIVATION = conflict_response(
    "self_deactivation_not_allowed",
    "Un usuario no puede desactivarse a si mismo.",
)

router = APIRouter(
    prefix="/api/v1",
    tags=["usuarios"],
    dependencies=[Depends(require_action(Action.MANAGE_USERS))],
    responses={401: UNAUTHENTICATED_RESPONSE, 403: FORBIDDEN_RESPONSE},
)


@router.get("/usuarios", response_model=list[UsuarioResponse])
def list_users(
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[ListUsers, Depends(get_list_users_use_case)],
) -> list[UsuarioResponse]:
    users = use_case.execute()
    return [
        UsuarioResponse(
            id=u.id or 0,
            usuario=u.username,
            nombre=u.name,
            roles=sorted(u.roles),
            activo=bool(u.active),
            intentos_fallidos=u.failed_attempts,
        )
        for u in users
    ]


@router.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioResponse,
    responses={404: USER_NOT_FOUND},
)
def get_user(
    usuario_id: int,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[ListUsers, Depends(get_list_users_use_case)],
) -> UsuarioResponse:
    users = use_case.execute()
    for u in users:
        if u.id == usuario_id:
            return UsuarioResponse(
                id=u.id or 0,
                usuario=u.username,
                nombre=u.name,
                roles=sorted(u.roles),
                activo=bool(u.active),
                intentos_fallidos=u.failed_attempts,
            )
    raise UserNotFoundError()


@router.post(
    "/usuarios",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: USERNAME_TAKEN},
)
def create_user(
    payload: UsuarioCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[CreateUser, Depends(get_create_user_use_case)],
) -> UsuarioResponse:
    user = use_case.execute(
        principal,
        usuario=payload.usuario,
        nombre=payload.nombre,
        contrasena=payload.contrasena,
        roles=frozenset(Role(value) for value in payload.roles),
        activo=payload.activo,
    )
    return UsuarioResponse(
        id=user.id or 0,
        usuario=user.username,
        nombre=user.name,
        roles=sorted(user.roles),
        activo=bool(user.active),
        intentos_fallidos=user.failed_attempts,
    )


@router.patch(
    "/usuarios/{usuario_id}",
    response_model=UsuarioResponse,
    responses={404: USER_NOT_FOUND, 409: SELF_DEACTIVATION},
)
def update_user(
    usuario_id: int,
    payload: UsuarioUpdate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[UpdateUser, Depends(get_update_user_use_case)],
) -> UsuarioResponse:
    user = use_case.execute(
        principal,
        user_id=usuario_id,
        nombre=payload.nombre,
        contrasena=payload.contrasena,
        roles=(
            frozenset(Role(value) for value in payload.roles)
            if payload.roles is not None
            else None
        ),
        activo=payload.activo,
    )
    return UsuarioResponse(
        id=user.id or 0,
        usuario=user.username,
        nombre=user.name,
        roles=sorted(user.roles),
        activo=bool(user.active),
        intentos_fallidos=user.failed_attempts,
    )
