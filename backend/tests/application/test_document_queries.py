from __future__ import annotations

import pytest

from app.application.errors import DocumentNotFoundError, RequirementNotFoundError
from app.application.use_cases.requirement import (
    GenerateRequirementDocuments,
    GetRequirementDocument,
    ListRequirementDocuments,
)
from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from tests.application.fakes import (
    FakeDocumentConverter,
    FakeDocumentRenderer,
    InMemoryRequirementDocumentRepository,
    InMemoryRequirementRepository,
)
from tests.factories import complete_version


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
    requirement_id: int,
) -> None:
    GenerateRequirementDocuments(
        repository,
        document_repository,
        FakeDocumentRenderer(),
        FakeDocumentConverter(),
        template_version="v1",
    ).execute(requirement_id)


def test_get_document_returns_content() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = repository.save(_signed_requirement(1))
    assert requirement.id is not None
    _generate(repository, document_repository, requirement.id)
    document_id = document_repository.list_by_requirement(requirement.id)[0].id
    assert document_id is not None

    document = GetRequirementDocument(repository, document_repository).execute(
        requirement.id, document_id
    )

    assert document.content is not None


def test_get_document_not_belonging_to_requirement_raises_not_found() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = repository.save(_signed_requirement(1))
    other = repository.save(_signed_requirement(2))
    assert requirement.id is not None and other.id is not None
    _generate(repository, document_repository, requirement.id)
    document_id = document_repository.list_by_requirement(requirement.id)[0].id
    assert document_id is not None

    with pytest.raises(DocumentNotFoundError):
        GetRequirementDocument(repository, document_repository).execute(
            other.id, document_id
        )


def test_list_documents_returns_history_without_content() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = repository.save(_signed_requirement(1))
    assert requirement.id is not None
    _generate(repository, document_repository, requirement.id)

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
