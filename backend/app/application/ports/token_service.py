from abc import ABC, abstractmethod

from app.domain.auth.session import Session


class TokenServicePort(ABC):
    @abstractmethod
    def issue(self, session: Session) -> str:
        pass

    @abstractmethod
    def parse(self, token: str) -> Session | None:
        pass
