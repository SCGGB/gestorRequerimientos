from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.domain.requirement.requirement import Requirement


class RequirementRepository(ABC):
    @abstractmethod
    def save(self, requirement: Requirement) -> Requirement:
        pass

    @abstractmethod
    def get(self, requirement_id: int) -> Requirement:
        pass

    @abstractmethod
    def get_by_folio(self, folio: int) -> Requirement | None:
        pass

    @abstractmethod
    def list(self) -> Sequence[Requirement]:
        pass
