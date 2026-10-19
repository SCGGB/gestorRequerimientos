from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.api.dependencies import get_requirement_repository
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import BenefitKind
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
from app.main import create_app
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


def _seed(
    repository: InMemoryRequirementRepository, **overrides: object
) -> tuple[int, int]:
    requirement = repository.save(
        Requirement(folio=1, versions=(_complete_version(**overrides),))
    )
    assert requirement.id is not None
    version = requirement.current_version()
    assert version is not None
    assert version.id is not None
    return requirement.id, version.id


def _client(repository: RequirementRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    return TestClient(app)


def test_validation_reports_errors_by_section() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id, version_id = _seed(
        repository, title="  ", current_need=None, objectives=()
    )

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/validar"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valido"] is False
    paths = {error["path"] for error in body["errores"]}
    assert "datos_generales.titulo" in paths
    assert "necesidad_actual" in paths
    assert "objetivos" in paths
    for error in body["errores"]:
        assert set(error) == {"path", "codigo", "mensaje", "seccion"}


def test_validation_returns_valid_for_complete_version() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id, version_id = _seed(repository)

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/validar"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valido"] is True
    assert body["errores"] == []


def test_validation_future_requirements_not_applying_has_no_errors() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id, version_id = _seed(
        repository, future_requirements_applies=False
    )

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/validar"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valido"] is True


def test_validation_future_requirements_applying_requires_content() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id, version_id = _seed(
        repository,
        future_requirements_applies=True,
        future_requirements_text=None,
        future_requirements_items=(),
    )

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/validar"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valido"] is False
    assert any(
        error["codigo"] == "future_requirements_missing"
        and error["seccion"] == "Requisitos futuros"
        for error in body["errores"]
    )


def test_validation_does_not_change_state() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id, version_id = _seed(repository)
    client = _client(repository)

    client.post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/validar"
    )
    detail = client.get(f"/api/v1/requerimientos/{requirement_id}")

    assert detail.status_code == 200
    assert detail.json()["estado"] == "BORRADOR"


def test_validation_missing_requirement_returns_404() -> None:
    repository = InMemoryRequirementRepository()

    response = _client(repository).post(
        "/api/v1/requerimientos/999999/versiones/1/validar"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "requirement_not_found"


def test_validation_missing_version_returns_404() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id, _ = _seed(repository)

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/999999/validar"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "version_not_found"
