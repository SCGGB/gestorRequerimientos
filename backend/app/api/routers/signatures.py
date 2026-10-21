from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_principal, get_register_signature_use_case
from app.api.openapi import FORBIDDEN_RESPONSE, UNAUTHENTICATED_RESPONSE
from app.api.schemas.requirement import SignatureCreate, SignatureResponse
from app.application.ports.auth import Principal
from app.application.use_cases.requirement.register_signature import RegisterSignature

router = APIRouter(
    prefix="/api/v1",
    tags=["firmas"],
    dependencies=[Depends(get_current_principal)],
    responses={401: UNAUTHENTICATED_RESPONSE, 403: FORBIDDEN_RESPONSE},
)


@router.post(
    "/requerimientos/{requirement_id}/versiones/{version_id}/firmas",
    response_model=SignatureResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_signature(
    requirement_id: int,
    version_id: int,
    payload: SignatureCreate,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[RegisterSignature, Depends(get_register_signature_use_case)],
) -> SignatureResponse:
    signature = use_case.execute(
        requirement_id,
        version_id,
        role=payload.rol,
        name=payload.nombre,
        position=payload.cargo,
        position_id=payload.cargo_id,
        principal=principal,
    )
    return SignatureResponse.from_domain(signature)
