from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_register_signature_use_case
from app.api.schemas.requirement import SignatureCreate, SignatureResponse
from app.application.use_cases.requirement.register_signature import RegisterSignature

router = APIRouter(prefix="/api/v1", tags=["firmas"])


@router.post(
    "/requerimientos/{requirement_id}/versiones/{version_id}/firmas",
    response_model=SignatureResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_signature(
    requirement_id: int,
    version_id: int,
    payload: SignatureCreate,
    use_case: Annotated[RegisterSignature, Depends(get_register_signature_use_case)],
) -> SignatureResponse:
    signature = use_case.execute(
        requirement_id,
        version_id,
        role=payload.rol,
        name=payload.nombre,
        position=payload.cargo,
        position_id=payload.cargo_id,
    )
    return SignatureResponse.from_domain(signature)
