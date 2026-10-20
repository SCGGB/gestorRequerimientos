from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_audit_recorder,
    get_auth_provider,
    get_check_health_use_case,
    get_document_converter,
    get_document_renderer,
    get_requirement_document_repository,
    get_requirement_repository,
)
from app.application.ports.auth import AuthProvider, Principal
from app.application.ports.database_health import DatabaseHealthPort
from app.application.use_cases.check_health import CheckHealthUseCase
from app.domain.health import DatabaseStatus
from app.main import create_app
from tests.api.helpers import build_app
from tests.application.fakes import (
    FakeAuditRecorder,
    FakeDocumentConverter,
    FakeDocumentRenderer,
    InMemoryRequirementDocumentRepository,
    InMemoryRequirementRepository,
)
from tests.factories import requirement_with


class _NullAuthProvider(AuthProvider):
    def current_principal(self) -> Principal | None:
        return None


class _FakeHealthPort(DatabaseHealthPort):
    def check(self) -> DatabaseStatus:
        return DatabaseStatus.OK


def _enforcement_client(*roles: str) -> TestClient:
    app = build_app(*roles)
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    return TestClient(app)


def test_read_endpoint_without_token_returns_401_envelope() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/requerimientos")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_write_endpoint_without_token_returns_401_envelope() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/requerimientos", json={"folio": 1})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_invalid_token_returns_401() -> None:
    app = create_app()
    app.dependency_overrides[get_auth_provider] = lambda: _NullAuthProvider()
    client = TestClient(app)

    response = client.get(
        "/api/v1/requerimientos", headers={"Authorization": "Bearer token-falso"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_expired_token_returns_401() -> None:
    app = create_app()
    app.dependency_overrides[get_auth_provider] = lambda: _NullAuthProvider()
    client = TestClient(app)

    response = client.get(
        "/api/v1/requerimientos", headers={"Authorization": "Bearer token-vencido"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_write_with_insufficient_role_returns_403_envelope() -> None:
    repository = InMemoryRequirementRepository()
    app = build_app("REVISO")
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    client = TestClient(app)

    response = client.post(
        "/api/v1/requerimientos",
        json={
            "folio": 1,
            "titulo": "Alta",
            "tipo_cambio_id": 1,
            "sistema": "SIS",
            "version_documento": "1.0",
            "fecha_version": "2026-10-15",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert client.get("/api/v1/requerimientos").json()["total"] == 0


def test_transition_with_insufficient_role_returns_403_and_state_unchanged() -> None:
    repository = InMemoryRequirementRepository()
    requirement = repository.save(requirement_with(status="BORRADOR"), actor="seed")
    assert requirement.id is not None
    app = build_app("REVISO")
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/requerimientos/{requirement.id}/transicionar",
        json={"a_estado": "EN_REVISION"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert client.get(f"/api/v1/requerimientos/{requirement.id}").json()["estado"] == (
        "BORRADOR"
    )


def test_signature_with_admin_returns_403_and_nothing_persisted() -> None:
    repository = InMemoryRequirementRepository()
    requirement = repository.save(requirement_with(status="APROBADO"), actor="seed")
    assert requirement.id is not None
    version = requirement.current_version()
    assert version is not None
    assert version.id is not None
    app = build_app("ADMIN")
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/requerimientos/{requirement.id}/versiones/{version.id}/firmas",
        json={"rol": "ELABORO", "nombre": "Ana", "cargo": "Analista"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    detail = client.get(f"/api/v1/requerimientos/{requirement.id}").json()
    assert detail["versiones"][0]["firmas"] == []


def test_generate_documents_with_elaboro_returns_403_and_nothing_generated() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement = repository.save(requirement_with(status="APROBADO"), actor="seed")
    assert requirement.id is not None
    app = build_app("ELABORO")
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_requirement_document_repository] = (
        lambda: document_repository
    )
    app.dependency_overrides[get_document_renderer] = lambda: FakeDocumentRenderer()
    app.dependency_overrides[get_document_converter] = lambda: FakeDocumentConverter()
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    client = TestClient(app)

    response = client.post(f"/api/v1/requerimientos/{requirement.id}/documentos")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    assert client.get(f"/api/v1/requerimientos/{requirement.id}/documentos").json() == []


def test_health_and_version_are_public() -> None:
    app = create_app()
    app.dependency_overrides[get_check_health_use_case] = lambda: CheckHealthUseCase(
        _FakeHealthPort()
    )
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/version").status_code == 200


def test_union_of_two_roles_grants_permission() -> None:
    repository = InMemoryRequirementRepository()
    app = build_app("REVISO", "ELABORO")
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    client = TestClient(app)

    response = client.post(
        "/api/v1/requerimientos",
        json={
            "folio": 1,
            "titulo": "Alta",
            "tipo_cambio_id": 1,
            "sistema": "SIS",
            "version_documento": "1.0",
            "fecha_version": "2026-10-15",
        },
    )

    assert response.status_code == 201
    assert response.json()["estado"] == "BORRADOR"
