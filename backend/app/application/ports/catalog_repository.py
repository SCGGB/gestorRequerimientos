from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.enums import SignatureRole


class ChangeTypeCatalog(ABC):
    @abstractmethod
    def list_active(self) -> Sequence[ChangeType]:
        pass

    @abstractmethod
    def get(self, change_type_id: int) -> ChangeType | None:
        pass


class PositionCatalog(ABC):
    @abstractmethod
    def list_by_role(self, role: SignatureRole) -> Sequence[Position]:
        pass

    @abstractmethod
    def get(self, position_id: int) -> Position | None:
        pass
