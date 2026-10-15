from datetime import date

import pytest

from app.domain.requirement.collections import (
    CollectionKind,
    item_by_id,
    items_of,
    make_item,
    with_added,
    with_content_updated,
    with_deactivated,
    with_reordered,
)
from app.domain.requirement.enums import BenefitKind, RequirementStatus
from app.domain.requirement.errors import (
    RequirementNotEditableError,
    SignatureNotAllowedError,
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


def _version_with_objectives() -> RequirementVersion:
    return RequirementVersion(
        number=1,
        document_version="1.0",
        version_date=date(2026, 10, 13),
        title="T",
        objectives=(
            Objective(content="uno", order=1, id=1),
            Objective(content="dos", order=2, id=2),
            Objective(content="tres", order=3, id=3),
            Objective(content="baja", order=4, active=False, id=4),
        ),
    )


def test_version_by_id_returns_matching_or_none() -> None:
    version = _version(version_id=7)
    requirement = Requirement(folio=1, versions=(version,))
    assert requirement.version_by_id(7) is version
    assert requirement.version_by_id(99) is None


def test_ensure_editable_allows_draft_only() -> None:
    Requirement(folio=1).ensure_editable()
    for status in (
        RequirementStatus.EN_REVISION,
        RequirementStatus.VALIDADO,
        RequirementStatus.APROBADO,
        RequirementStatus.GENERADO,
        RequirementStatus.CANCELADO,
    ):
        with pytest.raises(RequirementNotEditableError):
            Requirement(folio=1, status=status).ensure_editable()


def test_ensure_working_rejects_frozen_version() -> None:
    _version(frozen=False).ensure_working()
    with pytest.raises(RequirementNotEditableError):
        _version(frozen=True).ensure_working()


def test_ensure_signable_requires_final_state_and_current_version() -> None:
    draft = Requirement(
        folio=1, current_version_id=1, versions=(_version(version_id=1),)
    )
    with pytest.raises(SignatureNotAllowedError):
        draft.ensure_signable(1)

    older = _version(1, frozen=True, version_id=1)
    current = _version(2, version_id=2)
    approved = Requirement(
        folio=1,
        status=RequirementStatus.APROBADO,
        current_version_id=2,
        versions=(older, current),
    )
    approved.ensure_signable(2)
    with pytest.raises(SignatureNotAllowedError):
        approved.ensure_signable(1)


def test_make_item_creates_typed_items() -> None:
    objective = make_item(CollectionKind.OBJETIVOS, content="objetivo", order=1)
    assert isinstance(objective, Objective)

    benefit = make_item(
        CollectionKind.BENEFICIOS,
        content="beneficio",
        order=1,
        benefit_kind=BenefitKind.CUANTITATIVO,
    )
    assert isinstance(benefit, Benefit)
    assert benefit.kind is BenefitKind.CUANTITATIVO


def test_make_item_benefit_requires_kind() -> None:
    with pytest.raises(ValueError):
        make_item(CollectionKind.BENEFICIOS, content="beneficio", order=1)


def test_items_of_includes_inactive_items() -> None:
    version = _version_with_objectives()
    assert len(items_of(version, CollectionKind.OBJETIVOS)) == 4
    assert item_by_id(version, CollectionKind.OBJETIVOS, 4).active is False
    assert item_by_id(version, CollectionKind.OBJETIVOS, 99) is None


def test_with_added_assigns_next_incremental_order() -> None:
    version = _version_with_objectives()
    added = with_added(
        version,
        CollectionKind.OBJETIVOS,
        Objective(content="cuatro", order=0),
    )
    objectives = items_of(added, CollectionKind.OBJETIVOS)
    assert objectives[-1].content == "cuatro"
    assert objectives[-1].order == 5


def test_with_content_updated_updates_or_returns_none() -> None:
    version = _version_with_objectives()
    result = with_content_updated(version, CollectionKind.OBJETIVOS, 2, "dos-edit")
    assert result is not None
    updated_version, updated_item = result
    assert updated_item.content == "dos-edit"
    assert item_by_id(updated_version, CollectionKind.OBJETIVOS, 2).content == "dos-edit"

    assert with_content_updated(version, CollectionKind.OBJETIVOS, 99, "x") is None


def test_with_deactivated_soft_deletes_keeping_the_item() -> None:
    version = _version_with_objectives()
    result = with_deactivated(version, CollectionKind.OBJETIVOS, 1)
    items = items_of(result, CollectionKind.OBJETIVOS)
    assert len(items) == 4
    assert item_by_id(result, CollectionKind.OBJETIVOS, 1).active is False


def test_with_reordered_renumbers_and_keeps_unlisted_after() -> None:
    version = _version_with_objectives()
    result = with_reordered(version, CollectionKind.OBJETIVOS, [3, 1])
    items = items_of(result, CollectionKind.OBJETIVOS)
    assert [item.content for item in items] == ["tres", "uno", "dos", "baja"]
    assert [item.order for item in items] == [1, 2, 3, 4]


def test_with_reordered_ignores_unknown_and_duplicate_ids() -> None:
    version = _version_with_objectives()
    result = with_reordered(version, CollectionKind.OBJETIVOS, [2, 99, 2])
    items = items_of(result, CollectionKind.OBJETIVOS)
    assert items[0].id == 2
    assert [item.order for item in items] == [1, 2, 3, 4]
