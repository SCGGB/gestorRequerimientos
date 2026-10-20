from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_create_user_use_case,
    get_current_principal,
    get_list_users_use_case,
    get_update_user_use_case,
    require_action,
)
from app.api.schemas.user import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.application.ports.auth import Principal
from app.application.use_cases.users.create_user import CreateUser
from app.application.use_cases.users.list_users import ListUsers
from app.application.use_cases.users.update_user import UpdateUser
from app.domain.auth.authorization import Action
from app.domain.auth.roles import Role

router = APIRouter(
    prefix="/api/v1",
    tags=["usuarios"],
    dependencies=[Depends(require_action(Action.MANAGE_USERS))],
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


@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
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
    from app.application.errors import UserNotFoundError

    raise UserNotFoundError()


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
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


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioResponse)
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
