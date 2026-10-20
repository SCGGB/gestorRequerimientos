from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_audit_recorder,
    get_password_hasher,
    get_user_repository,
)
from app.domain.auth.roles import Role
from tests.api.helpers import build_app
from tests.application.fakes import (
    FakeAuditRecorder,
    FakePasswordHasher,
    InMemoryUserRepository,
    make_user,
)


def _client(
    *roles: str,
    repository: InMemoryUserRepository,
    audit: FakeAuditRecorder | None = None,
) -> TestClient:
    app = build_app(*roles)
    app.dependency_overrides[get_user_repository] = lambda: repository
    app.dependency_overrides[get_password_hasher] = lambda: FakePasswordHasher()
    app.dependency_overrides[get_audit_recorder] = lambda: audit or FakeAuditRecorder()
    return TestClient(app)


def test_create_user_returns_201() -> None:
    repository = InMemoryUserRepository()
    client = _client("ADMIN", repository=repository)

    response = client.post(
        "/api/v1/usuarios",
        json={
            "usuario": "luis",
            "nombre": "Luis",
            "contrasena": "clave1234",
            "roles": ["REVISO"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["usuario"] == "luis"
    assert body["nombre"] == "Luis"
    assert body["roles"] == ["REVISO"]
    assert body["activo"] is True
    assert body["intentos_fallidos"] == 0


def test_list_users_returns_all() -> None:
    repository = InMemoryUserRepository(
        [make_user("bruno"), make_user("ana", roles=frozenset({Role.ADMIN}))]
    )
    client = _client("ADMIN", repository=repository)

    response = client.get("/api/v1/usuarios")

    assert response.status_code == 200
    assert [user["usuario"] for user in response.json()] == ["ana", "bruno"]


def test_get_user_returns_200() -> None:
    repository = InMemoryUserRepository([make_user("ana")])
    client = _client("ADMIN", repository=repository)
    user_id = repository.get_by_username("ana")
    assert user_id is not None

    response = client.get(f"/api/v1/usuarios/{user_id.id}")

    assert response.status_code == 200
    assert response.json()["usuario"] == "ana"


def test_patch_user_resets_failed_attempts() -> None:
    repository = InMemoryUserRepository([make_user("ana", failed_attempts=3)])
    client = _client("ADMIN", repository=repository)
    user_id = repository.get_by_username("ana")
    assert user_id is not None

    response = client.patch(
        f"/api/v1/usuarios/{user_id.id}", json={"nombre": "Ana Editada"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["nombre"] == "Ana Editada"
    assert body["intentos_fallidos"] == 0


def test_users_forbidden_for_non_admin() -> None:
    client = _client("ELABORO", repository=InMemoryUserRepository())

    response = client.get("/api/v1/usuarios")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_self_deactivation_returns_409() -> None:
    repository = InMemoryUserRepository([make_user("tester", roles=frozenset({Role.ADMIN}))])
    client = _client("ADMIN", repository=repository)
    user_id = repository.get_by_username("tester")
    assert user_id is not None

    response = client.patch(f"/api/v1/usuarios/{user_id.id}", json={"activo": False})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "self_deactivation_not_allowed"


def test_get_missing_user_returns_404() -> None:
    client = _client("ADMIN", repository=InMemoryUserRepository())

    response = client.get("/api/v1/usuarios/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


def test_create_duplicate_username_returns_409() -> None:
    repository = InMemoryUserRepository([make_user("ana")])
    client = _client("ADMIN", repository=repository)

    response = client.post(
        "/api/v1/usuarios",
        json={
            "usuario": "ana",
            "nombre": "Otra Ana",
            "contrasena": "clave1234",
            "roles": ["ELABORO"],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "username_taken"


def test_create_short_password_returns_422() -> None:
    client = _client("ADMIN", repository=InMemoryUserRepository())

    response = client.post(
        "/api/v1/usuarios",
        json={
            "usuario": "luis",
            "nombre": "Luis",
            "contrasena": "short",
            "roles": ["ELABORO"],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
