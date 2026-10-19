from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.engine import Engine

from app.application.ports.catalog_repository import ChangeTypeCatalog, PositionCatalog
from app.application.ports.document_converter import DocumentConverterPort
from app.application.ports.document_renderer import DocumentRendererPort
from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.application.ports.requirement_repository import RequirementRepository
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
from app.infrastructure.adapters.catalogs import (
    SqlAlchemyChangeTypeCatalog,
    SqlAlchemyPositionCatalog,
)
from app.infrastructure.adapters.database_health import SqlAlchemyDatabaseHealthAdapter
from app.infrastructure.adapters.document_converter import (
    LibreofficeDocumentConverter,
)
from app.infrastructure.adapters.document_renderer import DocxtplDocumentRenderer
from app.infrastructure.adapters.requirement_document_repository import (
    SqlAlchemyRequirementDocumentRepository,
)
from app.infrastructure.adapters.requirement_repository import (
    SqlAlchemyRequirementRepository,
)
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


def get_create_requirement_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> CreateRequirement:
    return CreateRequirement(repository)


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
) -> UpdateVersion:
    return UpdateVersion(repository)


def get_freeze_and_advance_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> FreezeAndAdvance:
    return FreezeAndAdvance(repository)


def get_change_type_catalog() -> ChangeTypeCatalog:
    return SqlAlchemyChangeTypeCatalog(get_engine())


def get_position_catalog() -> PositionCatalog:
    return SqlAlchemyPositionCatalog(get_engine())


def get_catalog_repositories() -> tuple[ChangeTypeCatalog, PositionCatalog]:
    return get_change_type_catalog(), get_position_catalog()


def get_add_collection_item_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> AddCollectionItem:
    return AddCollectionItem(repository)


def get_update_collection_item_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> UpdateCollectionItem:
    return UpdateCollectionItem(repository)


def get_delete_collection_item_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> DeleteCollectionItem:
    return DeleteCollectionItem(repository)


def get_reorder_collection_items_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> ReorderCollectionItems:
    return ReorderCollectionItems(repository)


def get_register_signature_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> RegisterSignature:
    return RegisterSignature(repository)


def get_add_attachment_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> AddAttachment:
    return AddAttachment(repository)


def get_update_attachment_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> UpdateAttachment:
    return UpdateAttachment(repository)


def get_delete_attachment_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> DeleteAttachment:
    return DeleteAttachment(repository)


def get_reorder_attachments_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> ReorderAttachments:
    return ReorderAttachments(repository)


def get_change_status_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> ChangeStatus:
    return ChangeStatus(repository)


def get_validate_requirement_version_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> ValidateRequirementVersion:
    return ValidateRequirementVersion(repository)


def get_transition_requirement_state_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
) -> TransitionRequirementState:
    return TransitionRequirementState(repository)


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
) -> GenerateRequirementDocuments:
    return GenerateRequirementDocuments(
        repository,
        document_repository,
        renderer,
        converter,
        template_version=get_settings().document_template_version,
    )


def get_get_document_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    document_repository: Annotated[
        RequirementDocumentRepository, Depends(get_requirement_document_repository)
    ],
) -> GetRequirementDocument:
    return GetRequirementDocument(repository, document_repository)


def get_list_documents_use_case(
    repository: Annotated[RequirementRepository, Depends(get_requirement_repository)],
    document_repository: Annotated[
        RequirementDocumentRepository, Depends(get_requirement_document_repository)
    ],
) -> ListRequirementDocuments:
    return ListRequirementDocuments(repository, document_repository)
