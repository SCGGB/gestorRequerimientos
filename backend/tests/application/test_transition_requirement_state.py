from __future__ import annotations

import pytest

from app.application.errors import RequirementNotFoundError
from app.application.ports.auth import Principal
from app.application.use_cases.requirement import TransitionRequirementState
from app.domain.auth.audit import AuditAction
from app.domain.auth.errors import AccessDeniedError
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.requirement import Requirement
from tests.application.fakes import (
    FakeAuditRecorder,
    InMemoryRequirementRepository,
)
from tests.factories import requirement_with

_PRINCIPAL = Principal(
    user_id="tester",
    roles=frozenset({"ELABORO", "REVISO", "AUTORIZO", "ADMIN"}),
)


def _save(
    repository: InMemoryRequirementRepository,
    *,
    status: RequirementStatus = RequirementStatus.BORRADOR,
    **overrides: object,
) -> Requirement:
    return repository.save(requirement_with(status=status, **overrides), actor="seed")


@pytest.fixture()
def repository() -> InMemoryRequirementRepository:
    return InMemoryRequirementRepository()


@pytest.fixture()
def audit() -> FakeAuditRecorder:
    return FakeAuditRecorder()


def test_valid_advance_persists_new_status(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository, audit).execute(
        saved.id,
        RequirementStatus.EN_REVISION.value,
        principal=_PRINCIPAL,
    )

    assert outcome.is_valid is True
    assert outcome.previous_status is RequirementStatus.BORRADOR
    assert outcome.current_status is RequirementStatus.EN_REVISION
    assert repository.get(saved.id).status is RequirementStatus.EN_REVISION
    assert repository.last_actor == "tester"


def test_role_denied_transition_keeps_state(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    reviser = Principal(user_id="revisor", roles=frozenset({"REVISO"}))

    with pytest.raises(AccessDeniedError):
        TransitionRequirementState(repository, audit).execute(
            saved.id,
            RequirementStatus.EN_REVISION.value,
            principal=reviser,
        )

    assert repository.get(saved.id).status is RequirementStatus.BORRADOR
    assert audit.entries == []


def test_skipped_transition_is_invalid_and_does_not_persist(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository, audit).execute(
        saved.id,
        RequirementStatus.APROBADO.value,
        principal=_PRINCIPAL,
    )

    assert outcome.is_valid is False
    assert outcome.previous_status is RequirementStatus.BORRADOR
    assert outcome.current_status is RequirementStatus.BORRADOR
    assert [issue.code for issue in outcome.errors] == ["invalid_transition"]
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR


def test_unknown_target_state_is_rejected(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository, audit).execute(
        saved.id, "NO_EXISTE", principal=_PRINCIPAL
    )

    assert outcome.is_valid is False
    assert outcome.errors[0].code == "unknown_target_state"
    assert outcome.current_status is RequirementStatus.BORRADOR
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR


def test_advance_blocked_by_failed_validation(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository, title="   ", objectives=())
    assert saved.id is not None

    outcome = TransitionRequirementState(repository, audit).execute(
        saved.id,
        RequirementStatus.EN_REVISION.value,
        principal=_PRINCIPAL,
    )

    assert outcome.is_valid is False
    codes = {issue.code for issue in outcome.errors}
    assert "required_field" in codes
    assert "min_active_items" in codes
    assert repository.get(saved.id).status is RequirementStatus.BORRADOR


def test_cancel_does_not_require_validation(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository, title="", objectives=())
    assert saved.id is not None

    outcome = TransitionRequirementState(repository, audit).execute(
        saved.id,
        RequirementStatus.CANCELADO.value,
        principal=_PRINCIPAL,
    )

    assert outcome.is_valid is True
    assert repository.get(saved.id).status is RequirementStatus.CANCELADO


def test_backward_transition_is_allowed_without_validation(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository, status=RequirementStatus.VALIDADO, title="")
    assert saved.id is not None

    outcome = TransitionRequirementState(repository, audit).execute(
        saved.id,
        RequirementStatus.EN_REVISION.value,
        principal=_PRINCIPAL,
    )

    assert outcome.is_valid is True
    assert repository.get(saved.id).status is RequirementStatus.EN_REVISION


def test_success_audits_real_actor_and_reason(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    saved = _save(repository)
    assert saved.id is not None

    outcome = TransitionRequirementState(repository, audit).execute(
        saved.id,
        RequirementStatus.EN_REVISION.value,
        principal=_PRINCIPAL,
        reason="Listo para revision",
    )

    assert outcome.is_valid is True
    assert repository.get(saved.id).status is RequirementStatus.EN_REVISION

    entry = audit.find(AuditAction.STATE_TRANSITION.value)
    assert entry is not None
    assert entry.actor == "tester"
    assert entry.entity == "REQ_REQUERIMIENTO"
    assert entry.entity_id == saved.id
    assert entry.detail is not None
    assert entry.detail["estado_anterior"] == RequirementStatus.BORRADOR.value
    assert entry.detail["estado_actual"] == RequirementStatus.EN_REVISION.value
    assert entry.detail["motivo"] == "Listo para revision"


def test_missing_requirement_raises(
    repository: InMemoryRequirementRepository,
    audit: FakeAuditRecorder,
) -> None:
    with pytest.raises(RequirementNotFoundError):
        TransitionRequirementState(repository, audit).execute(
            999999, RequirementStatus.EN_REVISION.value, principal=_PRINCIPAL
        )
