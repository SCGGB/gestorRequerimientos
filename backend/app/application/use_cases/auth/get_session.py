from app.application.errors import NotAuthenticatedError, UserNotFoundError
from app.application.ports.auth import Principal
from app.application.ports.user_repository import UserRepository
from app.domain.auth.user import User


class GetSession:
    """Devuelve el perfil y roles actuales del usuario autenticado (RF-14)."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self, principal: Principal) -> User:
        user = self._user_repository.get_by_username(principal.user_id)
        if user is None:
            raise UserNotFoundError()
        if not user.active:
            raise NotAuthenticatedError()
        return user
