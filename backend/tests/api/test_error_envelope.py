from fastapi.testclient import TestClient

from app.api.dependencies import get_requirement_repository
from app.main import create_app
from tests.application.fakes import InMemoryRequirementRepository


def test_error_envelope_structure() -> None:
    app = create_app()
    app.dependency_overrides[get_requirement_repository] = lambda: InMemoryRequirementRepository()
    client = TestClient(app)
    r = client.get("/api/v1/requerimientos/999")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]


def test_openapi_has_endpoints() -> None:
    client = TestClient(create_app())
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/v1/requerimientos" in paths
    assert "/api/v1/catalogos/tipos-cambio" in paths
    assert "/api/v1/catalogos/cargos" in paths
