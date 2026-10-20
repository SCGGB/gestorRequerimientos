from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_principal
from app.application.ports.auth import Principal
from app.domain.auth.roles import Role
from app.main import create_app

ALL_ROLES = tuple(role.value for role in Role)


def build_app(*roles: str) -> FastAPI:
    """App con el principal de prueba inyectado; sin roles, usa todos los roles."""
    app = create_app()
    selected = roles or ALL_ROLES
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        user_id="tester", roles=frozenset(Role(value) for value in selected)
    )
    return app


def build_client(*roles: str) -> TestClient:
    return TestClient(build_app(*roles))
