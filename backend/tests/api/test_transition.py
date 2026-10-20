from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import get_audit_recorder, get_requirement_repository
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.signature import Signature
from tests.api.helpers import build_app
from tests.application.fakes import FakeAuditRecorder, InMemoryRequirementRepository
from tests.factories import requirement_with


def _seed(
    repository: InMemoryRequirementRepository,
    *,
    status: RequirementStatus = RequirementStatus.BORRADOR,
    **overrides: object,
) -> int:
    requirement = repository.save(
        requirement_with(status=status, **overrides), actor="seed"
    )
    assert requirement.id is not None
    return requirement.id


def _client(
    repository: RequirementRepository,
    audit: FakeAuditRecorder | None = None,
) -> TestClient:
    app = build_app()
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_audit_recorder] = lambda: audit or FakeAuditRecorder()
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


def test_transition_with_insufficient_role_returns_403_and_state_unchanged() -> None:
    repository = InMemoryRequirementRepository()
    requirement_id = _seed(repository)
    app = build_app("REVISO")
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/requerimientos/{requirement_id}/transicionar",
        json={"a_estado": "EN_REVISION"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert (
        client.get(f"/api/v1/requerimientos/{requirement_id}").json()["estado"]
        == "BORRADOR"
    )


def test_success_audits_motivo_and_sets_updated_by() -> None:
    repository = InMemoryRequirementRepository()
    audit = FakeAuditRecorder()
    requirement_id = _seed(repository)
    client = _client(repository, audit)

    response = client.post(
        f"/api/v1/requerimientos/{requirement_id}/transicionar",
        json={"a_estado": "EN_REVISION", "motivo": "Listo para revision"},
    )

    assert response.status_code == 200
    assert repository.last_actor == "tester"
    entry = audit.find("STATE_TRANSITION")
    assert entry is not None
    assert entry.actor == "tester"
    assert entry.detail is not None
    assert entry.detail["motivo"] == "Listo para revision"


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
