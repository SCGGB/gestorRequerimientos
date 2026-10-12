from fastapi.testclient import TestClient

from app.api.dependencies import get_get_version_use_case
from app.application.use_cases.get_version import GetVersionUseCase
from app.main import create_app


def test_version_returns_configured_version() -> None:
    app = create_app()
    app.dependency_overrides[get_get_version_use_case] = lambda: GetVersionUseCase("9.9.9")

    response = TestClient(app).get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "9.9.9"}
