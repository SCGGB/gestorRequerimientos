from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.application.ports.database_health import DatabaseHealthPort
from app.domain.health import DatabaseStatus


class SqlAlchemyDatabaseHealthAdapter(DatabaseHealthPort):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def check(self) -> DatabaseStatus:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1 FROM DUAL"))
        except Exception:
            return DatabaseStatus.DOWN
        return DatabaseStatus.OK
