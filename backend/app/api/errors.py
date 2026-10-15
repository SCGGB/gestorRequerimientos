from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.errors import ErrorDetail, ErrorResponse
from app.application.errors import (
    ApplicationError,
    AttachmentNotFoundError,
    CollectionItemNotFoundError,
    DataConflictError,
    DuplicateFolioError,
    RequirementNotFoundError,
    VersionNotFoundError,
)
from app.domain.requirement.errors import (
    AuthorizationNotOnCurrentVersionError,
    DomainError,
    InvalidFolioError,
    InvalidStateTransitionError,
    MultipleWorkingVersionsError,
    RequirementNotEditableError,
    SignatureNotAllowedError,
)


def _code_for_request_validation(_exc: RequestValidationError) -> str:
    return "validation_error"


def _map_domain(exc: DomainError) -> tuple[str, int, str | None]:
    if isinstance(exc, InvalidStateTransitionError):
        return "invalid_state_transition", status.HTTP_409_CONFLICT, None
    if isinstance(exc, AuthorizationNotOnCurrentVersionError):
        return "authorization_not_on_current_version", status.HTTP_409_CONFLICT, None
    if isinstance(exc, MultipleWorkingVersionsError):
        return "multiple_working_versions", status.HTTP_409_CONFLICT, None
    if isinstance(exc, RequirementNotEditableError):
        return "not_editable", status.HTTP_409_CONFLICT, None
    if isinstance(exc, SignatureNotAllowedError):
        return "signature_not_allowed", status.HTTP_409_CONFLICT, None
    if isinstance(exc, InvalidFolioError):
        return "invalid_folio", status.HTTP_422_UNPROCESSABLE_ENTITY, None
    return "domain_error", status.HTTP_409_CONFLICT, None


def _map_application(exc: ApplicationError) -> tuple[str, int, str | None]:
    if isinstance(exc, DuplicateFolioError):
        return "duplicate_folio", status.HTTP_409_CONFLICT, None
    if isinstance(exc, DataConflictError):
        return "data_conflict", status.HTTP_409_CONFLICT, None
    if isinstance(exc, RequirementNotFoundError):
        return "requirement_not_found", status.HTTP_404_NOT_FOUND, None
    if isinstance(exc, VersionNotFoundError):
        return "version_not_found", status.HTTP_404_NOT_FOUND, None
    if isinstance(exc, CollectionItemNotFoundError):
        return "collection_item_not_found", status.HTTP_404_NOT_FOUND, None
    if isinstance(exc, AttachmentNotFoundError):
        return "attachment_not_found", status.HTTP_404_NOT_FOUND, None
    return "application_error", status.HTTP_409_CONFLICT, None


def _map_http(exc: StarletteHTTPException) -> tuple[str, int]:
    return "http_error", exc.status_code


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain(request: Request, exc: DomainError) -> JSONResponse:
        code, http_status, details = _map_domain(exc)
        message = str(exc) or code
        return JSONResponse(
            status_code=http_status,
            content=ErrorResponse(
                error=ErrorDetail(code=code, message=message, details=details)
            ).model_dump(mode="json", exclude_none=True),
        )

    @app.exception_handler(ApplicationError)
    async def handle_application(request: Request, exc: ApplicationError) -> JSONResponse:
        code, http_status, details = _map_application(exc)
        message = str(exc) or code
        return JSONResponse(
            status_code=http_status,
            content=ErrorResponse(
                error=ErrorDetail(code=code, message=message, details=details)
            ).model_dump(mode="json", exclude_none=True),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        code = _code_for_request_validation(exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error=ErrorDetail(code=code, message=code, details=exc.errors())
            ).model_dump(mode="json"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, http_status = _map_http(exc)
        message = exc.detail if isinstance(exc.detail, str) else "http_error"
        details = exc.detail if not isinstance(exc.detail, str) else None
        return JSONResponse(
            status_code=http_status,
            content=ErrorResponse(
                error=ErrorDetail(code=code, message=message, details=details)
            ).model_dump(mode="json", exclude_none=True),
        )
