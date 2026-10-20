from __future__ import annotations

from datetime import date

import pytest

from app.application.errors import (
    AttachmentNotFoundError,
    CollectionItemNotFoundError,
    RequirementNotFoundError,
    VersionNotFoundError,
)
from app.application.ports.auth import Principal
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
from app.domain.auth.errors import AccessDeniedError
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
    FakeAuditRecorder,
    FakeChangeTypeCatalog,
    FakePositionCatalog,
    InMemoryRequirementRepository,
)

_VERSION_DATE = date(2026, 1, 1)

_PRINCIPAL = Principal(
    user_id="tester",
    roles=frozenset({"ELABORO", "REVISO", "AUTORIZO", "ADMIN"}),
)


@pytest.fixture()
def repository() -> InMemoryRequirementRepository:
    return InMemoryRequirementRepository()


@pytest.fixture()
def audit() -> FakeAuditRecorder:
    return FakeAuditRecorder()


def _create(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
    folio: int = 1,
) -> Requirement:
    return CreateRequirement(repository, audit).execute(
        principal=_PRINCIPAL,
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
    audit: FakeAuditRecorder,
    requirement_id: int,
    target: RequirementStatus,
) -> Requirement:
    return ChangeStatus(repository, audit).execute(
        requirement_id, target, principal=_PRINCIPAL
    )


def test_create_requirement_builds_borrador_working_version(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit, folio=42)

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
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None

    loaded = GetRequirement(repository).execute(created.id)
    assert loaded == created

    with pytest.raises(RequirementNotFoundError):
        GetRequirement(repository).execute(999999)


def test_list_requirements_paginates_and_filters(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    first = _create(repository, audit, folio=1)
    _create(repository, audit, folio=2)
    _create(repository, audit, folio=3)
    assert first.id is not None
    _to_status(repository, audit, first.id, RequirementStatus.EN_REVISION)

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
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    updated = UpdateVersion(repository, audit).execute(
        created.id,
        version_id,
        VersionEdit(title="Nuevo titulo", current_need="Necesidad"),
        principal=_PRINCIPAL,
    )
    assert _working_version(updated).title == "Nuevo titulo"
    assert _working_version(updated).current_need == "Necesidad"

    _to_status(repository, audit, created.id, RequirementStatus.EN_REVISION)
    with pytest.raises(RequirementNotEditableError):
        UpdateVersion(repository, audit).execute(
            created.id,
            version_id,
            VersionEdit(title="No permitido"),
            principal=_PRINCIPAL,
        )


def test_update_frozen_version_is_rejected(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    FreezeAndAdvance(repository, audit).execute(
        created.id,
        principal=_PRINCIPAL,
        document_version="2.0",
        version_date=_VERSION_DATE,
    )

    with pytest.raises(RequirementNotEditableError):
        UpdateVersion(repository, audit).execute(
            created.id,
            version_id,
            VersionEdit(title="No permitido"),
            principal=_PRINCIPAL,
        )


def test_list_versions_and_get_version(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    FreezeAndAdvance(repository, audit).execute(
        created.id,
        principal=_PRINCIPAL,
        document_version="2.0",
        version_date=_VERSION_DATE,
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
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    with_item = AddCollectionItem(repository, audit).execute(
        created.id,
        version_id,
        CollectionKind.OBJETIVOS,
        principal=_PRINCIPAL,
        content="Objetivo activo",
    )
    item_id = with_item.objectives[0].id
    assert item_id is not None
    DeleteCollectionItem(repository, audit).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, item_id, principal=_PRINCIPAL
    )
    AddCollectionItem(repository, audit).execute(
        created.id,
        version_id,
        CollectionKind.OBJETIVOS,
        principal=_PRINCIPAL,
        content="Objetivo dos",
    )

    advanced = FreezeAndAdvance(repository, audit).execute(
        created.id,
        principal=_PRINCIPAL,
        document_version="2.0",
        version_date=_VERSION_DATE,
        title="v2",
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
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None

    in_review = _to_status(repository, audit, created.id, RequirementStatus.EN_REVISION)
    assert in_review.status is RequirementStatus.EN_REVISION
    validated = _to_status(repository, audit, created.id, RequirementStatus.VALIDADO)
    assert validated.status is RequirementStatus.VALIDADO

    # Destino sin fila en la matriz de roles: AccessDeniedError para todos
    # (incluido ADMIN) antes de evaluar la maquina de estados.
    with pytest.raises(AccessDeniedError):
        _to_status(repository, audit, created.id, RequirementStatus.BORRADOR)

    with pytest.raises(InvalidStateTransitionError):
        _to_status(repository, audit, created.id, RequirementStatus.GENERADO)


def test_change_status_denies_insufficient_role(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None

    editor = Principal(user_id="editor", roles=frozenset({"ELABORO"}))
    # El destino GENERADO exige AUTORIZO/ADMIN: 403 de rol sin persistir.
    with pytest.raises(AccessDeniedError):
        ChangeStatus(repository, audit).execute(
            created.id, RequirementStatus.GENERADO, principal=editor
        )

    assert repository.get(created.id).status is RequirementStatus.BORRADOR


def test_collections_add_update_delete_reorder(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    adder = AddCollectionItem(repository, audit)

    for content in ("uno", "dos", "tres"):
        adder.execute(
            created.id,
            version_id,
            CollectionKind.OBJETIVOS,
            principal=_PRINCIPAL,
            content=content,
        )

    version = GetRequirement(repository).execute(created.id).versions[0]
    ids = [item.id for item in version.objectives]
    assert len(ids) == 3
    assert [item.content for item in version.objectives] == ["uno", "dos", "tres"]

    updated = UpdateCollectionItem(repository, audit).execute(
        created.id,
        version_id,
        CollectionKind.OBJETIVOS,
        ids[1],
        principal=_PRINCIPAL,
        content="dos editado",
    )
    assert [item.content for item in updated.objectives] == ["uno", "dos editado", "tres"]

    reordered = ReorderCollectionItems(repository, audit).execute(
        created.id,
        version_id,
        CollectionKind.OBJETIVOS,
        [ids[2], ids[0]],
        principal=_PRINCIPAL,
    )
    assert [item.content for item in reordered.objectives] == ["tres", "uno", "dos editado"]
    assert [item.order for item in reordered.objectives] == [1, 2, 3]

    DeleteCollectionItem(repository, audit).execute(
        created.id, version_id, CollectionKind.OBJETIVOS, ids[0], principal=_PRINCIPAL
    )
    after_delete = GetRequirement(repository).execute(created.id).versions[0]
    deleted = next(item for item in after_delete.objectives if item.id == ids[0])
    assert deleted.active is False


def test_collections_benefits_keep_kind(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    adder = AddCollectionItem(repository, audit)

    adder.execute(
        created.id,
        version_id,
        CollectionKind.BENEFICIOS,
        principal=_PRINCIPAL,
        content="Cualitativo",
        benefit_kind=BenefitKind.CUALITATIVO,
    )
    version = adder.execute(
        created.id,
        version_id,
        CollectionKind.BENEFICIOS,
        principal=_PRINCIPAL,
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
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    with pytest.raises(CollectionItemNotFoundError):
        UpdateCollectionItem(repository, audit).execute(
            created.id,
            version_id,
            CollectionKind.OBJETIVOS,
            999999,
            principal=_PRINCIPAL,
            content="x",
        )
    with pytest.raises(CollectionItemNotFoundError):
        DeleteCollectionItem(repository, audit).execute(
            created.id, version_id, CollectionKind.OBJETIVOS, 999999, principal=_PRINCIPAL
        )
    with pytest.raises(CollectionItemNotFoundError):
        ReorderCollectionItems(repository, audit).execute(
            created.id,
            version_id,
            CollectionKind.OBJETIVOS,
            [999999],
            principal=_PRINCIPAL,
        )


def test_attachments_crud(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    added = AddAttachment(repository, audit).execute(
        created.id,
        version_id,
        principal=_PRINCIPAL,
        name="anexo.pdf",
        storage_key="objects/anexo.pdf",
        mime_type="application/pdf",
        caption="Soporte",
    )
    assert added.id is not None
    assert added.name == "anexo.pdf"

    updated = UpdateAttachment(repository, audit).execute(
        created.id, version_id, added.id, principal=_PRINCIPAL, name="anexo-v2.pdf"
    )
    assert updated.name == "anexo-v2.pdf"

    second = AddAttachment(repository, audit).execute(
        created.id,
        version_id,
        principal=_PRINCIPAL,
        name="b.txt",
        storage_key="objects/b.txt",
    )
    assert second.id is not None
    reordered = ReorderAttachments(repository, audit).execute(
        created.id, version_id, [second.id, added.id], principal=_PRINCIPAL
    )
    assert [attachment.id for attachment in reordered] == [second.id, added.id]

    DeleteAttachment(repository, audit).execute(
        created.id, version_id, added.id, principal=_PRINCIPAL
    )
    after = GetRequirement(repository).execute(created.id).versions[0]
    deleted = next(item for item in after.attachments if item.id == added.id)
    assert deleted.active is False

    with pytest.raises(AttachmentNotFoundError):
        UpdateAttachment(repository, audit).execute(
            created.id, version_id, 999999, principal=_PRINCIPAL, name="x"
        )


def test_register_signature_requires_final_state_and_current_version(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None
    signer = RegisterSignature(repository, audit)

    with pytest.raises(SignatureNotAllowedError):
        signer.execute(
            created.id,
            version_id,
            principal=_PRINCIPAL,
            role=SignatureRole.ELABORO,
            name="Ana",
            position="Analista",
        )

    _to_status(repository, audit, created.id, RequirementStatus.EN_REVISION)
    _to_status(repository, audit, created.id, RequirementStatus.VALIDADO)
    approved = _to_status(repository, audit, created.id, RequirementStatus.APROBADO)
    assert approved.status is RequirementStatus.APROBADO

    elaboration = signer.execute(
        created.id,
        version_id,
        principal=_PRINCIPAL,
        role=SignatureRole.ELABORO,
        name="Ana",
        position="Analista",
    )
    assert elaboration.id is not None
    authorization = signer.execute(
        created.id,
        version_id,
        principal=_PRINCIPAL,
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
            principal=_PRINCIPAL,
            role=SignatureRole.REVISO,
            name="X",
            position="Y",
        )


def test_register_signature_rejects_wrong_role_and_admin(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    _to_status(repository, audit, created.id, RequirementStatus.EN_REVISION)
    _to_status(repository, audit, created.id, RequirementStatus.VALIDADO)
    _to_status(repository, audit, created.id, RequirementStatus.APROBADO)

    reviser = Principal(user_id="revisor", roles=frozenset({"REVISO"}))
    with pytest.raises(AccessDeniedError):
        RegisterSignature(repository, audit).execute(
            created.id,
            version_id,
            principal=reviser,
            role=SignatureRole.ELABORO,
            name="Ana",
            position="Analista",
        )

    admin_only = Principal(user_id="root", roles=frozenset({"ADMIN"}))
    with pytest.raises(AccessDeniedError):
        RegisterSignature(repository, audit).execute(
            created.id,
            version_id,
            principal=admin_only,
            role=SignatureRole.ELABORO,
            name="Ana",
            position="Analista",
        )

    assert repository.get(created.id).versions[0].signatures == ()


def test_register_signature_on_non_current_version_is_rejected(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = _create(repository, audit)
    assert created.id is not None
    version_id = _working_version(created).id
    assert version_id is not None

    _to_status(repository, audit, created.id, RequirementStatus.EN_REVISION)
    _to_status(repository, audit, created.id, RequirementStatus.VALIDADO)
    _to_status(repository, audit, created.id, RequirementStatus.APROBADO)
    FreezeAndAdvance(repository, audit).execute(
        created.id,
        principal=_PRINCIPAL,
        document_version="2.0",
        version_date=_VERSION_DATE,
    )

    with pytest.raises(SignatureNotAllowedError):
        RegisterSignature(repository, audit).execute(
            created.id,
            version_id,
            principal=_PRINCIPAL,
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
