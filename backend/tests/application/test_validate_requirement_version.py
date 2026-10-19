from __future__ import annotations

import pytest

from app.application.errors import RequirementNotFoundError, VersionNotFoundError
from app.application.use_cases.requirement import ValidateRequirementVersion
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.requirement import Requirement
from tests.application.fakes import InMemoryRequirementRepository
from tests.factories import requirement_with


def _save_complete(
    repository: InMemoryRequirementRepository, **overrides: object
) -> Requirement:
    return repository.save(requirement_with(**overrides))


@pytest.fixture()
def repository() -> InMemoryRequirementRepository:
    return InMemoryRequirementRepository()


def test_validate_returns_result_without_persisting(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save_complete(repository)
    assert saved.id is not None
    version = saved.current_version()
    assert version is not None
    assert version.id is not None

    result = ValidateRequirementVersion(repository).execute(saved.id, version.id)

    assert result.is_valid is True
    assert repository.get(saved.id) == saved


def test_validate_missing_version_raises(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save_complete(repository)
    assert saved.id is not None

    with pytest.raises(VersionNotFoundError):
        ValidateRequirementVersion(repository).execute(saved.id, 999999)


def test_validate_missing_requirement_raises(
    repository: InMemoryRequirementRepository,
) -> None:
    with pytest.raises(RequirementNotFoundError):
        ValidateRequirementVersion(repository).execute(999999, 1)


def test_validate_with_target_state_checks_signatures_without_saving(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save_complete(repository)
    assert saved.id is not None
    version = saved.current_version()
    assert version is not None
    assert version.id is not None

    result = ValidateRequirementVersion(repository).execute(
        saved.id,
        version.id,
        target_state=RequirementStatus.GENERADO.value,
    )

    codes = {issue.code for issue in result.errors}
    assert result.is_valid is False
    assert codes == {"signatures_missing"}
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR


def test_validate_unknown_target_state_returns_structured_error(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save_complete(repository)
    assert saved.id is not None
    version = saved.current_version()
    assert version is not None
    assert version.id is not None

    result = ValidateRequirementVersion(repository).execute(
        saved.id,
        version.id,
        target_state="NO_EXISTE",
    )

    assert result.is_valid is False
    assert [issue.code for issue in result.errors] == ["unknown_target_state"]
    assert result.errors[0].path == "a_estado"
