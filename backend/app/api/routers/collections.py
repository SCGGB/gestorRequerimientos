from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_add_collection_item_use_case,
    get_current_principal,
    get_delete_collection_item_use_case,
    get_reorder_collection_items_use_case,
    get_update_collection_item_use_case,
    require_action,
)
from app.api.openapi import FORBIDDEN_RESPONSE, UNAUTHENTICATED_RESPONSE
from app.api.schemas.collection import (
    BenefitCreate,
    CollectionItemCreate,
    CollectionItemUpdate,
    ReorderRequest,
)
from app.api.schemas.requirement import (
    VersionResponse,
)
from app.application.ports.auth import Principal
from app.application.use_cases.requirement.manage_collection import (
    AddCollectionItem,
    DeleteCollectionItem,
    ReorderCollectionItems,
    UpdateCollectionItem,
)
from app.domain.auth.authorization import Action
from app.domain.requirement.collections import CollectionKind

router = APIRouter(
    prefix="/api/v1",
    tags=["colecciones"],
    dependencies=[Depends(get_current_principal)],
    responses={401: UNAUTHENTICATED_RESPONSE, 403: FORBIDDEN_RESPONSE},
)

_RESOURCE_TO_KIND: dict[str, CollectionKind] = {
    "objetivos": CollectionKind.OBJETIVOS,
    "consideraciones": CollectionKind.CONSIDERACIONES,
    "beneficios": CollectionKind.BENEFICIOS,
    "restricciones": CollectionKind.RESTRICCIONES,
    "volumetria": CollectionKind.VOLUMETRIA,
    "riesgos": CollectionKind.RIESGOS,
    "requisitos-futuros": CollectionKind.REQUISITOS_FUTUROS,
}


def _to_kind(c: str) -> CollectionKind:
    try:
        return _RESOURCE_TO_KIND[c]
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"Recurso de coleccion desconocido: {c}") from exc


@router.post(
    "/requerimientos/{requirement_id}/versiones/{version_id}/{coleccion}",
    response_model=VersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_item(
    requirement_id: int,
    version_id: int,
    coleccion: Literal[
        "objetivos",
        "consideraciones",
        "beneficios",
        "restricciones",
        "volumetria",
        "riesgos",
        "requisitos-futuros",
    ],
    payload: CollectionItemCreate | BenefitCreate,
    principal: Annotated[Principal, Depends(require_action(Action.REQUIREMENT_WRITE))],
    use_case: Annotated[AddCollectionItem, Depends(get_add_collection_item_use_case)],
) -> VersionResponse:
    kind = _to_kind(coleccion)
    benefit_kind = None
    if isinstance(payload, BenefitCreate):
        benefit_kind = payload.tipo
    version_updated = use_case.execute(
        requirement_id,
        version_id,
        kind,
        principal=principal,
        content=payload.contenido,
        benefit_kind=benefit_kind,
    )
    return VersionResponse.from_domain(version_updated)


@router.patch(
    "/requerimientos/{requirement_id}/versiones/{version_id}/{coleccion}/{item_id}",
    response_model=VersionResponse,
)
def update_item(
    requirement_id: int,
    version_id: int,
    coleccion: Literal[
        "objetivos",
        "consideraciones",
        "beneficios",
        "restricciones",
        "volumetria",
        "riesgos",
        "requisitos-futuros",
    ],
    item_id: int,
    payload: CollectionItemUpdate,
    principal: Annotated[Principal, Depends(require_action(Action.REQUIREMENT_WRITE))],
    use_case: Annotated[
        UpdateCollectionItem, Depends(get_update_collection_item_use_case)
    ],
) -> VersionResponse:
    kind = _to_kind(coleccion)
    version_updated = use_case.execute(
        requirement_id,
        version_id,
        kind,
        item_id,
        principal=principal,
        content=payload.contenido,
    )
    return VersionResponse.from_domain(version_updated)


@router.delete(
    "/requerimientos/{requirement_id}/versiones/{version_id}/{coleccion}/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    requirement_id: int,
    version_id: int,
    coleccion: Literal[
        "objetivos",
        "consideraciones",
        "beneficios",
        "restricciones",
        "volumetria",
        "riesgos",
        "requisitos-futuros",
    ],
    item_id: int,
    principal: Annotated[Principal, Depends(require_action(Action.REQUIREMENT_WRITE))],
    use_case: Annotated[
        DeleteCollectionItem, Depends(get_delete_collection_item_use_case)
    ],
) -> None:
    kind = _to_kind(coleccion)
    use_case.execute(
        requirement_id, version_id, kind, item_id, principal=principal
    )


@router.put(
    "/requerimientos/{requirement_id}/versiones/{version_id}/{coleccion}/orden",
    response_model=VersionResponse,
)
def reorder_items(
    requirement_id: int,
    version_id: int,
    coleccion: Literal[
        "objetivos",
        "consideraciones",
        "beneficios",
        "restricciones",
        "volumetria",
        "riesgos",
        "requisitos-futuros",
    ],
    payload: ReorderRequest,
    principal: Annotated[Principal, Depends(require_action(Action.REQUIREMENT_WRITE))],
    use_case: Annotated[
        ReorderCollectionItems, Depends(get_reorder_collection_items_use_case)
    ],
) -> VersionResponse:
    kind = _to_kind(coleccion)
    version_updated = use_case.execute(
        requirement_id, version_id, kind, ordered_ids=payload.ids, principal=principal
    )
    return VersionResponse.from_domain(version_updated)
