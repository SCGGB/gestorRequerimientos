from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    get_current_principal,
    get_transition_requirement_state_use_case,
    get_validate_requirement_version_use_case,
)
from app.api.schemas.validation import (
    StateTransitionRequest,
    StateTransitionResponse,
    ValidationRequest,
    ValidationResultResponse,
)
from app.application.ports.auth import Principal
from app.application.use_cases.requirement.transition_requirement_state import (
    TransitionRequirementState,
)
from app.application.use_cases.requirement.validate_requirement_version import (
    ValidateRequirementVersion,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["validacion"],
    dependencies=[Depends(get_current_principal)],
)


@router.post(
    "/requerimientos/{requirement_id}/versiones/{version_id}/validar",
    response_model=ValidationResultResponse,
)
def validate_version(
    requirement_id: int,
    version_id: int,
    use_case: Annotated[
        ValidateRequirementVersion,
        Depends(get_validate_requirement_version_use_case),
    ],
    payload: ValidationRequest | None = None,
) -> ValidationResultResponse:
    target_state = payload.a_estado if payload is not None else None
    result = use_case.execute(
        requirement_id,
        version_id,
        target_state=target_state,
    )
    return ValidationResultResponse.from_domain(result)


@router.post(
    "/requerimientos/{requirement_id}/transicionar",
    response_model=StateTransitionResponse,
)
def transition_state(
    requirement_id: int,
    payload: StateTransitionRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[
        TransitionRequirementState,
        Depends(get_transition_requirement_state_use_case),
    ],
    response: Response,
) -> StateTransitionResponse:
    outcome = use_case.execute(
        requirement_id,
        payload.a_estado,
        principal=principal,
        reason=payload.motivo,
    )
    if not outcome.is_valid:
        response.status_code = status.HTTP_400_BAD_REQUEST
    return StateTransitionResponse.from_outcome(outcome)
