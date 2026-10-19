from __future__ import annotations

from datetime import date

import pytest

from app.application.errors import RequirementNotFoundError
from app.application.use_cases.requirement import TransitionRequirementState
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


def _save(
    repository: InMemoryRequirementRepository,
    *,
    status: RequirementStatus = RequirementStatus.BORRADOR,
    **overrides: object,
) -> Requirement:
    requirement = Requirement(
        folio=1,
        status=status,
        versions=(_complete_version(**overrides),),
    )
    return repository.save(requirement)


@pytest.fixture()
def repository() -> InMemoryRequirementRepository:
    return InMemoryRequirementRepository()


def test_valid_advance_persists_new_status(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository).execute(
        saved.id, RequirementStatus.EN_REVISION.value
    )

    assert outcome.is_valid is True
    assert outcome.previous_status is RequirementStatus.BORRADOR
    assert outcome.current_status is RequirementStatus.EN_REVISION
    assert repository.get(saved.id).status is RequirementStatus.EN_REVISION


def test_skipped_transition_is_invalid_and_does_not_persist(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository).execute(
        saved.id, RequirementStatus.APROBADO.value
    )

    assert outcome.is_valid is False
    assert outcome.previous_status is RequirementStatus.BORRADOR
    assert outcome.current_status is RequirementStatus.BORRADOR
    assert [issue.code for issue in outcome.errors] == ["invalid_transition"]
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR


def test_unknown_target_state_is_rejected(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository).execute(saved.id, "NO_EXISTE")

    assert outcome.is_valid is False
    assert outcome.errors[0].code == "unknown_target_state"
    assert outcome.current_status is RequirementStatus.BORRADOR
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR


def test_advance_blocked_by_failed_validation(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save(repository, title="   ", objectives=())
    assert saved.id is not None

    outcome = TransitionRequirementState(repository).execute(
        saved.id, RequirementStatus.EN_REVISION.value
    )

    assert outcome.is_valid is False
    codes = {issue.code for issue in outcome.errors}
    assert "required_field" in codes
    assert "min_active_items" in codes
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR


def test_cancel_does_not_require_validation(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save(repository, title="", objectives=())
    assert saved.id is not None

    outcome = TransitionRequirementState(repository).execute(
        saved.id, RequirementStatus.CANCELADO.value
    )

    assert outcome.is_valid is True
    assert repository.get(saved.id).status is RequirementStatus.CANCELADO


def test_backward_transition_is_allowed_without_validation(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save(repository, status=RequirementStatus.VALIDADO, title="")
    assert saved.id is not None

    outcome = TransitionRequirementState(repository).execute(
        saved.id, RequirementStatus.EN_REVISION.value
    )

    assert outcome.is_valid is True
    assert repository.get(saved.id).status is RequirementStatus.EN_REVISION


def test_reason_and_actor_are_accepted_without_persisting(
    repository: InMemoryRequirementRepository,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository).execute(
        saved.id,
        RequirementStatus.EN_REVISION.value,
        reason="Listo para revision",
        actor_id=42,
    )

    assert outcome.is_valid is True
    assert repository.get(saved.id).status is RequirementStatus.EN_REVISION


def test_missing_requirement_raises(
    repository: InMemoryRequirementRepository,
) -> None:
    with pytest.raises(RequirementNotFoundError):
        TransitionRequirementState(repository).execute(
            999999, RequirementStatus.EN_REVISION.value
        )
