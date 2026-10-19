from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.api.dependencies import get_requirement_repository
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.items import (
    Benefit,
    Consideration,
    Objective,
    Restriction,
    Risk,
    Volumetry,
)
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
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
    repository: InMemoryRequirementRepository,
    *,
    status: RequirementStatus = RequirementStatus.BORRADOR,
    **overrides: object,
) -> int:
    requirement = repository.save(
        Requirement(
            folio=1,
            status=status,
            versions=(_complete_version(**overrides),),
        )
    )
    assert requirement.id is not None
    return requirement.id


def _client(repository: RequirementRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    return TestClient(app)


def test_valid_transition_returns_200_and_persists() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id = _seed(repository)
    client = _client(repository)

    response = client.post(
        f"/api/v1/requerimientos/{requirement_id}/transicionar",
        json={"a_estado": "EN_REVISION"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["estado_anterior"] == "BORRADOR"
    assert body["estado_actual"] == "EN_REVISION"
    assert body["transicion_valida"] is True
    detail = client.get(f"/api/v1/requerimientos/{requirement_id}")
    assert detail.json()["estado"] == "EN_REVISION"


def test_forbidden_transition_returns_400_with_body() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id = _seed(repository)
    client = _client(repository)

    response = client.post(
        f"/api/v1/requerimientos/{requirement_id}/transicionar",
        json={"a_estado": "APROBADO"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["transicion_valida"] is False
    assert body["estado_actual"] == "BORRADOR"
    assert body["errores"][0]["codigo"] == "invalid_transition"
    assert client.get(f"/api/v1/requerimientos/{requirement_id}").json()[
        "estado"
    ] == "BORRADOR"


def test_unknown_target_state_returns_400() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id = _seed(repository)

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/transicionar",
        json={"a_estado": "NO_EXISTE"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["transicion_valida"] is False
    assert body["errores"][0]["codigo"] == "unknown_target_state"


def test_transition_to_generado_requires_signatures() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id = _seed(repository, status=RequirementStatus.APROBADO)

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/transicionar",
        json={"a_estado": "GENERADO"},
    )

    assert response.status_code == 400
    body = response.json()
    codes = {error["codigo"] for error in body["errores"]}
    assert codes == {"signatures_missing"}


def test_transition_to_generado_with_signatures_succeeds() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id = _seed(
        repository,
        status=RequirementStatus.APROBADO,
        signatures=(
            Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista"),
            Signature(role=SignatureRole.AUTORIZO, name="Luis", position="Gerente"),
        ),
    )

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/transicionar",
        json={"a_estado": "GENERADO"},
    )

    assert response.status_code == 200
    assert response.json()["estado_actual"] == "GENERADO"


def test_transition_missing_requirement_returns_404() -> None:
    repository = InMemoryRequirementRepository()

    response = _client(repository).post(
        "/api/v1/requerimientos/999999/transicionar",
        json={"a_estado": "EN_REVISION"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "requirement_not_found"


def test_legacy_status_endpoint_keeps_409() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id = _seed(repository)

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/estado",
        json={"nuevo_estado": "APROBADO"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_state_transition"
