from collections.abc import Sequence

from app.application.errors import CollectionItemNotFoundError
from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement._common import (
    load_editable_working_version,
    save_version,
)
from app.domain.requirement.collections import (
    CollectionKind,
    item_by_id,
    make_item,
    with_added,
    with_content_updated,
    with_deactivated,
    with_reordered,
)
from app.domain.requirement.enums import BenefitKind
from app.domain.requirement.version import RequirementVersion


class AddCollectionItem:
    """Agrega un elemento al final de la coleccion de la version de trabajo."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        *,
        content: str,
        benefit_kind: BenefitKind | None = None,
    ) -> RequirementVersion:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        item = make_item(kind, content=content, order=0, benefit_kind=benefit_kind)
        updated = with_added(version, kind, item)
        return save_version(self._repository, requirement, version, updated)


class UpdateCollectionItem:
    """Actualiza el contenido de un elemento de la coleccion."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        item_id: int,
        *,
        content: str,
    ) -> RequirementVersion:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        result = with_content_updated(version, kind, item_id, content)
        if result is None:
            raise CollectionItemNotFoundError()
        updated, _item = result
        return save_version(self._repository, requirement, version, updated)


class DeleteCollectionItem:
    """Baja logica de un elemento de la coleccion (soft-delete)."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        item_id: int,
    ) -> None:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        if item_by_id(version, kind, item_id) is None:
            raise CollectionItemNotFoundError()
        updated = with_deactivated(version, kind, item_id)
        save_version(self._repository, requirement, version, updated)


class ReorderCollectionItems:
    """Reordena los elementos de la coleccion segun la lista de ids."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        ordered_ids: Sequence[int],
    ) -> RequirementVersion:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        for item_id in ordered_ids:
            if item_by_id(version, kind, item_id) is None:
                raise CollectionItemNotFoundError()
        updated = with_reordered(version, kind, list(ordered_ids))
        return save_version(self._repository, requirement, version, updated)
