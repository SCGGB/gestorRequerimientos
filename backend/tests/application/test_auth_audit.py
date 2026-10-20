from __future__ import annotations

from datetime import date

import pytest

from app.application.ports.auth import Principal
from app.application.use_cases.auth import LogoutUser
from app.application.use_cases.requirement import (
    AddAttachment,
    AddCollectionItem,
    CreateRequirement,
    FreezeAndAdvance,
    GenerateRequirementDocuments,
    GetRequirementDocument,
    RegisterSignature,
    TransitionRequirementState,
    UpdateVersion,
    VersionEdit,
)
from app.domain.auth.audit import AuditAction
from app.domain.requirement.collections import CollectionKind
from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.infrastructure.config import Settings
from tests.application.fakes import (
    FakeAuditRecorder,
    FakeDocumentConverter,
    FakeDocumentRenderer,
    InMemoryRequirementDocumentRepository,
    InMemoryRequirementRepository,
)
from tests.factories import complete_version, requirement_with

_PRINCIPAL = Principal(
    user_id="tester",
    roles=frozenset({"ELABORO", "REVISO", "AUTORIZO", "ADMIN"}),
)
_VERSION_DATE = date(2026, 1, 1)


def _signed_requirement(status: RequirementStatus) -> Requirement:
    version = complete_version()
    version = version.with_signature(
        Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista")
    )
    version = version.with_signature(
        Signature(role=SignatureRole.AUTORIZO, name="Luis", position="Gerente")
    )
    return Requirement(folio=1, status=status, versions=(version,))


@pytest.fixture()
def repository() -> InMemoryRequirementRepository:
    return InMemoryRequirementRepository()


@pytest.fixture()
def audit() -> FakeAuditRecorder:
    return FakeAuditRecorder()


def test_logout_registers_audit_entry(audit: FakeAuditRecorder) -> None:
    LogoutUser(audit).execute(_PRINCIPAL)

    entry = audit.find(AuditAction.LOGOUT.value)
    assert entry is not None
    assert entry.entity == "SYS_USUARIO"
    assert entry.actor == "tester"
    assert entry.entity_id is None


def test_requirement_writes_audit_real_actor(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = CreateRequirement(repository, audit).execute(
        principal=_PRINCIPAL,
        folio=7,
        title="Titulo inicial",
        change_type_id=1,
        system="SAP",
        document_version="1.0",
        version_date=_VERSION_DATE,
    )
    assert created.id is not None
    version = created.current_version()
    assert version is not None and version.id is not None
    version_id = version.id

    UpdateVersion(repository, audit).execute(
        created.id,
        version_id,
        VersionEdit(title="Titulo editado"),
        principal=_PRINCIPAL,
    )
    FreezeAndAdvance(repository, audit).execute(
        created.id,
        principal=_PRINCIPAL,
        document_version="2.0",
        version_date=_VERSION_DATE,
    )

    assert audit.actions() == (
        AuditAction.REQUIREMENT_CREATE.value,
        AuditAction.VERSION_UPDATE.value,
        AuditAction.VERSION_FREEZE.value,
    )
    assert all(entry.actor == "tester" for entry in audit.entries)

    create = audit.entries[0]
    assert create.entity == "REQ_REQUERIMIENTO"
    assert create.entity_id == created.id
    assert create.detail == {"folio": 7, "titulo": "Titulo inicial"}

    update = audit.entries[1]
    assert update.entity == "REQ_VERSION"
    assert update.entity_id == version_id
    assert update.detail == {"campos": ["title"]}

    freeze = audit.entries[2]
    assert freeze.entity == "REQ_VERSION"
    assert freeze.detail == {"numero_version": 1, "version_documento": "2.0"}


def test_transition_audits_reason_in_detail(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = repository.save(requirement_with(), actor="seed")
    assert saved.id is not None

    TransitionRequirementState(repository, audit).execute(
        saved.id,
        RequirementStatus.EN_REVISION.value,
        principal=_PRINCIPAL,
        reason="Documentacion completa",
    )

    entry = audit.find(AuditAction.STATE_TRANSITION.value)
    assert entry is not None
    assert entry.entity == "REQ_REQUERIMIENTO"
    assert entry.entity_id == saved.id
    assert entry.actor == "tester"
    assert entry.detail is not None
    assert entry.detail["estado_anterior"] == "BORRADOR"
    assert entry.detail["estado_actual"] == "EN_REVISION"
    assert entry.detail["motivo"] == "Documentacion completa"


def test_collections_and_attachments_audited_at_version_level(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    created = CreateRequirement(repository, audit).execute(
        principal=_PRINCIPAL,
        folio=8,
        title="Titulo",
        change_type_id=1,
        system="SAP",
        document_version="1.0",
        version_date=_VERSION_DATE,
    )
    assert created.id is not None
    version_id = created.current_version().id  # type: ignore[union-attr]
    assert version_id is not None
    audit.entries.clear()

    AddCollectionItem(repository, audit).execute(
        created.id,
        version_id,
        CollectionKind.OBJETIVOS,
        principal=_PRINCIPAL,
        content="Objetivo",
    )
    AddAttachment(repository, audit).execute(
        created.id,
        version_id,
        principal=_PRINCIPAL,
        name="anexo.pdf",
        storage_key="objects/anexo.pdf",
    )

    collection = audit.find(AuditAction.COLLECTION_UPDATE.value)
    assert collection is not None
    assert collection.entity == "REQ_VERSION"
    assert collection.entity_id == version_id
    assert collection.detail == {"coleccion": "OBJETIVOS", "operacion": "alta"}

    attachment = audit.find(AuditAction.ATTACHMENT_UPDATE.value)
    assert attachment is not None
    assert attachment.entity == "REQ_VERSION"
    assert attachment.entity_id == version_id
    assert attachment.detail == {"operacion": "alta"}


def test_signature_audited(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = repository.save(
        _signed_requirement(RequirementStatus.APROBADO), actor="seed"
    )
    assert saved.id is not None
    version_id = saved.versions[0].id
    assert version_id is not None

    RegisterSignature(repository, audit).execute(
        saved.id,
        version_id,
        principal=_PRINCIPAL,
        role=SignatureRole.ELABORO,
        name="Ana",
        position="Analista",
    )

    entry = audit.find(AuditAction.SIGNATURE_REGISTERED.value)
    assert entry is not None
    assert entry.entity == "REQ_VERSION"
    assert entry.entity_id == version_id
    assert entry.actor == "tester"
    assert entry.detail == {"rol": "ELABORO", "nombre": "Ana"}


def test_documents_generated_and_downloaded_are_audited(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    document_repository = InMemoryRequirementDocumentRepository()
    saved = repository.save(
        _signed_requirement(RequirementStatus.APROBADO), actor="seed"
    )
    assert saved.id is not None

    documents = GenerateRequirementDocuments(
        repository,
        document_repository,
        FakeDocumentRenderer(),
        FakeDocumentConverter(),
        audit,
        template_version="v1",
    ).execute(saved.id, principal=_PRINCIPAL)

    generated = [
        entry for entry in audit.entries
        if entry.action is AuditAction.DOCUMENT_GENERATED
    ]
    assert len(generated) == 2
    assert all(entry.actor == "tester" for entry in generated)
    assert all(entry.entity == "REQ_DOCUMENTO" for entry in generated)
    assert {entry.detail["formato"] for entry in generated} == {"DOCX", "PDF"}  # type: ignore[index]
    assert {entry.detail["nombre_archivo"] for entry in generated} == {  # type: ignore[index]
        document.file_name for document in documents
    }

    audit.entries.clear()
    document_id = documents[0].id
    assert document_id is not None
    GetRequirementDocument(repository, document_repository, audit).execute(
        saved.id, document_id, principal=_PRINCIPAL
    )

    download = audit.find(AuditAction.DOCUMENT_DOWNLOADED.value)
    assert download is not None
    assert download.actor == "tester"
    assert download.entity == "REQ_DOCUMENTO"
    assert download.entity_id == document_id
    assert download.detail == {"nombre_archivo": documents[0].file_name}


def test_full_write_flow_works_without_ai_service(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CA-15: ningun caso de uso de negocio requiere un proveedor de IA."""
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    settings = Settings(_env_file=None)
    assert settings.ai_provider == "none"

    created = CreateRequirement(repository, audit).execute(
        principal=_PRINCIPAL,
        folio=9,
        title="Sin IA",
        change_type_id=1,
        system="SAP",
        document_version="1.0",
        version_date=_VERSION_DATE,
    )
    assert created.id is not None
    version = created.current_version()
    assert version is not None and version.id is not None
    version_id = version.id

    UpdateVersion(repository, audit).execute(
        created.id,
        version_id,
        VersionEdit(current_need="Necesidad real"),
        principal=_PRINCIPAL,
    )
    # BORRADOR->EN_REVISION exigiria colecciones minimas; con CANCELADO la
    # maquina no valida contenido y el flujo completo sigue sin IA.
    TransitionRequirementState(repository, audit).execute(
        created.id,
        RequirementStatus.CANCELADO.value,
        principal=_PRINCIPAL,
        reason="Alta sin IA",
    )

    assert audit.actions() == (
        AuditAction.REQUIREMENT_CREATE.value,
        AuditAction.VERSION_UPDATE.value,
        AuditAction.STATE_TRANSITION.value,
    )
    assert repository.get(created.id).status is RequirementStatus.CANCELADO
