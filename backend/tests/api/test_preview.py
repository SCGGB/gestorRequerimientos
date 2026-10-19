from datetime import date

from fastapi.testclient import TestClient

from app.api.dependencies import get_requirement_repository
from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement.create_requirement import CreateRequirement
from app.main import create_app
from tests.application.fakes import InMemoryRequirementRepository


def _client_with_repository(repository: RequirementRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    return TestClient(app)


def _seed(repo: InMemoryRequirementRepository, folio: int = 1) -> tuple[int, int]:
    requirement = CreateRequirement(repo).execute(
        folio=folio,
        title="Gestion de contratos",
        change_type_id=1,
        system="SAP",
        document_version="1.0",
        version_date=date(2026, 10, 15),
    )
    assert requirement.id is not None
    version = requirement.versions[0]
    assert version.id is not None
    return requirement.id, version.id


def test_preview_returns_document_contract() -> None:
    repo = InMemoryRequirementRepository()
    requirement_id, version_id = _seed(repo, folio=5)
    client = _client_with_repository(repo)
    client.patch(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}",
        json={"necesidad_actual": "Necesidad", "requisitos_futuros_aplica": False},
    )

    response = client.get(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/vista-previa"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["folio"] == 5
    assert body["ticket"] == "T#5"
    assert body["titulo"] == "Gestion de contratos"
    assert body["version_documento"] == "1.0"
    assert body["fecha_version"] == "15-10-2026"
    assert [section["numero"] for section in body["secciones"]] == [
        "1",
        "2",
        "3",
        "4",
        "4.1",
        "4.2",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
    ]
    necesidad = body["secciones"][0]
    assert necesidad["codigo"] == "necesidad_actual"
    assert necesidad["bloques"][0] == {"tipo": "parrafo", "texto": "Necesidad", "items": None}

    objetivos = body["secciones"][1]
    assert objetivos["bloques"][0]["tipo"] == "no_aplica"
    assert objetivos["bloques"][0]["texto"] == "No aplica"

    futuros = next(
        section for section in body["secciones"] if section["codigo"] == "requisitos_futuros"
    )
    assert futuros["bloques"][0]["texto"] == "No Aplica."

    assert len(body["control_versiones"]) == 1
    row = body["control_versiones"][0]
    assert row["version"] == "1.0"
    assert row["fecha"] == "15-10-2026"
    assert row["descripcion_cambio"] is None
    assert body["firmas"] == {"elaboro": None, "reviso": None, "autorizo": None}


def test_preview_requirement_not_found() -> None:
    client = _client_with_repository(InMemoryRequirementRepository())

    response = client.get("/api/v1/requerimientos/999/versiones/1/vista-previa")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "requirement_not_found"


def test_preview_version_not_found() -> None:
    repo = InMemoryRequirementRepository()
    requirement_id, _ = _seed(repo)
    client = _client_with_repository(repo)

    response = client.get(
        f"/api/v1/requerimientos/{requirement_id}/versiones/999/vista-previa"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "version_not_found"


def test_preview_is_read_only() -> None:
    repo = InMemoryRequirementRepository()
    requirement_id, version_id = _seed(repo)
    client = _client_with_repository(repo)

    before = client.get(f"/api/v1/requerimientos/{requirement_id}").json()
    client.get(
        f"/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/vista-previa"
    )
    after = client.get(f"/api/v1/requerimientos/{requirement_id}").json()

    assert before["estado"] == after["estado"]
    assert len(before["versiones"]) == len(after["versiones"])
    assert after["versiones"][0]["firmas"] == []
