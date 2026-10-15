from dataclasses import replace
from enum import StrEnum
from typing import Any, TypeVar, cast

from app.domain.requirement.enums import BenefitKind
from app.domain.requirement.items import (
    Benefit,
    CollectionItem,
    Consideration,
    FutureRequirementItem,
    Objective,
    Restriction,
    Risk,
    Volumetry,
)
from app.domain.requirement.version import RequirementVersion

ItemT = TypeVar("ItemT", bound=CollectionItem)


class CollectionKind(StrEnum):
    """Colecciones ordenadas de una version (nombres de recurso de la API)."""

    OBJETIVOS = "OBJETIVOS"
    CONSIDERACIONES = "CONSIDERACIONES"
    BENEFICIOS = "BENEFICIOS"
    RESTRICCIONES = "RESTRICCIONES"
    VOLUMETRIA = "VOLUMETRIA"
    RIESGOS = "RIESGOS"
    REQUISITOS_FUTUROS = "REQUISITOS_FUTUROS"


_ATTRIBUTE: dict[CollectionKind, str] = {
    CollectionKind.OBJETIVOS: "objectives",
    CollectionKind.CONSIDERACIONES: "considerations",
    CollectionKind.BENEFICIOS: "benefits",
    CollectionKind.RESTRICCIONES: "restrictions",
    CollectionKind.VOLUMETRIA: "volumetry",
    CollectionKind.RIESGOS: "risks",
    CollectionKind.REQUISITOS_FUTUROS: "future_requirements_items",
}

_ITEM_TYPE: dict[CollectionKind, type[CollectionItem]] = {
    CollectionKind.OBJETIVOS: Objective,
    CollectionKind.CONSIDERACIONES: Consideration,
    CollectionKind.BENEFICIOS: Benefit,
    CollectionKind.RESTRICCIONES: Restriction,
    CollectionKind.VOLUMETRIA: Volumetry,
    CollectionKind.RIESGOS: Risk,
    CollectionKind.REQUISITOS_FUTUROS: FutureRequirementItem,
}


def make_item(
    kind: CollectionKind,
    *,
    content: str,
    order: int,
    benefit_kind: BenefitKind | None = None,
) -> CollectionItem:
    """Crea el tipo de elemento correcto para la coleccion (Benefit exige kind)."""
    item_type = _ITEM_TYPE[kind]
    if item_type is Benefit:
        if benefit_kind is None:
            raise ValueError("Los beneficios requieren un BenefitKind.")
        return Benefit(content=content, order=order, kind=benefit_kind)
    return item_type(content=content, order=order)


def items_of(
    version: RequirementVersion, kind: CollectionKind
) -> tuple[CollectionItem, ...]:
    """Accesor uniforme a los elementos de la coleccion (incluye inactivos)."""
    items = getattr(version, _ATTRIBUTE[kind])
    return cast("tuple[CollectionItem, ...]", items)


def item_by_id(
    version: RequirementVersion, kind: CollectionKind, item_id: int
) -> CollectionItem | None:
    """Devuelve el elemento con ese id (activo o no), o ``None``."""
    for item in items_of(version, kind):
        if item.id == item_id:
            return item
    return None


def with_added(
    version: RequirementVersion, kind: CollectionKind, item: CollectionItem
) -> RequirementVersion:
    """Agrega un elemento con el siguiente orden incremental."""
    existing = items_of(version, kind)
    next_order = max((current.order for current in existing), default=0) + 1
    added = replace(item, order=next_order)
    return _set(version, kind, (*existing, added))


def with_content_updated(
    version: RequirementVersion, kind: CollectionKind, item_id: int, content: str
) -> tuple[RequirementVersion, CollectionItem] | None:
    """Actualiza el contenido de un elemento; ``None`` si el id no existe."""
    updated: CollectionItem | None = None
    result: list[CollectionItem] = []
    for item in items_of(version, kind):
        if item.id == item_id:
            updated = replace(item, content=content)
            result.append(updated)
        else:
            result.append(item)
    if updated is None:
        return None
    return _set(version, kind, tuple(result)), updated


def with_deactivated(
    version: RequirementVersion, kind: CollectionKind, item_id: int
) -> RequirementVersion:
    """Baja logica: marca ``active=False`` sin quitarlo de la tupla."""
    deactivated = tuple(
        replace(item, active=False) if item.id == item_id else item
        for item in items_of(version, kind)
    )
    return _set(version, kind, deactivated)


def with_reordered(
    version: RequirementVersion,
    kind: CollectionKind,
    ordered_ids: list[int],
) -> RequirementVersion:
    """Renumera por la lista de ids; no listados quedan despues, con orden unico.

    Los ids desconocidos se ignoran (el caso de uso valida existencia antes).
    """
    items = items_of(version, kind)
    by_id = {item.id: item for item in items if item.id is not None}

    leading: list[CollectionItem] = []
    seen: set[int] = set()
    for item_id in ordered_ids:
        item = by_id.get(item_id)
        if item is not None and item_id not in seen:
            leading.append(item)
            seen.add(item_id)

    active_rest = [
        item for item in items if item.active and item.id not in seen
    ]
    inactive = [item for item in items if not item.active]
    sequence = (*leading, *active_rest, *inactive)
    renumbered = tuple(
        replace(item, order=order) for order, item in enumerate(sequence, start=1)
    )
    return _set(version, kind, renumbered)


def _set(
    version: RequirementVersion,
    kind: CollectionKind,
    items: tuple[CollectionItem, ...],
) -> RequirementVersion:
    changes: dict[str, Any] = {_ATTRIBUTE[kind]: items}
    return replace(version, **changes)
