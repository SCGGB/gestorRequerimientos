from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_audit_recorder,
    get_password_hasher,
    get_token_service,
    get_user_repository,
)
from app.domain.auth.roles import Role
from tests.api.helpers import build_app
from tests.application.fakes import (
    FakeAuditRecorder,
    FakePasswordHasher,
    FakeTokenService,
    InMemoryUserRepository,
    make_user,
)


def _login_client(
    repository: InMemoryUserRepository,
    *,
    audit: FakeAuditRecorder | None = None,
    tokens: FakeTokenService | None = None,
) -> TestClient:
    app = build_app()
    app.dependency_overrides[get_user_repository] = lambda: repository
    app.dependency_overrides[get_password_hasher] = lambda: FakePasswordHasher()
    app.dependency_overrides[get_token_service] = lambda: tokens or FakeTokenService()
    app.dependency_overrides[get_audit_recorder] = lambda: audit or FakeAuditRecorder()
    return TestClient(app)


def test_login_success_returns_token_and_profile() -> None:
    repository = InMemoryUserRepository([make_user("ana")])
    client = _login_client(repository)

    response = client.post(
        "/api/v1/auth/login", json={"usuario": "ana", "contrasena": "secreto123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["tipo_token"] == "Bearer"
    assert body["usuario"] == "ana"
    assert body["expira_en"] > 0


def test_login_wrong_password_returns_invalid_credentials() -> None:
    repository = InMemoryUserRepository([make_user("ana")])
    client = _login_client(repository)

    response = client.post(
        "/api/v1/auth/login", json={"usuario": "ana", "contrasena": "mala"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_unknown_user_returns_invalid_credentials() -> None:
    client = _login_client(InMemoryUserRepository())

    response = client.post(
        "/api/v1/auth/login", json={"usuario": "fantasma", "contrasena": "secreto123"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_locked_account_returns_account_locked() -> None:
    repository = InMemoryUserRepository([make_user("ana", failed_attempts=5)])
    client = _login_client(repository)

    response = client.post(
        "/api/v1/auth/login", json={"usuario": "ana", "contrasena": "secreto123"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "account_locked"


def test_login_missing_fields_returns_422() -> None:
    client = _login_client(InMemoryUserRepository())

    response = client.post("/api/v1/auth/login", json={"usuario": "ana"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_logout_returns_204(client_as) -> None:  # type: ignore[no-untyped-def]
    app = client_as().app
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()

    response = TestClient(app).post("/api/v1/auth/logout")

    assert response.status_code == 204


def test_session_returns_profile_and_roles(client_as) -> None:  # type: ignore[no-untyped-def]
    app = client_as().app
    app.dependency_overrides[get_user_repository] = lambda: InMemoryUserRepository(
        [make_user("tester", roles=frozenset({Role.ELABORO, Role.ADMIN}))]
    )

    response = TestClient(app).get("/api/v1/auth/sesion")

    assert response.status_code == 200
    body = response.json()
    assert body["usuario"] == "tester"
    assert body["nombre"] == "Usuario tester"
    assert body["activo"] is True
    assert set(body["roles"]) == {"ELABORO", "ADMIN"}
