from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_add_attachment_use_case,
    get_delete_attachment_use_case,
    get_reorder_attachments_use_case,
    get_update_attachment_use_case,
)
from app.api.schemas.attachment import AttachmentCreate, AttachmentUpdate
from app.api.schemas.collection import ReorderRequest
from app.api.schemas.requirement import AttachmentResponse
from app.application.use_cases.requirement.manage_attachment import (
    AddAttachment,
    DeleteAttachment,
    ReorderAttachments,
    UpdateAttachment,
)
from app.domain.requirement.attachment import Attachment

router = APIRouter(prefix="/api/v1", tags=["anexos"])


@router.post(
    "/requerimientos/{requirement_id}/versiones/{version_id}/anexos",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_attachment(
    requirement_id: int,
    version_id: int,
    payload: AttachmentCreate,
    use_case: Annotated[AddAttachment, Depends(get_add_attachment_use_case)],
) -> AttachmentResponse:
    attachment = use_case.execute(
        requirement_id,
        version_id,
        name=payload.nombre,
        storage_key=payload.storage_key,
        mime_type=payload.tipo_mime,
        caption=payload.leyenda,
    )
    return AttachmentResponse.from_domain(attachment)


@router.patch(
    "/requerimientos/{requirement_id}/versiones/{version_id}/anexos/{attachment_id}",
    response_model=AttachmentResponse,
)
def update_attachment(
    requirement_id: int,
    version_id: int,
    attachment_id: int,
    payload: AttachmentUpdate,
    use_case: Annotated[UpdateAttachment, Depends(get_update_attachment_use_case)],
) -> AttachmentResponse:
    attachment = use_case.execute(
        requirement_id,
        version_id,
        attachment_id,
        name=payload.nombre,
        storage_key=payload.storage_key,
        mime_type=payload.tipo_mime,
        caption=payload.leyenda,
    )
    return AttachmentResponse.from_domain(attachment)


@router.delete(
    "/requerimientos/{requirement_id}/versiones/{version_id}/anexos/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attachment(
    requirement_id: int,
    version_id: int,
    attachment_id: int,
    use_case: Annotated[DeleteAttachment, Depends(get_delete_attachment_use_case)],
) -> None:
    use_case.execute(requirement_id, version_id, attachment_id)


@router.put(
    "/requerimientos/{requirement_id}/versiones/{version_id}/anexos/orden",
    response_model=list[AttachmentResponse],
)
def reorder_attachments(
    requirement_id: int,
    version_id: int,
    payload: ReorderRequest,
    use_case: Annotated[ReorderAttachments, Depends(get_reorder_attachments_use_case)],
) -> list[AttachmentResponse]:
    attachments: Sequence[Attachment] = use_case.execute(
        requirement_id, version_id, ordered_ids=payload.ids
    )
    return [AttachmentResponse.from_domain(item) for item in attachments]
