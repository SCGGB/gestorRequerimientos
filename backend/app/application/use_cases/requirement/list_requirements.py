from collections.abc import Sequence
from dataclasses import dataclass

from app.application.ports.requirement_repository import (
    RequirementRepository,
    RequirementSearchFilters,
)
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.requirement import Requirement


@dataclass(frozen=True, slots=True)
class RequirementPage:
    items: Sequence[Requirement]
    total: int
    page: int
    size: int


class ListRequirements:
    """Listado filtrado y paginado de requerimientos."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        status: RequirementStatus | None = None,
        folio: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> RequirementPage:
        filters = RequirementSearchFilters(status=status, folio=folio)
        offset = (page - 1) * size
        items, total = self._repository.search(filters, offset=offset, limit=size)
        return RequirementPage(items=items, total=total, page=page, size=size)
