from app.api.schemas.attachment import AttachmentCreate, AttachmentUpdate
from app.api.schemas.auth import LoginRequest, LoginResponse, SesionResponse
from app.api.schemas.catalog import ChangeTypeResponse, PositionResponse
from app.api.schemas.collection import (
    BenefitCreate,
    CollectionItemCreate,
    CollectionItemUpdate,
    ReorderRequest,
)
from app.api.schemas.document import (
    GeneratedDocumentResponse,
    GenerateDocumentsRequest,
)
from app.api.schemas.errors import ErrorDetail, ErrorResponse
from app.api.schemas.health import HealthResponse
from app.api.schemas.preview import (
    PreviewBlockResponse,
    PreviewDocumentResponse,
    PreviewFirmasResponse,
    PreviewSectionResponse,
    PreviewSignerResponse,
    PreviewVersionRowResponse,
)
from app.api.schemas.requirement import (
    AttachmentResponse,
    BenefitResponse,
    CollectionItemResponse,
    NewVersionRequest,
    RequirementCreate,
    RequirementPage,
    RequirementResponse,
    RequirementSummary,
    SignatureCreate,
    SignatureResponse,
    StatusChangeRequest,
    VersionResponse,
    VersionUpdate,
)
from app.api.schemas.user import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.api.schemas.validation import (
    StateTransitionRequest,
    StateTransitionResponse,
    ValidationErrorSchema,
    ValidationRequest,
    ValidationResultResponse,
)
from app.api.schemas.version import VersionResponse as AppVersionResponse

__all__ = [
    "AppVersionResponse",
    "AttachmentCreate",
    "AttachmentResponse",
    "AttachmentUpdate",
    "BenefitCreate",
    "BenefitResponse",
    "ChangeTypeResponse",
    "CollectionItemCreate",
    "CollectionItemResponse",
    "CollectionItemUpdate",
    "ErrorDetail",
    "ErrorResponse",
    "GenerateDocumentsRequest",
    "GeneratedDocumentResponse",
    "HealthResponse",
    "LoginRequest",
    "LoginResponse",
    "NewVersionRequest",
    "PositionResponse",
    "PreviewBlockResponse",
    "PreviewDocumentResponse",
    "PreviewFirmasResponse",
    "PreviewSectionResponse",
    "PreviewSignerResponse",
    "PreviewVersionRowResponse",
    "ReorderRequest",
    "RequirementCreate",
    "RequirementPage",
    "RequirementResponse",
    "RequirementSummary",
    "SesionResponse",
    "SignatureCreate",
    "SignatureResponse",
    "StateTransitionRequest",
    "StateTransitionResponse",
    "StatusChangeRequest",
    "UsuarioCreate",
    "UsuarioResponse",
    "UsuarioUpdate",
    "ValidationErrorSchema",
    "ValidationRequest",
    "ValidationResultResponse",
    "VersionResponse",
    "VersionUpdate",
]
