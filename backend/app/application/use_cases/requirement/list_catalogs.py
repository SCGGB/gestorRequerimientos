from collections.abc import Sequence

from app.application.ports.catalog_repository import ChangeTypeCatalog, PositionCatalog
from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.enums import SignatureRole


class ListChangeTypes:
    """Tipos de cambio activos."""

    def __init__(self, catalog: ChangeTypeCatalog) -> None:
        self._catalog = catalog

    def execute(self) -> Sequence[ChangeType]:
        return self._catalog.list_active()


class ListPositions:
    """Cargos activos, filtrados por rol cuando se informa."""

    def __init__(self, catalog: PositionCatalog) -> None:
        self._catalog = catalog

    def execute(self, role: SignatureRole | None = None) -> Sequence[Position]:
        if role is None:
            return self._catalog.list_active()
        return self._catalog.list_by_role(role)
