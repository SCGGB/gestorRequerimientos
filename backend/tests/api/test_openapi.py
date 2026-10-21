from typing import Any

from fastapi.testclient import TestClient

from app.main import create_app


def _openapi() -> dict[str, Any]:
    client = TestClient(create_app())
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def _responses(spec: dict[str, Any], path: str, method: str) -> dict[str, Any]:
    return spec["paths"][path][method]["responses"]


def test_openapi_exposes_new_auth_and_users_endpoints() -> None:
    spec = _openapi()

    for path, method in (
        ("/api/v1/auth/login", "post"),
        ("/api/v1/auth/logout", "post"),
        ("/api/v1/auth/sesion", "get"),
        ("/api/v1/usuarios", "get"),
        ("/api/v1/usuarios", "post"),
        ("/api/v1/usuarios/{usuario_id}", "get"),
        ("/api/v1/usuarios/{usuario_id}", "patch"),
    ):
        assert path in spec["paths"], path
        assert method in spec["paths"][path], f"{method} {path}"


def test_openapi_documents_401_on_every_protected_endpoint() -> None:
    spec = _openapi()

    for path, operations in spec["paths"].items():
        if not path.startswith("/api/v1"):
            continue
        for method, operation in operations.items():
            responses = operation["responses"]
            if path == "/api/v1/auth/login" and method == "post":
                continue
            assert "401" in responses, f"{method} {path}"


def test_openapi_documents_403_on_role_restricted_endpoints() -> None:
    spec = _openapi()

    for path, method in (
        ("/api/v1/usuarios", "get"),
        ("/api/v1/usuarios", "post"),
        ("/api/v1/usuarios/{usuario_id}", "get"),
        ("/api/v1/usuarios/{usuario_id}", "patch"),
        ("/api/v1/requerimientos", "post"),
        ("/api/v1/requerimientos/{requirement_id}/versiones/{version_id}", "patch"),
        ("/api/v1/requerimientos/{requirement_id}/transicionar", "post"),
        ("/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/firmas", "post"),
        ("/api/v1/requerimientos/{requirement_id}/documentos", "post"),
    ):
        responses = _responses(spec, path, method)
        assert "403" in responses, f"{method} {path}"
        schema = responses["403"]["content"]["application/json"]["schema"]
        assert schema["$ref"] == "#/components/schemas/ErrorResponse"


def test_openapi_login_documents_invalid_credentials_and_locked_codes() -> None:
    spec = _openapi()

    responses = _responses(spec, "/api/v1/auth/login", "post")
    examples = responses["401"]["content"]["application/json"]["examples"]
    assert set(examples) == {"invalid_credentials", "account_locked"}
    assert examples["invalid_credentials"]["value"]["error"]["code"] == "invalid_credentials"
    assert examples["account_locked"]["value"]["error"]["code"] == "account_locked"


def test_openapi_registers_the_shared_error_envelope_schema() -> None:
    spec = _openapi()

    assert "ErrorResponse" in spec["components"]["schemas"]
