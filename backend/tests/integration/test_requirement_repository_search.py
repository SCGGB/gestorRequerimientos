from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from sqlalchemy.engine import Engine

from app.application.errors import DuplicateFolioError
from app.application.ports.requirement_repository import RequirementSearchFilters
from app.domain.requirement.attachment import Attachment
from app.domain.requirement.collections import (
    CollectionKind,
    with_content_updated,
    with_reordered,
)
from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.items import Objective
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion
from app.infrastructure.adapters.requirement_repository import (
    SqlAlchemyRequirementRepository,
)

pytestmark = pytest.mark.integration

FOLIO_PAGE = 810001
FOLIO_STATUS = 810010
FOLIO_DUPLICATE = 810020
FOLIO_STABLE_IDS = 810030
FOLIO_REORDER = 810040


def _requirement(
    folio: int,
    *,
    status: RequirementStatus = RequirementStatus.BORRADOR,
) -> Requirement:
    version = RequirementVersion(
        number=1,
        document_version="1.0",
        version_date=date(2026, 10, 14),
        title=f"Requerimiento {folio}",
        system="Sistema de busqueda",
        objectives=(
            Objective(content="Objetivo A", order=1),
            Objective(content="Objetivo B", order=2),
        ),
        signatures=(
            Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista"),
        ),
        attachments=(
            Attachment(
                name="anexo1.pdf",
                order=1,
                storage_key="objects/anexo1.pdf",
                mime_type="application/pdf",
            ),
            Attachment(
                name="anexo2.pdf",
                order=2,
                storage_key="objects/anexo2.pdf",
                mime_type="application/pdf",
            ),
        ),
    )
    requirement = Requirement(folio=folio, versions=(version,))
    if status is not RequirementStatus.BORRADOR:
        requirement = requirement.change_status(status)
    return requirement


@pytest.fixture()
def repository(migrated_engine: Engine) -> SqlAlchemyRequirementRepository:
    return SqlAlchemyRequirementRepository(migrated_engine)


def test_search_without_filters_and_pagination(
    repository: SqlAlchemyRequirementRepository,
) -> None:
    baseline = len(repository.list())
    for folio in (FOLIO_PAGE, FOLIO_PAGE + 1, FOLIO_PAGE + 2):
        repository.save(_requirement(folio), actor="tester")

    items, total = repository.search(RequirementSearchFilters(), offset=0, limit=1000)

    assert total == baseline + 3
    assert {item.folio for item in items} >= {FOLIO_PAGE, FOLIO_PAGE + 1, FOLIO_PAGE + 2}
    ids = [int(item.id) for item in items]
    assert ids == sorted(ids)

    page, page_total = repository.search(RequirementSearchFilters(), offset=0, limit=2)
    assert page_total == total
    assert len(page) == 2
    assert {item.id for item in page}.isdisjoint({item.id for item in items[2:]})

    tail, tail_total = repository.search(
        RequirementSearchFilters(), offset=total - 2, limit=2
    )
    assert tail_total == total
    assert [item.folio for item in tail] == [FOLIO_PAGE + 1, FOLIO_PAGE + 2]

    beyond, beyond_total = repository.search(
        RequirementSearchFilters(), offset=total + 10, limit=5
    )
    assert beyond == ()
    assert beyond_total == total


def test_search_filters_by_status_and_folio(
    repository: SqlAlchemyRequirementRepository,
) -> None:
    repository.save(
        _requirement(FOLIO_STATUS, status=RequirementStatus.EN_REVISION),
        actor="tester",
    )

    by_folio, folio_total = repository.search(
        RequirementSearchFilters(folio=FOLIO_STATUS), offset=0, limit=10
    )
    assert folio_total == 1
    assert by_folio[0].status is RequirementStatus.EN_REVISION

    both, both_total = repository.search(
        RequirementSearchFilters(status=RequirementStatus.EN_REVISION, folio=FOLIO_STATUS),
        offset=0,
        limit=10,
    )
    assert both_total == 1
    assert both[0].folio == FOLIO_STATUS

    by_status, _ = repository.search(
        RequirementSearchFilters(status=RequirementStatus.EN_REVISION), offset=0, limit=1000
    )
    assert [item.folio for item in by_status] == [FOLIO_STATUS]

    missed, missed_total = repository.search(
        RequirementSearchFilters(status=RequirementStatus.BORRADOR, folio=FOLIO_STATUS),
        offset=0,
        limit=10,
    )
    assert missed_total == 0
    assert missed == ()


def test_duplicate_folio_is_translated_to_application_error(
    repository: SqlAlchemyRequirementRepository,
) -> None:
    repository.save(_requirement(FOLIO_DUPLICATE), actor="tester")

    with pytest.raises(DuplicateFolioError):
        repository.save(_requirement(FOLIO_DUPLICATE), actor="tester")


def test_child_ids_are_stable_across_writes(
    repository: SqlAlchemyRequirementRepository,
) -> None:
    saved = repository.save(_requirement(FOLIO_STABLE_IDS), actor="tester")
    version = saved.versions[0]
    objective_ids = [item.id for item in version.objectives]
    signature_ids = [item.id for item in version.signatures]
    attachment_ids = [item.id for item in version.attachments]
    assert all(item_id is not None for item_id in objective_ids)
    assert all(item_id is not None for item_id in signature_ids)
    assert all(item_id is not None for item_id in attachment_ids)

    updated = with_content_updated(
        version, CollectionKind.OBJETIVOS, int(objective_ids[0]), "Objetivo A editado"
    )
    assert updated is not None
    edited_version, edited_item = updated

    reloaded = repository.save(replace(saved, versions=(edited_version,)), actor="tester")
    reloaded_version = reloaded.versions[0]

    assert [item.id for item in reloaded_version.objectives] == objective_ids
    assert [item.id for item in reloaded_version.signatures] == signature_ids
    assert [item.id for item in reloaded_version.attachments] == attachment_ids
    assert edited_item.id == objective_ids[0]
    assert reloaded_version.objectives[0].content == "Objetivo A editado"


def test_reorder_keeps_ids_and_avoids_unique_constraint(
    repository: SqlAlchemyRequirementRepository,
) -> None:
    saved = repository.save(_requirement(FOLIO_REORDER), actor="tester")
    version = saved.versions[0]
    objective_ids = [int(item.id) for item in version.objectives]
    attachment_ids = [int(item.id) for item in version.attachments]

    reordered = with_reordered(
        version, CollectionKind.OBJETIVOS, [objective_ids[1], objective_ids[0]]
    )
    first, second = version.attachments
    reordered = replace(
        reordered,
        attachments=(
            replace(second, order=first.order),
            replace(first, order=second.order),
        ),
    )

    reloaded = repository.save(replace(saved, versions=(reordered,)), actor="tester")
    reloaded_version = reloaded.versions[0]

    assert sorted(int(item.id) for item in reloaded_version.objectives) == sorted(
        objective_ids
    )
    assert [item.id for item in reloaded_version.objectives] == list(
        reversed(objective_ids)
    )
    assert [item.content for item in reloaded_version.objectives] == [
        "Objetivo B",
        "Objetivo A",
    ]
    assert [item.id for item in reloaded_version.attachments] == list(
        reversed(attachment_ids)
    )
    assert [item.name for item in reloaded_version.attachments] == [
        "anexo2.pdf",
        "anexo1.pdf",
    ]
