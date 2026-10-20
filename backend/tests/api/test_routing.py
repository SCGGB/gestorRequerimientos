from fastapi.testclient import TestClient

from app.api.dependencies import get_audit_recorder, get_requirement_repository
from app.application.ports.auth import Principal
from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement.create_requirement import CreateRequirement
from tests.api.helpers import build_app
from tests.application.fakes import FakeAuditRecorder, InMemoryRequirementRepository

TESTER = Principal(user_id="tester", roles=frozenset({"ELABORO", "ADMIN"}))


def _client(repository: RequirementRepository) -> TestClient:
    app = build_app()
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    return TestClient(app)


def _seed() -> tuple[InMemoryRequirementRepository, int, int]:
    repository = InMemoryRequirementRepository()
    requirement = CreateRequirement(repository, FakeAuditRecorder()).execute(
        principal=TESTER,
        folio=1,
        title="Titulo",
        change_type_id=1,
        system="SAP",
        document_version="1.0",
        version_date="2026-01-01",
    )
    assert requirement.id is not None
    version = requirement.current_version()
    assert version is not None
    assert version.id is not None
    return repository, requirement.id, version.id


def test_signature_route_is_not_shadowed_by_collections() -> None:
    repository, requirement_id, version_id = _seed()

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/firmas",
        json={"rol": "ELABORO", "nombre": "Ana", "cargo": "Analista"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "signature_not_allowed"


def test_attachment_route_is_not_shadowed_by_collections() -> None:
    repository, requirement_id, version_id = _seed()

    response = _client(repository).post(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/anexos",
        json={"nombre": "anexo.pdf", "storage_key": "objects/anexo.pdf"},
    )

    assert response.status_code == 201
    assert response.json()["nombre"] == "anexo.pdf"
