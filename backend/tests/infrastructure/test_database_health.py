from unittest.mock import MagicMock

from sqlalchemy.engine import Engine

from app.domain.health import DatabaseStatus
from app.infrastructure.adapters.database_health import SqlAlchemyDatabaseHealthAdapter


def test_check_returns_ok_when_query_succeeds() -> None:
    engine = MagicMock(spec=Engine)
    connection = engine.connect.return_value.__enter__.return_value
    adapter = SqlAlchemyDatabaseHealthAdapter(engine)

    status = adapter.check()

    assert status is DatabaseStatus.OK
    connection.execute.assert_called_once()


def test_check_returns_down_when_query_raises() -> None:
    engine = MagicMock(spec=Engine)
    engine.connect.side_effect = RuntimeError("database unavailable")
    adapter = SqlAlchemyDatabaseHealthAdapter(engine)

    status = adapter.check()

    assert status is DatabaseStatus.DOWN
