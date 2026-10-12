from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_check_health_use_case
from app.api.schemas.health import HealthResponse
from app.application.use_cases.check_health import CheckHealthUseCase

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(
    use_case: Annotated[CheckHealthUseCase, Depends(get_check_health_use_case)],
) -> HealthResponse:
    report = use_case.execute()
    return HealthResponse(status=report.app.value, database=report.database.value)
