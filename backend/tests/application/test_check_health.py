from app.application.ports.database_health import DatabaseHealthPort
from app.application.use_cases.check_health import CheckHealthUseCase
from app.domain.health import ApplicationStatus, DatabaseStatus


class FakeDatabaseHealthPort(DatabaseHealthPort):
    def __init__(self, status: DatabaseStatus | None = None, raise_error: bool = False) -> None:
        self._status = status
        self._raise_error = raise_error

    def check(self) -> DatabaseStatus:
        if self._raise_error:
            raise RuntimeError("database unavailable")
        assert self._status is not None
        return self._status


def test_health_report_ok_when_database_up() -> None:
    use_case = CheckHealthUseCase(FakeDatabaseHealthPort(status=DatabaseStatus.OK))

    report = use_case.execute()

    assert report.app is ApplicationStatus.OK
    assert report.database is DatabaseStatus.OK


def test_health_report_down_when_database_reports_down() -> None:
    use_case = CheckHealthUseCase(FakeDatabaseHealthPort(status=DatabaseStatus.DOWN))

    report = use_case.execute()

    assert report.app is ApplicationStatus.OK
    assert report.database is DatabaseStatus.DOWN


def test_health_report_down_when_database_raises() -> None:
    use_case = CheckHealthUseCase(FakeDatabaseHealthPort(raise_error=True))

    report = use_case.execute()

    assert report.app is ApplicationStatus.OK
    assert report.database is DatabaseStatus.DOWN
