from __future__ import annotations

import pytest

from app.application.errors import DocumentNotFoundError, RequirementNotFoundError
from app.application.ports.auth import Principal
from app.application.use_cases.requirement import (
    GenerateRequirementDocuments,
    GetRequirementDocument,
    ListRequirementDocuments,
)
from app.domain.auth.audit import AuditAction
from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from tests.application.fakes import (
    FakeAuditRecorder,
    FakeDocumentConverter,
    FakeDocumentRenderer,
    InMemoryRequirementDocumentRepository,
    InMemoryRequirementRepository,
)
from tests.factories import complete_version

_PRINCIPAL = Principal(
    user_id="tester",
    roles=frozenset({"ELABORO", "REVISO", "AUTORIZO", "ADMIN"}),
)


def _signed_requirement(folio: int) -> Requirement:
    version = complete_version()
    version = version.with_signature(
        Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista")
    )
    version = version.with_signature(
        Signature(role=SignatureRole.AUTORIZO, name="Luis", position="Gerente")
    )
    return Requirement(
        folio=folio,
        status=RequirementStatus.APROBADO,
        versions=(version,),
    )


def _generate(
    repository: InMemoryRequirementRepository,
    document_repository: InMemoryRequirementDocumentRepository,
    audit: FakeAuditRecorder,
    requirement_id: int,
) -> None:
    GenerateRequirementDocuments(
        repository,
        document_repository,
        FakeDocumentRenderer(),
        FakeDocumentConverter(),
        audit,
        template_version="v1",
    ).execute(requirement_id, principal=_PRINCIPAL)


def test_get_document_returns_content_and_audits_download() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    audit = FakeAuditRecorder()
    requirement = repository.save(_signed_requirement(1), actor="seed")
    assert requirement.id is not None
    _generate(repository, document_repository, audit, requirement.id)
    document_id = document_repository.list_by_requirement(requirement.id)[0].id
    assert document_id is not None
    audit.entries.clear()

    document = GetRequirementDocument(repository, document_repository, audit).execute(
        requirement.id, document_id, principal=_PRINCIPAL
    )

    assert document.content is not None
    entry = audit.find(AuditAction.DOCUMENT_DOWNLOADED.value)
    assert entry is not None
    assert entry.actor == "tester"
    assert entry.entity == "REQ_DOCUMENTO"
    assert entry.entity_id == document_id
    assert entry.detail is not None
    assert entry.detail["nombre_archivo"] == document.file_name


def test_get_document_not_belonging_to_requirement_raises_not_found() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    audit = FakeAuditRecorder()
    requirement = repository.save(_signed_requirement(1), actor="seed")
    other = repository.save(_signed_requirement(2), actor="seed")
    assert requirement.id is not None and other.id is not None
    _generate(repository, document_repository, audit, requirement.id)
    document_id = document_repository.list_by_requirement(requirement.id)[0].id
    assert document_id is not None
    audit.entries.clear()

    with pytest.raises(DocumentNotFoundError):
        GetRequirementDocument(repository, document_repository, audit).execute(
            other.id, document_id, principal=_PRINCIPAL
        )

    assert audit.entries == []


def test_list_documents_returns_history_without_content() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    audit = FakeAuditRecorder()
    requirement = repository.save(_signed_requirement(1), actor="seed")
    assert requirement.id is not None
    _generate(repository, document_repository, audit, requirement.id)

    documents = ListRequirementDocuments(repository, document_repository).execute(
        requirement.id
    )

    assert len(documents) == 2
    assert all(document.content is None for document in documents)


def test_list_documents_missing_requirement_raises_not_found() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()

    with pytest.raises(RequirementNotFoundError):
        ListRequirementDocuments(repository, document_repository).execute(999)
