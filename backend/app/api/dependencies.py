from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.engine import Engine

from app.application.errors import NotAuthenticatedError
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import AuthProvider, Principal
from app.application.ports.catalog_repository import ChangeTypeCatalog, PositionCatalog
from app.application.ports.document_converter import DocumentConverterPort
from app.application.ports.document_renderer import DocumentRendererPort
from app.application.ports.password_hasher import PasswordHasherPort
from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.application.ports.requirement_repository import RequirementRepository
from app.application.ports.token_service import TokenServicePort
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.auth.get_session import GetSession
from app.application.use_cases.auth.login import AuthenticateUser
from app.application.use_cases.auth.logout import LogoutUser
from app.application.use_cases.check_health import CheckHealthUseCase
from app.application.use_cases.get_version import GetVersionUseCase
from app.application.use_cases.requirement.build_preview_document import (
    BuildPreviewDocument,
)
from app.application.use_cases.requirement.change_status import ChangeStatus
from app.application.use_cases.requirement.create_requirement import CreateRequirement
from app.application.use_cases.requirement.freeze_version import FreezeAndAdvance
from app.application.use_cases.requirement.generate_documents import (
    GenerateRequirementDocuments,
)
from app.application.use_cases.requirement.get_document import GetRequirementDocument
from app.application.use_cases.requirement.get_requirement import GetRequirement
from app.application.use_cases.requirement.list_catalogs import (
    ListChangeTypes,
    ListPositions,
)
from app.application.use_cases.requirement.list_documents import (
    ListRequirementDocuments,
)
from app.application.use_cases.requirement.list_requirements import ListRequirements
from app.application.use_cases.requirement.list_versions import GetVersion, ListVersions
from app.application.use_cases.requirement.manage_attachment import (
    AddAttachment,
    DeleteAttachment,
    ReorderAttachments,
    UpdateAttachment,
)
from app.application.use_cases.requirement.manage_collection import (
    AddCollectionItem,
    DeleteCollectionItem,
    ReorderCollectionItems,
    UpdateCollectionItem,
)
from app.application.use_cases.requirement.register_signature import RegisterSignature
from app.application.use_cases.requirement.transition_requirement_state import (
    TransitionRequirementState,
)
from app.application.use_cases.requirement.update_version import UpdateVersion
from app.application.use_cases.requirement.validate_requirement_version import (
    ValidateRequirementVersion,
)
from app.application.use_cases.users.create_user import CreateUser
from app.application.use_cases.users.list_users import ListUsers
from app.application.use_cases.users.update_user import UpdateUser
from app.domain.auth.authorization import Action, ensure_authorized
from app.domain.auth.roles import Role
from app.infrastructure.adapters.audit_repository import SqlAlchemyAuditRecorder
from app.infrastructure.adapters.catalogs import (
    SqlAlchemyChangeTypeCatalog,
    SqlAlchemyPositionCatalog,
)
from app.infrastructure.adapters.database_health import SqlAlchemyDatabaseHealthAdapter
from app.infrastructure.adapters.document_converter import (
    LibreofficeDocumentConverter,
)
from app.infrastructure.adapters.document_renderer import DocxtplDocumentRenderer
from app.infrastructure.adapters.jwt_token_service import JwtTokenService
from app.infrastructure.adapters.local_auth_provider import build_auth_provider
from app.infrastructure.adapters.password_hasher import Pbkdf2PasswordHasher
from app.infrastructure.adapters.requirement_document_repository import (
    SqlAlchemyRequirementDocumentRepository,
)
from app.infrastructure.adapters.requirement_repository import (
    SqlAlchemyRequirementRepository,
)
from app.infrastructure.adapters.user_repository import SqlAlchemyUserRepository
from app.infrastructure.config import get_settings
from app.infrastructure.database import create_db_engine


@lru_cache
def get_engine() -> Engine:
    return create_db_engine(get_settings())


def get_check_health_use_case() -> CheckHealthUseCase:
    adapter = SqlAlchemyDatabaseHealthAdapter(get_engine())
    return CheckHealthUseCase(adapter)


def get_get_version_use_case() -> GetVersionUseCase:
    return GetVersionUseCase(get_settings().app_version)


def get_requirement_repository() -> RequirementRepository:
    return SqlAlchemyRequirementRepository(get_engine())


def get_token_service() -> TokenServicePort:
    return JwtTokenService(get_settings().jwt_secret.get_secret_value())


def get_password_hasher() -> PasswordHasherPort:
    return Pbkdf2PasswordHasher(get_settings().password_hash_iterations)


def get_user_repository() -> UserRepository:
    return SqlAlchemyUserRepository(get_engine())


def get_audit_recorder() -> AuditRecorderPort:
    return SqlAlchemyAuditRecorder(get_engine())


def get_create_requirement_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> CreateRequirement:
    return CreateRequirement(repository, audit)


def get_list_requirements_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> ListRequirements:
    return ListRequirements(repository)


def get_get_requirement_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> GetRequirement:
    return GetRequirement(repository)


def get_list_versions_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> ListVersions:
    return ListVersions(repository)


def get_get_requirement_version_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> GetVersion:
    return GetVersion(repository)


def get_build_preview_document_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> BuildPreviewDocument:
    return BuildPreviewDocument(repository)


def get_update_version_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> UpdateVersion:
    return UpdateVersion(repository, audit)


def get_freeze_and_advance_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> FreezeAndAdvance:
    return FreezeAndAdvance(repository, audit)


def get_change_type_catalog() -> ChangeTypeCatalog:
    return SqlAlchemyChangeTypeCatalog(get_engine())


def get_position_catalog() -> PositionCatalog:
    return SqlAlchemyPositionCatalog(get_engine())


def get_catalog_repositories() -> tuple[ChangeTypeCatalog, PositionCatalog]:
    return get_change_type_catalog(), get_position_catalog()


def get_add_collection_item_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> AddCollectionItem:
    return AddCollectionItem(repository, audit)


def get_update_collection_item_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> UpdateCollectionItem:
    return UpdateCollectionItem(repository, audit)


def get_delete_collection_item_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> DeleteCollectionItem:
    return DeleteCollectionItem(repository, audit)


def get_reorder_collection_items_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> ReorderCollectionItems:
    return ReorderCollectionItems(repository, audit)


def get_register_signature_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> RegisterSignature:
    return RegisterSignature(repository, audit)


def get_add_attachment_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> AddAttachment:
    return AddAttachment(repository, audit)


def get_update_attachment_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> UpdateAttachment:
    return UpdateAttachment(repository, audit)


def get_delete_attachment_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> DeleteAttachment:
    return DeleteAttachment(repository, audit)


def get_reorder_attachments_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> ReorderAttachments:
    return ReorderAttachments(repository, audit)


def get_change_status_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> ChangeStatus:
    return ChangeStatus(repository, audit)


def get_validate_requirement_version_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> ValidateRequirementVersion:
    return ValidateRequirementVersion(repository)


def get_transition_requirement_state_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> TransitionRequirementState:
    return TransitionRequirementState(repository, audit)


def get_list_change_types_use_case(
    catalog: Annotated[ChangeTypeCatalog, Depends(get_change_type_catalog)],
) -> ListChangeTypes:
    return ListChangeTypes(catalog)


def get_list_positions_use_case(
    catalog: Annotated[PositionCatalog, Depends(get_position_catalog)],
) -> ListPositions:
    return ListPositions(catalog)


def get_document_renderer() -> DocumentRendererPort:
    return DocxtplDocumentRenderer(get_settings().templates_dir)


def get_document_converter() -> DocumentConverterPort:
    settings = get_settings()
    return LibreofficeDocumentConverter(
        settings.libreoffice_binary,
        settings.document_generation_timeout_seconds,
    )


def get_requirement_document_repository() -> RequirementDocumentRepository:
    return SqlAlchemyRequirementDocumentRepository(get_engine())


def get_generate_documents_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    document_repository: Annotated[
        RequirementDocumentRepository, Depends(get_requirement_document_repository)
    ],
    renderer: Annotated[DocumentRendererPort, Depends(get_document_renderer)],
    converter: Annotated[DocumentConverterPort, Depends(get_document_converter)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> GenerateRequirementDocuments:
    return GenerateRequirementDocuments(
        repository,
        document_repository,
        renderer,
        converter,
        audit,
        template_version=get_settings().document_template_version,
    )


def get_get_document_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    document_repository: Annotated[
        RequirementDocumentRepository, Depends(get_requirement_document_repository)
    ],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> GetRequirementDocument:
    return GetRequirementDocument(repository, document_repository, audit)


def get_list_documents_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    document_repository: Annotated[
        RequirementDocumentRepository, Depends(get_requirement_document_repository)
    ],
) -> ListRequirementDocuments:
    return ListRequirementDocuments(repository, document_repository)


def get_auth_provider(request: Request) -> AuthProvider:
    settings = get_settings()
    return build_auth_provider(
        settings.auth_provider,
        token_service=get_token_service(),
        user_repository=get_user_repository(),
        authorization=request.headers.get("authorization"),
    )


def get_current_principal(
    auth: Annotated[AuthProvider, Depends(get_auth_provider)],
) -> Principal:
    principal = auth.current_principal()
    if principal is None:
        raise NotAuthenticatedError()
    return principal


def require_action(action: Action) -> Callable[..., Principal]:
    def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        ensure_authorized(frozenset(Role(value) for value in principal.roles), action)
        return principal

    return dependency


def get_authenticate_use_case(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasherPort, Depends(get_password_hasher)],
    token_service: Annotated[TokenServicePort, Depends(get_token_service)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> AuthenticateUser:
    settings = get_settings()
    return AuthenticateUser(
        user_repository,
        password_hasher,
        token_service,
        audit,
        session_ttl_hours=settings.jwt_ttl_hours,
        max_failed_attempts=settings.login_max_failed_attempts,
    )


def get_logout_use_case(
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> LogoutUser:
    return LogoutUser(audit)


def get_session_use_case(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> GetSession:
    return GetSession(user_repository)


def get_create_user_use_case(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasherPort, Depends(get_password_hasher)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> CreateUser:
    return CreateUser(user_repository, password_hasher, audit)


def get_update_user_use_case(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[PasswordHasherPort, Depends(get_password_hasher)],
    audit: Annotated[AuditRecorderPort, Depends(get_audit_recorder)],
) -> UpdateUser:
    return UpdateUser(user_repository, password_hasher, audit)


def get_list_users_use_case(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> ListUsers:
    return ListUsers(user_repository)
