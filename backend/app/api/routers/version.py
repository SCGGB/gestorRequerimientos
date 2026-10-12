from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_get_version_use_case
from app.api.schemas.version import VersionResponse
from app.application.use_cases.get_version import GetVersionUseCase

router = APIRouter(tags=["version"])


@router.get("/version", response_model=VersionResponse)
def get_version(
    use_case: Annotated[GetVersionUseCase, Depends(get_get_version_use_case)],
) -> VersionResponse:
    return VersionResponse(version=use_case.execute())
