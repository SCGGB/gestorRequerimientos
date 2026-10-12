from fastapi.testclient import TestClient

from app.api.dependencies import get_check_health_use_case
from app.application.ports.database_health import DatabaseHealthPort
from app.application.use_cases.check_health import CheckHealthUseCase
from app.domain.health import DatabaseStatus
from app.main import create_app


class FakeDatabaseHealthPort(DatabaseHealthPort):
    def __init__(self, status: DatabaseStatus) -> None:
        self._status = status

    def check(self) -> DatabaseStatus:
        return self._status


def _client_with_database(status: DatabaseStatus) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_check_health_use_case] = lambda: CheckHealthUseCase(
        FakeDatabaseHealthPort(status)
    )
    return TestClient(app)


def test_health_returns_ok_when_database_is_up() -> None:
    response = _client_with_database(DatabaseStatus.OK).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_down_when_database_is_down() -> None:
    response = _client_with_database(DatabaseStatus.DOWN).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "down"}
