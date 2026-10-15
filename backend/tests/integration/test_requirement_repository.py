from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from sqlalchemy.engine import Engine

from app.application.errors import DataConflictError, DuplicateFolioError
from app.domain.requirement.attachment import Attachment
from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.items import Benefit, Objective, Risk
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion
from app.infrastructure.adapters.requirement_repository import (
    SqlAlchemyRequirementRepository,
)
from app.infrastructure.db import mappers

pytestmark = pytest.mark.integration


@pytest.fixture()
def repository(migrated_engine: Engine) -> SqlAlchemyRequirementRepository:
    return SqlAlchemyRequirementRepository(migrated_engine)


def _full_requirement(folio: int) -> Requirement:
    version = RequirementVersion(
        number=1,
        document_version="1.0",
        version_date=date(2026, 10, 13),
        title="Requerimiento completo",
        system="Sistema de prueba",
        current_need="Necesidad",
        context_description="Contexto",
        context_error_handling="Manejo de errores",
        users_permissions="Usuarios y permisos",
        future_requirements_applies=True,
        future_requirements_text="Requisitos futuros",
        dynamic_fields={"prioridad": "alta", "esfuerzo": 5},
        objectives=(
            Objective(content="Objetivo uno", order=1),
            Objective(content="Objetivo dos", order=2),
        ),
        benefits=(
            Benefit(content="Beneficio cualitativo", order=1, kind=BenefitKind.CUALITATIVO),
            Benefit(content="Beneficio cuantitativo", order=2, kind=BenefitKind.CUANTITATIVO),
        ),
        risks=(Risk(content="Riesgo uno", order=1),),
        signatures=(
            Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista"),
            Signature(role=SignatureRole.REVISO, name="Luis", position="Lider"),
        ),
        attachments=(
            Attachment(
                name="anexo.pdf",
                order=1,
                storage_key="objects/anexo.pdf",
                mime_type="application/pdf",
                caption="Anexo de soporte",
            ),
        ),
    )
    return Requirement(folio=folio, versions=(version,))


def test_saves_and_loads_full_aggregate(repository: SqlAlchemyRequirementRepository) -> None:
    saved = repository.save(_full_requirement(800001))

    assert saved.id is not None
    assert saved.current_version_id is not None
    assert saved.current_version_id == saved.versions[0].id

    loaded = repository.get(saved.id)
    assert loaded == saved

    version = loaded.versions[0]
    assert [objective.content for objective in version.objectives] == [
        "Objetivo uno",
        "Objetivo dos",
    ]
    assert [benefit.kind for benefit in version.benefits] == [
        BenefitKind.CUALITATIVO,
        BenefitKind.CUANTITATIVO,
    ]
    assert version.dynamic_fields == {"prioridad": "alta", "esfuerzo": 5}
    assert {signature.role for signature in version.signatures} == {
        SignatureRole.ELABORO,
        SignatureRole.REVISO,
    }
    assert version.attachments[0].storage_key == "objects/anexo.pdf"
    assert version.attachments[0].caption == "Anexo de soporte"
    assert loaded.status is RequirementStatus.BORRADOR


def test_get_by_folio_and_list(repository: SqlAlchemyRequirementRepository) -> None:
    saved = repository.save(_full_requirement(800002))

    assert repository.get_by_folio(800002) == saved
    assert repository.get_by_folio(999999) is None
    assert any(item.folio == 800002 for item in repository.list())


def test_updates_existing_requirement(repository: SqlAlchemyRequirementRepository) -> None:
    saved = repository.save(_full_requirement(800003))
    updated_version = replace(saved.versions[0], title="Titulo actualizado")
    updated = replace(saved, versions=(updated_version,))

    persisted = repository.save(updated)

    assert persisted.id == saved.id
    assert persisted.versions[0].title == "Titulo actualizado"


def test_duplicate_folio_is_rejected(repository: SqlAlchemyRequirementRepository) -> None:
    repository.save(_full_requirement(800004))

    with pytest.raises(DuplicateFolioError):
        repository.save(_full_requirement(800004))


def test_invalid_dynamic_fields_json_is_rejected(
    repository: SqlAlchemyRequirementRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mappers, "dynamic_fields_to_json", lambda fields: "no-es-json")

    with pytest.raises(DataConflictError):
        repository.save(_full_requirement(800005))
