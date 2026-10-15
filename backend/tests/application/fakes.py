from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from itertools import count
from typing import Any, TypeVar

from app.application.errors import DuplicateFolioError, RequirementNotFoundError
from app.application.ports.catalog_repository import ChangeTypeCatalog, PositionCatalog
from app.application.ports.requirement_repository import (
    RequirementRepository,
    RequirementSearchFilters,
)
from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.enums import SignatureRole
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion

ItemT = TypeVar("ItemT")


class InMemoryRequirementRepository(RequirementRepository):
    """Repositorio en memoria con ids estables (sin base de datos)."""

    def __init__(self) -> None:
        self._requirements: dict[int, Requirement] = {}
        self._ids = count(1)

    def save(self, requirement: Requirement) -> Requirement:
        # Check for duplicate folio before assigning/overwriting
        target_folio = requirement.folio
        for existing in self._requirements.values():
            if existing.folio == target_folio and (
                requirement.id is None or existing.id != requirement.id
            ):
                raise DuplicateFolioError()
        assigned = self._assign_requirement(requirement)
        if assigned.id is None:
            raise RuntimeError("El requerimiento debe tener id tras guardar.")
        self._requirements[assigned.id] = assigned
        return assigned

    def get(self, requirement_id: int) -> Requirement:
        try:
            return self._requirements[requirement_id]
        except KeyError:
            raise RequirementNotFoundError() from None

    def get_by_folio(self, folio: int) -> Requirement | None:
        for requirement in self._requirements.values():
            if requirement.folio == folio:
                return requirement
        return None

    def list(self) -> Sequence[Requirement]:
        return tuple(
            self._requirements[requirement_id]
            for requirement_id in sorted(self._requirements)
        )

    def search(
        self,
        filters: RequirementSearchFilters,
        *,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Requirement], int]:
        items = [
            requirement
            for requirement in self.list()
            if (filters.status is None or requirement.status is filters.status)
            and (filters.folio is None or requirement.folio == filters.folio)
        ]
        return tuple(items[offset : offset + limit]), len(items)

    def _assign_requirement(self, requirement: Requirement) -> Requirement:
        requirement_id = requirement.id
        if requirement_id is None:
            requirement_id = next(self._ids)
        versions = tuple(
            self._assign_version(version, requirement_id)
            for version in requirement.versions
        )
        return replace(requirement, id=requirement_id, versions=versions)

    def _assign_version(
        self, version: RequirementVersion, requirement_id: int
    ) -> RequirementVersion:
        version_id = version.id
        if version_id is None:
            version_id = next(self._ids)
        return replace(
            version,
            id=version_id,
            requirement_id=requirement_id,
            objectives=self._assign_ids(version.objectives),
            considerations=self._assign_ids(version.considerations),
            benefits=self._assign_ids(version.benefits),
            restrictions=self._assign_ids(version.restrictions),
            volumetry=self._assign_ids(version.volumetry),
            risks=self._assign_ids(version.risks),
            future_requirements_items=self._assign_ids(
                version.future_requirements_items
            ),
            signatures=self._assign_ids(version.signatures),
            attachments=self._assign_ids(version.attachments),
        )

    def _assign_ids(self, items: Sequence[ItemT]) -> tuple[Any, ...]:
        return tuple(
            replace(item, id=next(self._ids))  # type: ignore[call-overload]
            if getattr(item, "id", None) is None
            else item
            for item in items
        )


class FakeChangeTypeCatalog(ChangeTypeCatalog):
    def __init__(self, change_types: Sequence[ChangeType]) -> None:
        self._change_types = tuple(change_types)

    def list_active(self) -> Sequence[ChangeType]:
        return tuple(change_type for change_type in self._change_types if change_type.active)

    def get(self, change_type_id: int) -> ChangeType | None:
        for change_type in self._change_types:
            if change_type.id == change_type_id:
                return change_type
        return None


class FakePositionCatalog(PositionCatalog):
    def __init__(self, positions: Sequence[Position]) -> None:
        self._positions = tuple(positions)

    def list_by_role(self, role: SignatureRole) -> Sequence[Position]:
        return tuple(
            position
            for position in self._positions
            if position.role == role and position.active
        )

    def list_active(self) -> Sequence[Position]:
        return tuple(position for position in self._positions if position.active)

    def get(self, position_id: int) -> Position | None:
        for position in self._positions:
            if position.id == position_id:
                return position
        return None
