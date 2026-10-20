from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.auth.user import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    def get(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    def list_all(self) -> Sequence[User]:
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        pass
