from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_build_preview_document_use_case,
    get_change_status_use_case,
    get_create_requirement_use_case,
    get_current_principal,
    get_freeze_and_advance_use_case,
    get_get_requirement_use_case,
    get_get_requirement_version_use_case,
    get_list_requirements_use_case,
    get_list_versions_use_case,
    get_update_version_use_case,
    require_action,
)
from app.api.schemas.preview import PreviewDocumentResponse
from app.api.schemas.requirement import (
    NewVersionRequest,
    RequirementCreate,
    RequirementPage,
    RequirementResponse,
    RequirementSummary,
    StatusChangeRequest,
    VersionResponse,
    VersionUpdate,
)
from app.application.errors import VersionNotFoundError
from app.application.ports.auth import Principal
from app.application.use_cases.requirement.build_preview_document import (
    BuildPreviewDocument,
)
from app.application.use_cases.requirement.change_status import ChangeStatus
from app.application.use_cases.requirement.create_requirement import CreateRequirement
from app.application.use_cases.requirement.freeze_version import FreezeAndAdvance
from app.application.use_cases.requirement.get_requirement import GetRequirement
from app.application.use_cases.requirement.list_requirements import ListRequirements
from app.application.use_cases.requirement.list_versions import GetVersion, ListVersions
from app.application.use_cases.requirement.update_version import UpdateVersion
from app.domain.auth.authorization import Action
from app.domain.requirement.enums import RequirementStatus

router = APIRouter(
    prefix="/api/v1",
    tags=["requerimientos"],
    dependencies=[Depends(get_current_principal)],
)


@router.post(
    "/requerimientos",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement(
    payload: RequirementCreate,
    principal: Annotated[Principal, Depends(require_action(Action.REQUIREMENT_WRITE))],
    use_case: Annotated[CreateRequirement, Depends(get_create_requirement_use_case)],
) -> RequirementResponse:
    requirement = use_case.execute(
        folio=payload.folio,
        title=payload.titulo,
        change_type_id=payload.tipo_cambio_id,
        system=payload.sistema,
        document_version=payload.version_documento,
        version_date=payload.fecha_version,
        principal=principal,
    )
    return RequirementResponse.from_domain(requirement)


@router.get("/requerimientos", response_model=RequirementPage)
def list_requirements(
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[ListRequirements, Depends(get_list_requirements_use_case)],
    estado: RequirementStatus | None = None,
    folio: int | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1)] = 20,
) -> RequirementPage:
    result = use_case.execute(status=estado, folio=folio, page=page, size=size)
    return RequirementPage(
        items=[RequirementSummary.from_domain(item) for item in result.items],
        total=result.total,
        page=result.page,
        size=result.size,
    )


@router.get("/requerimientos/{requirement_id}", response_model=RequirementResponse)
def get_requirement(
    requirement_id: int,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[GetRequirement, Depends(get_get_requirement_use_case)],
) -> RequirementResponse:
    return RequirementResponse.from_domain(use_case.execute(requirement_id))


@router.get(
    "/requerimientos/{requirement_id}/versiones",
    response_model=list[VersionResponse],
)
def list_versions(
    requirement_id: int,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[ListVersions, Depends(get_list_versions_use_case)],
) -> list[VersionResponse]:
    return [
        VersionResponse.from_domain(version) for version in use_case.execute(requirement_id)
    ]


@router.get(
    "/requerimientos/{requirement_id}/versiones/{version_id}",
    response_model=VersionResponse,
)
def get_version(
    requirement_id: int,
    version_id: int,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[GetVersion, Depends(get_get_requirement_version_use_case)],
) -> VersionResponse:
    return VersionResponse.from_domain(use_case.execute(requirement_id, version_id))


@router.get(
    "/requerimientos/{requirement_id}/versiones/{version_id}/vista-previa",
    response_model=PreviewDocumentResponse,
)
def get_version_preview(
    requirement_id: int,
    version_id: int,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[
        BuildPreviewDocument, Depends(get_build_preview_document_use_case)
    ],
) -> PreviewDocumentResponse:
    document = use_case.execute(requirement_id, version_id)
    return PreviewDocumentResponse.from_domain(document)


@router.patch(
    "/requerimientos/{requirement_id}/versiones/{version_id}",
    response_model=VersionResponse,
)
def update_version(
    requirement_id: int,
    version_id: int,
    payload: VersionUpdate,
    principal: Annotated[Principal, Depends(require_action(Action.REQUIREMENT_WRITE))],
    use_case: Annotated[UpdateVersion, Depends(get_update_version_use_case)],
) -> VersionResponse:
    requirement = use_case.execute(
        requirement_id, version_id, payload.to_edit(), principal=principal
    )
    version = requirement.version_by_id(version_id)
    if version is None:
        raise VersionNotFoundError()
    return VersionResponse.from_domain(version)


@router.post(
    "/requerimientos/{requirement_id}/versiones",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_version(
    requirement_id: int,
    payload: NewVersionRequest,
    principal: Annotated[Principal, Depends(require_action(Action.REQUIREMENT_WRITE))],
    use_case: Annotated[FreezeAndAdvance, Depends(get_freeze_and_advance_use_case)],
) -> RequirementResponse:
    requirement = use_case.execute(
        requirement_id,
        document_version=payload.version_documento,
        version_date=payload.fecha_version,
        title=payload.titulo,
        principal=principal,
    )
    return RequirementResponse.from_domain(requirement)


@router.post("/requerimientos/{requirement_id}/estado", response_model=RequirementResponse)
def change_status(
    requirement_id: int,
    payload: StatusChangeRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[ChangeStatus, Depends(get_change_status_use_case)],
) -> RequirementResponse:
    requirement = use_case.execute(requirement_id, payload.nuevo_estado, principal=principal)
    return RequirementResponse.from_domain(requirement)
