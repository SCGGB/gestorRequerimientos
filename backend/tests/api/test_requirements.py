from fastapi.testclient import TestClient

from app.api.dependencies import get_requirement_repository
from app.application.ports.requirement_repository import RequirementRepository
from app.main import create_app
from tests.application.fakes import InMemoryRequirementRepository


def _client_with_repository(repository: RequirementRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    return TestClient(app)


def test_create_requirement_returns_201() -> None:
    client = _client_with_repository(InMemoryRequirementRepository())
    response = client.post(
        "/api/v1/requerimientos",
        json={
            "folio": 1,
            "titulo": "Alta reporte",
            "tipo_cambio_id": 1,
            "sistema": "SIS",
            "version_documento": "1.0",
            "fecha_version": "2026-10-15",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["folio"] == 1
    assert body["estado"] == "BORRADOR"
    assert len(body["versiones"]) == 1


def test_list_requirements_pagination() -> None:
    repo = InMemoryRequirementRepository()
    # seed two
    from app.application.use_cases.requirement.create_requirement import (
        CreateRequirement,
    )

    uc = CreateRequirement(repo)
    uc.execute(
        folio=1,
        title="A",
        change_type_id=1,
        system="S",
        document_version="1.0",
        version_date="2026-10-15",
    )
    uc.execute(
        folio=2,
        title="B",
        change_type_id=1,
        system="S",
        document_version="1.0",
        version_date="2026-10-15",
    )
    client = _client_with_repository(repo)
    r = client.get("/api/v1/requerimientos", params={"page": 1, "size": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["size"] == 1
    assert len(data["items"]) == 1


def test_list_requirements_includes_titulo() -> None:
    repo = InMemoryRequirementRepository()
    from app.application.use_cases.requirement.create_requirement import (
        CreateRequirement,
    )

    uc = CreateRequirement(repo)
    uc.execute(
        folio=7,
        title="Titulo vigente",
        change_type_id=1,
        system="S",
        document_version="1.0",
        version_date="2026-10-15",
    )
    client = _client_with_repository(repo)
    r = client.get("/api/v1/requerimientos")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 1
    assert items[0]["titulo"] == "Titulo vigente"


def test_get_requirement_not_found() -> None:
    client = _client_with_repository(InMemoryRequirementRepository())
    r = client.get("/api/v1/requerimientos/123")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "requirement_not_found"


def test_patch_working_version_ok() -> None:
    repo = InMemoryRequirementRepository()
    from app.application.use_cases.requirement.create_requirement import (
        CreateRequirement,
    )

    uc = CreateRequirement(repo)
    req = uc.execute(
        folio=5,
        title="T",
        change_type_id=1,
        system="S",
        document_version="1.0",
        version_date="2026-10-15",
    )
    vid = req.versions[0].id
    rid = req.id
    client = _client_with_repository(repo)
    r = client.patch(
        f"/api/v1/requerimientos/{rid}/versiones/{vid}",
        json={"necesidad_actual": "N"},
    )
    assert r.status_code == 200
    assert r.json()["necesidad_actual"] == "N"


def test_folio_duplicate_409() -> None:
    repo = InMemoryRequirementRepository()
    from app.application.use_cases.requirement.create_requirement import (
        CreateRequirement,
    )

    uc = CreateRequirement(repo)
    uc.execute(
        folio=10,
        title="A",
        change_type_id=1,
        system="S",
        document_version="1.0",
        version_date="2026-10-15",
    )
    client = _client_with_repository(repo)
    r = client.post(
        "/api/v1/requerimientos",
        json={
            "folio": 10,
            "titulo": "B",
            "tipo_cambio_id": 1,
            "sistema": "S",
            "version_documento": "1.0",
            "fecha_version": "2026-10-15",
        },
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "duplicate_folio"


def test_422_on_invalid_payload() -> None:
    client = _client_with_repository(InMemoryRequirementRepository())
    r = client.post(
        "/api/v1/requerimientos",
        json={"folio": "x"},  # type: ignore[arg-type]
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
