from app.application.ports.database_health import DatabaseHealthPort
from app.domain.health import ApplicationStatus, DatabaseStatus, HealthReport


class CheckHealthUseCase:
    def __init__(self, database_health: DatabaseHealthPort) -> None:
        self._database_health = database_health

    def execute(self) -> HealthReport:
        try:
            database = self._database_health.check()
        except Exception:
            database = DatabaseStatus.DOWN
        return HealthReport(app=ApplicationStatus.OK, database=database)
