from collections.abc import Sequence

from app.application.ports.user_repository import UserRepository
from app.domain.auth.user import User


class ListUsers:
    """Listado de usuarios para la pantalla ADMIN (sin auditoria, RF-12)."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def execute(self) -> Sequence[User]:
        return self._user_repository.list_all()
