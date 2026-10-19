from __future__ import annotations

import pytest

from app.application.errors import DocumentGenerationNotAllowedError
from app.application.use_cases.requirement import GenerateRequirementDocuments
from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.errors import InvalidStateTransitionError
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion
from tests.application.fakes import (
    FakeDocumentConverter,
    FakeDocumentRenderer,
    InMemoryRequirementDocumentRepository,
    InMemoryRequirementRepository,
)
from tests.factories import complete_version


def _signed_version() -> RequirementVersion:
    version = complete_version()
    version = version.with_signature(
        Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista")
    )
    return version.with_signature(
        Signature(role=SignatureRole.AUTORIZO, name="Luis", position="Gerente")
    )


def _save(repository: InMemoryRequirementRepository, status: RequirementStatus) -> Requirement:
    requirement = Requirement(
        folio=1,
        status=status,
        versions=(_signed_version(),),
    )
    return repository.save(requirement)


def _use_case(
    repository: InMemoryRequirementRepository,
    document_repository: InMemoryRequirementDocumentRepository,
) -> GenerateRequirementDocuments:
    return GenerateRequirementDocuments(
        repository,
        document_repository,
        FakeDocumentRenderer(),
        FakeDocumentConverter(),
        template_version="v1",
    )


def test_generates_docx_and_pdf_and_transitions_to_generated() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = _save(repository, RequirementStatus.APROBADO)
    assert requirement.id is not None

    documents = _use_case(repository, document_repository).execute(requirement.id)

    assert {document.format for document in documents} == {"DOCX", "PDF"}
    assert all(document.id is not None for document in documents)
    assert all(document.content is None for document in documents)
    assert {document.file_name for document in documents} == {
        "T#1-v1.0.docx",
        "T#1-v1.0.pdf",
    }
    assert all(document.template_version == "v1" for document in documents)
    assert all(document.generated_by == "SYSTEM" for document in documents)
    assert repository.get(requirement.id).status is RequirementStatus.GENERADO


def test_state_not_allowed_is_rejected_without_records() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = _save(repository, RequirementStatus.BORRADOR)
    assert requirement.id is not None

    with pytest.raises(InvalidStateTransitionError):
        _use_case(repository, document_repository).execute(requirement.id)

    assert repository.get(requirement.id).status is RequirementStatus.BORRADOR
    assert not document_repository.list_by_requirement(requirement.id)


def test_missing_signatures_are_rejected_without_records() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = repository.save(
        Requirement(folio=1, status=RequirementStatus.APROBADO, versions=(complete_version(),))
    )
    assert requirement.id is not None

    with pytest.raises(DocumentGenerationNotAllowedError):
        _use_case(repository, document_repository).execute(requirement.id)

    assert repository.get(requirement.id).status is RequirementStatus.APROBADO
    assert not document_repository.list_by_requirement(requirement.id)


def test_regeneration_adds_documents_without_overwriting() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = _save(repository, RequirementStatus.APROBADO)
    assert requirement.id is not None
    use_case = _use_case(repository, document_repository)

    first = use_case.execute(requirement.id)
    second = use_case.execute(requirement.id)

    history = document_repository.list_by_requirement(requirement.id)
    assert len(history) == 4
    assert {document.id for document in first}.isdisjoint(
        {document.id for document in second}
    )
    assert repository.get(requirement.id).status is RequirementStatus.GENERADO
