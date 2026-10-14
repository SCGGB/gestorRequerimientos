from datetime import date

import pytest

from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.errors import (
    AuthorizationNotOnCurrentVersionError,
    InvalidFolioError,
    InvalidStateTransitionError,
    MultipleWorkingVersionsError,
)
from app.domain.requirement.items import Benefit, Objective
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion


def _version(
    number: int = 1, *, frozen: bool = False, version_id: int | None = None
) -> RequirementVersion:
    return RequirementVersion(
        number=number,
        document_version=f"{number}.0",
        version_date=date(2026, 10, 13),
        title=f"Version {number}",
        frozen=frozen,
        id=version_id,
    )


def test_ticket_uses_fixed_prefix() -> None:
    requirement = Requirement(folio=64508394)
    assert requirement.ticket == "T#64508394"


def test_invalid_folio_is_rejected() -> None:
    with pytest.raises(InvalidFolioError):
        Requirement(folio=0)


def test_only_one_working_version_allowed() -> None:
    with pytest.raises(MultipleWorkingVersionsError):
        Requirement(folio=1, versions=(_version(1), _version(2)))


def test_forward_transitions_are_allowed() -> None:
    requirement = Requirement(folio=1)
    advanced = (
        requirement.change_status(RequirementStatus.EN_REVISION)
        .change_status(RequirementStatus.VALIDADO)
        .change_status(RequirementStatus.APROBADO)
        .change_status(RequirementStatus.GENERADO)
    )
    assert advanced.status is RequirementStatus.GENERADO


def test_backward_transitions_are_allowed() -> None:
    requirement = Requirement(folio=1, status=RequirementStatus.VALIDADO)
    assert requirement.change_status(RequirementStatus.EN_REVISION).status is (
        RequirementStatus.EN_REVISION
    )

    in_review = Requirement(folio=1, status=RequirementStatus.EN_REVISION)
    assert in_review.change_status(RequirementStatus.BORRADOR).status is (
        RequirementStatus.BORRADOR
    )


def test_forbidden_transition_is_rejected() -> None:
    requirement = Requirement(folio=1)
    with pytest.raises(InvalidStateTransitionError):
        requirement.change_status(RequirementStatus.APROBADO)


def test_terminal_states_have_no_transitions() -> None:
    generated = Requirement(folio=1, status=RequirementStatus.GENERADO)
    with pytest.raises(InvalidStateTransitionError):
        generated.change_status(RequirementStatus.CANCELADO)


def test_cancel_from_non_terminal_is_allowed() -> None:
    requirement = Requirement(folio=1, status=RequirementStatus.APROBADO)
    assert requirement.change_status(RequirementStatus.CANCELADO).status is (
        RequirementStatus.CANCELADO
    )


def test_freeze_and_advance_copies_only_active_items_preserving_order() -> None:
    working = RequirementVersion(
        number=1,
        document_version="1.0",
        version_date=date(2026, 10, 13),
        title="T",
        objectives=(
            Objective(content="uno", order=1, id=10),
            Objective(content="eliminado", order=2, active=False, id=11),
            Objective(content="dos", order=3, id=12),
        ),
        benefits=(Benefit(content="cual", order=1, kind=BenefitKind.CUALITATIVO, id=20),),
    )
    requirement = Requirement(folio=1, versions=(working,))

    advanced = requirement.freeze_and_advance(
        document_version="2.0", version_date=date(2026, 10, 14), title="T2"
    )

    frozen, successor = advanced.versions
    assert frozen.frozen is True
    assert frozen is advanced.versions[0]
    assert successor.number == 2
    assert successor.frozen is False
    assert advanced.working_version() is successor
    assert advanced.current_version() is successor

    assert [item.content for item in successor.objectives] == ["uno", "dos"]
    assert [item.order for item in successor.objectives] == [1, 3]
    assert all(item.id is None for item in successor.objectives)
    assert successor.benefits[0].kind is BenefitKind.CUALITATIVO
    assert successor.benefits[0].id is None


def test_authorize_only_on_current_version() -> None:
    older = _version(1, frozen=True, version_id=1)
    current = _version(2, version_id=2)
    requirement = Requirement(
        folio=1, current_version_id=2, versions=(older, current)
    )

    with pytest.raises(AuthorizationNotOnCurrentVersionError):
        requirement.authorize(version_id=1, name="Ana", position="Analista")

    authorized = requirement.authorize(version_id=2, name="Ana", position="Analista")
    signatures = authorized.current_version().signatures
    assert len(signatures) == 1
    assert signatures[0].role is SignatureRole.AUTORIZO
    assert signatures[0].name == "Ana"


def test_current_version_falls_back_to_working_version() -> None:
    working = _version(1)
    requirement = Requirement(folio=1, versions=(working,))
    assert requirement.current_version() is working
