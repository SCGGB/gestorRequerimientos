from abc import ABC, abstractmethod

from app.domain.health import DatabaseStatus


class DatabaseHealthPort(ABC):
    @abstractmethod
    def check(self) -> DatabaseStatus:
        """Devuelve el estado de la base de datos."""
        raise NotImplementedError
