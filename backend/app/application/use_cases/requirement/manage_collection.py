from collections.abc import Sequence

from app.application.errors import CollectionItemNotFoundError
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement._common import (
    load_editable_working_version,
    save_version,
)
from app.domain.auth.audit import AuditAction, AuditEntry
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

_AUDIT_ACTION = AuditAction.COLLECTION_UPDATE


class _CollectionUseCase:
    """Base con repositorio y auditoria compartidos por las operaciones de coleccion."""

    def __init__(self, repository: RequirementRepository, audit: AuditRecorderPort) -> None:
        self._repository = repository
        self._audit = audit

    def _record(
        self,
        version: RequirementVersion,
        kind: CollectionKind,
        operation: str,
        actor: str,
        item_id: int | None = None,
    ) -> None:
        detail: dict[str, object] = {"coleccion": kind.value, "operacion": operation}
        if item_id is not None:
            detail["item_id"] = item_id
        self._audit.record(
            AuditEntry(
                entity="REQ_VERSION",
                entity_id=version.id,
                action=_AUDIT_ACTION,
                actor=actor,
                detail=detail,
            )
        )


class AddCollectionItem(_CollectionUseCase):
    """Agrega un elemento al final de la coleccion de la version de trabajo."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        *,
        principal: Principal,
        content: str,
        benefit_kind: BenefitKind | None = None,
    ) -> RequirementVersion:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        item = make_item(kind, content=content, order=0, benefit_kind=benefit_kind)
        updated = with_added(version, kind, item)
        saved = save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, kind, "alta", principal.user_id)
        return saved


class UpdateCollectionItem(_CollectionUseCase):
    """Actualiza el contenido de un elemento de la coleccion."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        item_id: int,
        *,
        principal: Principal,
        content: str,
    ) -> RequirementVersion:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        result = with_content_updated(version, kind, item_id, content)
        if result is None:
            raise CollectionItemNotFoundError()
        updated, _item = result
        saved = save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, kind, "edicion", principal.user_id, item_id)
        return saved


class DeleteCollectionItem(_CollectionUseCase):
    """Baja logica de un elemento de la coleccion (soft-delete)."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        item_id: int,
        *,
        principal: Principal,
    ) -> None:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        if item_by_id(version, kind, item_id) is None:
            raise CollectionItemNotFoundError()
        updated = with_deactivated(version, kind, item_id)
        save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, kind, "baja", principal.user_id, item_id)


class ReorderCollectionItems(_CollectionUseCase):
    """Reordena los elementos de la coleccion segun la lista de ids."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        kind: CollectionKind,
        ordered_ids: Sequence[int],
        *,
        principal: Principal,
    ) -> RequirementVersion:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        for item_id in ordered_ids:
            if item_by_id(version, kind, item_id) is None:
                raise CollectionItemNotFoundError()
        updated = with_reordered(version, kind, list(ordered_ids))
        saved = save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, kind, "reorden", principal.user_id)
        return saved
