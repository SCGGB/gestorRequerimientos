from __future__ import annotations

from datetime import date

import pytest

from app.application.errors import RequirementNotFoundError, VersionNotFoundError
from app.application.use_cases.requirement import (
    BuildPreviewDocument,
    CreateRequirement,
    FreezeAndAdvance,
)
from app.domain.requirement.requirement import Requirement
from tests.application.fakes import InMemoryRequirementRepository

_VERSION_DATE = date(2026, 1, 1)


class RecordingRepository(InMemoryRequirementRepository):
    """Repositorio en memoria que cuenta las llamadas a ``save``."""

    def __init__(self) -> None:
        super().__init__()
        self.save_calls = 0

    def save(self, requirement: Requirement) -> Requirement:
        self.save_calls += 1
        return super().save(requirement)


@pytest.fixture()
def repository() -> RecordingRepository:
    return RecordingRepository()


def _create(repository: RecordingRepository, folio: int = 1) -> Requirement:
    return CreateRequirement(repository).execute(
        folio=folio,
        title="Gestion de contratos",
        change_type_id=1,
        system="SAP",
        document_version="1.0",
        version_date=_VERSION_DATE,
    )


def test_returns_preview_of_requested_version(
    repository: RecordingRepository,
) -> None:
    requirement = _create(repository, folio=5)
    version = requirement.current_version()
    assert version is not None and version.id is not None
    assert requirement.id is not None

    document = BuildPreviewDocument(repository).execute(requirement.id, version.id)

    assert document.folio == 5
    assert document.ticket == "T#5"
    assert document.title == "Gestion de contratos"
    assert document.document_version == "1.0"
    assert document.version_date == "01-01-2026"


def test_missing_requirement_raises_not_found(
    repository: RecordingRepository,
) -> None:
    with pytest.raises(RequirementNotFoundError):
        BuildPreviewDocument(repository).execute(999, 1)


def test_missing_version_raises_not_found(
    repository: RecordingRepository,
) -> None:
    requirement = _create(repository)
    assert requirement.id is not None

    with pytest.raises(VersionNotFoundError):
        BuildPreviewDocument(repository).execute(requirement.id, 999)


def test_preview_is_read_only(repository: RecordingRepository) -> None:
    requirement = _create(repository)
    version = requirement.current_version()
    assert version is not None and version.id is not None
    assert requirement.id is not None
    saves_before = repository.save_calls

    BuildPreviewDocument(repository).execute(requirement.id, version.id)

    assert repository.save_calls == saves_before


def test_version_control_lists_all_versions_ordered(
    repository: RecordingRepository,
) -> None:
    requirement = _create(repository)
    assert requirement.id is not None
    advanced = FreezeAndAdvance(repository).execute(
        requirement.id,
        document_version="2.0",
        version_date=date(2026, 2, 10),
    )
    working = advanced.current_version()
    assert working is not None and working.id is not None

    document = BuildPreviewDocument(repository).execute(requirement.id, working.id)

    assert [row.document_version for row in document.version_control] == ["1.0", "2.0"]
    assert [row.date for row in document.version_control] == [
        "01-01-2026",
        "10-02-2026",
    ]
    assert all(row.change_description is None for row in document.version_control)
    assert document.signatures.prepared_by is None
    assert document.signatures.reviewed_by is None
    assert document.signatures.authorized_by is None
