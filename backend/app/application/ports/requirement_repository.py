from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.requirement import Requirement


@dataclass(frozen=True, slots=True)
class RequirementSearchFilters:
    status: RequirementStatus | None = None
    folio: int | None = None


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

    @abstractmethod
    def search(
        self,
        filters: RequirementSearchFilters,
        *,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Requirement], int]:
        pass
