from __future__ import annotations

from datetime import date

import pytest

from app.application.errors import RequirementNotFoundError, VersionNotFoundError
from app.application.use_cases.requirement import ValidateRequirementVersion
from app.domain.requirement.enums import BenefitKind, RequirementStatus
from app.domain.requirement.items import (
    Benefit,
    Consideration,
    Objective,
    Restriction,
    Risk,
    Volumetry,
)
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion
from tests.application.fakes import InMemoryRequirementRepository


def _complete_version(**overrides: object) -> RequirementVersion:
    defaults: dict[str, object] = {
        "number": 1,
        "document_version": "1.0",
        "version_date": date(2026, 1, 1),
        "title": "Titulo",
        "change_type_id": 1,
        "system": "SAP",
        "current_need": "Necesidad",
        "context_description": "Contexto",
        "users_permissions": "Usuarios",
        "objectives": (Objective(content="Objetivo", order=1),),
        "considerations": (Consideration(content="Consideracion", order=1),),
        "benefits": (
            Benefit(content="Beneficio", order=1, kind=BenefitKind.CUALITATIVO),
        ),
        "restrictions": (Restriction(content="Restriccion", order=1),),
        "volumetry": (Volumetry(content="Volumetria", order=1),),
        "risks": (Risk(content="Riesgo", order=1),),
    }
    defaults.update(overrides)
    return RequirementVersion(**defaults)  # type: ignore[arg-type]


def _save_complete(
    repository: InMemoryRequirementRepository, **overrides: object
) -> Requirement:
    requirement = Requirement(folio=1, versions=(_complete_version(**overrides),))
    return repository.save(requirement)


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
        target_state=RequirementStatus.GENERADO,
    )

    codes = {issue.code for issue in result.errors}
    assert result.is_valid is False
    assert codes == {"signatures_missing"}
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR
