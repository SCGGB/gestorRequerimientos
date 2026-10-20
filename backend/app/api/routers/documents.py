from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from app.api.dependencies import (
    get_current_principal,
    get_generate_documents_use_case,
    get_get_document_use_case,
    get_list_documents_use_case,
    require_action,
)
from app.api.schemas.document import (
    GeneratedDocumentResponse,
    GenerateDocumentsRequest,
)
from app.application.ports.auth import Principal
from app.application.use_cases.requirement.generate_documents import (
    GenerateRequirementDocuments,
)
from app.application.use_cases.requirement.get_document import GetRequirementDocument
from app.application.use_cases.requirement.list_documents import (
    ListRequirementDocuments,
)
from app.domain.auth.authorization import Action

router = APIRouter(
    prefix="/api/v1",
    tags=["documentos"],
    dependencies=[Depends(get_current_principal)],
)


@router.post(
    "/requerimientos/{requirement_id}/documentos",
    response_model=list[GeneratedDocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_documents(
    requirement_id: int,
    principal: Annotated[Principal, Depends(require_action(Action.GENERATE_DOCUMENTS))],
    use_case: Annotated[
        GenerateRequirementDocuments, Depends(get_generate_documents_use_case)
    ],
    payload: GenerateDocumentsRequest | None = None,
) -> list[GeneratedDocumentResponse]:
    documents = use_case.execute(
        requirement_id,
        version_id=payload.version_id if payload is not None else None,
        principal=principal,
    )
    return [GeneratedDocumentResponse.from_domain(document) for document in documents]


@router.get(
    "/requerimientos/{requirement_id}/documentos",
    response_model=list[GeneratedDocumentResponse],
)
def list_documents(
    requirement_id: int,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[
        ListRequirementDocuments, Depends(get_list_documents_use_case)
    ],
) -> list[GeneratedDocumentResponse]:
    return [
        GeneratedDocumentResponse.from_domain(document)
        for document in use_case.execute(requirement_id)
    ]


@router.get("/requerimientos/{requirement_id}/documentos/{document_id}/descarga")
def download_document(
    requirement_id: int,
    document_id: int,
    principal: Annotated[Principal, Depends(get_current_principal)],
    use_case: Annotated[GetRequirementDocument, Depends(get_get_document_use_case)],
) -> Response:
    document = use_case.execute(requirement_id, document_id, principal=principal)
    return Response(
        content=document.content or b"",
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.file_name}"',
        },
    )
