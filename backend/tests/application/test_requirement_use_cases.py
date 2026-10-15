from __future__ import annotations

from datetime import date

import pytest

from app.application.errors import (
    AttachmentNotFoundError,
    CollectionItemNotFoundError,
    RequirementNotFoundError,
    VersionNotFoundError,
)
from app.application.use_cases.requirement import (
    AddAttachment,
    AddCollectionItem,
    ChangeStatus,
    CreateRequirement,
    DeleteAttachment,
    DeleteCollectionItem,
    FreezeAndAdvance,
    GetRequirement,
    GetVersion,
    ListChangeTypes,
    ListPositions,
    ListRequirements,
    ListVersions,
    RegisterSignature,
    ReorderAttachments,
    ReorderCollectionItems,
    UpdateAttachment,
    UpdateCollectionItem,
    UpdateVersion,
    VersionEdit,
)
from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.collections import CollectionKind
from app.domain.requirement.enums import (
    BenefitKind,
    RequirementStatus,
    SignatureRole,
)
from app.domain.requirement.errors import (
    InvalidStateTransitionError,
    RequirementNotEditableError,
    SignatureNotAllowedError,
)
from app.domain.requirement.items import Benefit
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion
from tests.application.fakes import (
    FakeChangeTypeCatalog,
    FakePositionCatalog,
    InMemoryRequirementRepository,
)

_VERSION_DATE = date(2026, 1, 1)


@pytest.fixture()
def repository() -> InMemoryRequirementRepository:
    return InMemoryRequirementRepository()


def _create(repository: InMemoryRequirementRepository, folio: int = 1) -> Requirement:
    return CreateRequirement(repository).execute(
        folio=folio,
        title="Titulo",
        change_type_id=1,
        system="SAP",
        document_version="1.0",
        version_date=_VERSION_DATE,
    )


def _working_version(requirement: Requirement) -> RequirementVersion:
    version = requirement.current_version()
    assert version is not None
    return version


def _to_status(
    repository: InMemoryRequirementRepository,
    requirement_id: int,
    target: RequirementStatus,
) -> Requirement:
    return ChangeStatus(repository).execute(requirement_id, target)


def test_create_requirement_builds_borrador_working_version(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository, folio=42)

    assert created.id is not None
    assert created.folio == 42
    assert created.ticket == "T#42"
    assert created.status is RequirementStatus.BORRADOR
    version = _working_version(created)
    assert version.number == 1
    assert version.title == "Titulo"
    assert version.change_type_id == 1
    assert version.system == "SAP"
    assert version.document_version == "1.0"
    assert version.frozen is False


def test_get_requirement_returns_aggregate_and_raises_404(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None

    loaded = GetRequirement(repository).execute(created.id)
    assert loaded == created

    with pytest.raises(RequirementNotFoundError):
        GetRequirement(repository).execute(999999)


def test_list_requirements_paginates_and_filters(
    repository: InMemoryRequirementRepository,
) -> None:
    first = _create(repository, folio=1)
    _create(repository, folio=2)
    _create(repository, folio=3)
    assert first.id is not None
    _to_status(repository, first.id, RequirementStatus.EN_REVISION)

    page = ListRequirements(repository).execute(page=2, size=2)
    assert page.page == 2
    assert page.size == 2
    assert page.total == 3
    assert len(page.items) == 1
    assert page.items[0].folio == 3

    by_status = ListRequirements(repository).execute(
        status=RequirementStatus.EN_REVISION
    )
    assert by_status.total == 1
    assert by_status.items[0].folio == 1

    by_folio = ListRequirements(repository).execute(folio=3)
    assert by_folio.total == 1
    assert by_folio.items[0].folio == 3


def test_update_version_only_in_borrador(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    updated = UpdateVersion(repository).execute(
        created.id, version_id, VersionEdit(title="Nuevo titulo", current_need="Necesidad")
    )
    assert _working_version(updated).title == "Nuevo titulo"
    assert _working_version(updated).current_need == "Necesidad"

    _to_status(repository, created.id, RequirementStatus.EN_REVISION)
    with pytest.raises(RequirementNotEditableError):
        UpdateVersion(repository).execute(
            created.id, version_id, VersionEdit(title="No permitido")
        )


def test_update_frozen_version_is_rejected(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    FreezeAndAdvance(repository).execute(
        created.id, document_version="2.0", version_date=_VERSION_DATE
    )

    with pytest.raises(RequirementNotEditableError):
        UpdateVersion(repository).execute(
            created.id, version_id, VersionEdit(title="No permitido")
        )


def test_list_versions_and_get_version(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    FreezeAndAdvance(repository).execute(
        created.id, document_version="2.0", version_date=_VERSION_DATE
    )

    versions = ListVersions(repository).execute(created.id)
    assert [version.number for version in versions] == [1, 2]

    second = versions[1]
    assert second.id is not None
    assert GetVersion(repository).execute(created.id, second.id) == second

    with pytest.raises(VersionNotFoundError):
        GetVersion(repository).execute(created.id, 999999)


def test_freeze_and_advance_copy_on_write(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    with_item = AddCollectionItem(repository).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, content="Objetivo activo"
    )
    item_id = with_item.objectives[0].id
    assert item_id is not None
    DeleteCollectionItem(repository).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, item_id
    )
    AddCollectionItem(repository).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, content="Objetivo dos"
    )

    advanced = FreezeAndAdvance(repository).execute(
        created.id, document_version="2.0", version_date=_VERSION_DATE, title="v2"
    )

    assert len(advanced.versions) == 2
    frozen, successor = advanced.versions
    assert frozen.frozen is True
    assert successor.frozen is False
    assert successor.title == "v2"
    assert all(item.active for item in successor.objectives)
    assert [item.content for item in successor.objectives] == ["Objetivo dos"]
    assert advanced.current_version() is successor


def test_change_status_allowed_and_rejected(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None

    in_review = _to_status(repository, created.id, RequirementStatus.EN_REVISION)
    assert in_review.status is RequirementStatus.EN_REVISION
    validated = _to_status(repository, created.id, RequirementStatus.VALIDADO)
    assert validated.status is RequirementStatus.VALIDADO

    with pytest.raises(InvalidStateTransitionError):
        _to_status(repository, created.id, RequirementStatus.BORRADOR)


def test_collections_add_update_delete_reorder(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    adder = AddCollectionItem(repository)

    for content in ("uno", "dos", "tres"):
        adder.execute(created.id, version_id, CollectionKind.OBJETIVOS, content=content)

    version = GetRequirement(repository).execute(created.id).versions[0]
    ids = [item.id for item in version.objectives]
    assert len(ids) == 3
    assert [item.content for item in version.objectives] == ["uno", "dos", "tres"]

    updated = UpdateCollectionItem(repository).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, ids[1], content="dos editado"
    )
    assert [item.content for item in updated.objectives] == ["uno", "dos editado", "tres"]

    reordered = ReorderCollectionItems(repository).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, [ids[2], ids[0]]
    )
    assert [item.content for item in reordered.objectives] == ["tres", "uno", "dos editado"]
    assert [item.order for item in reordered.objectives] == [1, 2, 3]

    DeleteCollectionItem(repository).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, ids[0]
    )
    after_delete = GetRequirement(repository).execute(created.id).versions[0]
    deleted = next(item for item in after_delete.objectives if item.id == ids[0])
    assert deleted.active is False


def test_collections_benefits_keep_kind(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    adder = AddCollectionItem(repository)

    adder.execute(
        created.id,
        version_id,
        CollectionKind.BENEFICIOS,
        content="Cualitativo",
        benefit_kind=BenefitKind.CUALITATIVO,
    )
    version = adder.execute(
        created.id,
        version_id,
        CollectionKind.BENEFICIOS,
        content="Cuantitativo",
        benefit_kind=BenefitKind.CUANTITATIVO,
    )

    assert all(isinstance(item, Benefit) for item in version.benefits)
    assert [item.kind for item in version.benefits] == [
        BenefitKind.CUALITATIVO,
        BenefitKind.CUANTITATIVO,
    ]


def test_collection_item_not_found(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    with pytest.raises(CollectionItemNotFoundError):
        UpdateCollectionItem(repository).execute(
            created.id, version_id, CollectionKind.OBJETIVOS, 999999, content="x"
        )
    with pytest.raises(CollectionItemNotFoundError):
        DeleteCollectionItem(repository).execute(
            created.id, version_id, CollectionKind.OBJETIVOS, 999999
        )
    with pytest.raises(CollectionItemNotFoundError):
        ReorderCollectionItems(repository).execute(
            created.id, version_id, CollectionKind.OBJETIVOS, [999999]
        )


def test_attachments_crud(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    added = AddAttachment(repository).execute(
        created.id,
        version_id,
        name="anexo.pdf",
        storage_key="objects/anexo.pdf",
        mime_type="application/pdf",
        caption="Soporte",
    )
    assert added.id is not None
    assert added.name == "anexo.pdf"

    updated = UpdateAttachment(repository).execute(
        created.id, version_id, added.id, name="anexo-v2.pdf"
    )
    assert updated.name == "anexo-v2.pdf"

    second = AddAttachment(repository).execute(
        created.id, version_id, name="b.txt", storage_key="objects/b.txt"
    )
    assert second.id is not None
    reordered = ReorderAttachments(repository).execute(
        created.id, version_id, [second.id, added.id]
    )
    assert [attachment.id for attachment in reordered] == [second.id, added.id]

    DeleteAttachment(repository).execute(created.id, version_id, added.id)
    after = GetRequirement(repository).execute(created.id).versions[0]
    deleted = next(item for item in after.attachments if item.id == added.id)
    assert deleted.active is False

    with pytest.raises(AttachmentNotFoundError):
        UpdateAttachment(repository).execute(
            created.id, version_id, 999999, name="x"
        )


def test_register_signature_requires_final_state_and_current_version(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    signer = RegisterSignature(repository)

    with pytest.raises(SignatureNotAllowedError):
        signer.execute(
            created.id,
            version_id,
            role=SignatureRole.ELABORO,
            name="Ana",
            position="Analista",
        )

    _to_status(repository, created.id, RequirementStatus.EN_REVISION)
    _to_status(repository, created.id, RequirementStatus.VALIDADO)
    approved = _to_status(repository, created.id, RequirementStatus.APROBADO)
    assert approved.status is RequirementStatus.APROBADO

    elaboration = signer.execute(
        created.id,
        version_id,
        role=SignatureRole.ELABORO,
        name="Ana",
        position="Analista",
    )
    assert elaboration.id is not None
    authorization = signer.execute(
        created.id,
        version_id,
        role=SignatureRole.AUTORIZO,
        name="Luis",
        position="Gerente",
    )
    assert authorization.role is SignatureRole.AUTORIZO

    signatures = GetRequirement(repository).execute(created.id).versions[0].signatures
    assert {signature.role for signature in signatures} == {
        SignatureRole.ELABORO,
        SignatureRole.AUTORIZO,
    }

    with pytest.raises(VersionNotFoundError):
        signer.execute(
            created.id,
            999999,
            role=SignatureRole.REVISO,
            name="X",
            position="Y",
        )


def test_register_signature_on_non_current_version_is_rejected(
    repository: InMemoryRequirementRepository,
) -> None:
    created = _create(repository)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    _to_status(repository, created.id, RequirementStatus.EN_REVISION)
    _to_status(repository, created.id, RequirementStatus.VALIDADO)
    _to_status(repository, created.id, RequirementStatus.APROBADO)
    FreezeAndAdvance(repository).execute(
        created.id, document_version="2.0", version_date=_VERSION_DATE
    )

    with pytest.raises(SignatureNotAllowedError):
        RegisterSignature(repository).execute(
            created.id,
            version_id,
            role=SignatureRole.ELABORO,
            name="Ana",
            position="Analista",
        )


def test_list_catalogs() -> None:
    change_types = FakeChangeTypeCatalog(
        (
            ChangeType(code="MEJORA", name="Mejora", id=1),
            ChangeType(code="NUEVO", name="Nuevo", active=False, id=2),
        )
    )
    assert [item.code for item in ListChangeTypes(change_types).execute()] == ["MEJORA"]

    positions = FakePositionCatalog(
        (
            Position(role=SignatureRole.ELABORO, name="Analista", id=1),
            Position(role=SignatureRole.AUTORIZO, name="Gerente", id=2),
            Position(
                role=SignatureRole.AUTORIZO, name="Inactivo", active=False, id=3
            ),
        )
    )
    assert [item.name for item in ListPositions(positions).execute()] == [
        "Analista",
        "Gerente",
    ]
    assert [
        item.name
        for item in ListPositions(positions).execute(SignatureRole.AUTORIZO)
    ] == ["Gerente"]
