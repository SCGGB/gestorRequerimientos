from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_current_principal,
    get_list_change_types_use_case,
    get_list_positions_use_case,
)
from app.api.openapi import UNAUTHENTICATED_RESPONSE
from app.api.schemas.catalog import ChangeTypeResponse, PositionResponse
from app.application.use_cases.requirement.list_catalogs import (
    ListChangeTypes,
    ListPositions,
)
from app.domain.requirement.enums import SignatureRole

router = APIRouter(
    prefix="/api/v1",
    tags=["catalogos"],
    dependencies=[Depends(get_current_principal)],
    responses={401: UNAUTHENTICATED_RESPONSE},
)


@router.get("/catalogos/tipos-cambio", response_model=list[ChangeTypeResponse])
def list_change_types(
    use_case: Annotated[ListChangeTypes, Depends(get_list_change_types_use_case)],
) -> list[ChangeTypeResponse]:
    return [
        ChangeTypeResponse.from_domain(change_type)
        for change_type in use_case.execute()
    ]


@router.get("/catalogos/cargos", response_model=list[PositionResponse])
def list_positions(
    use_case: Annotated[ListPositions, Depends(get_list_positions_use_case)],
    rol: Annotated[SignatureRole | None, Query(alias="rol")] = None,
) -> list[PositionResponse]:
    return [PositionResponse.from_domain(position) for position in use_case.execute(rol)]
