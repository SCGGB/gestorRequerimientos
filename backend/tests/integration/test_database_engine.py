import pytest
import sqlalchemy as sa
from sqlalchemy.engine import make_url

from app.infrastructure.config import Settings
from app.infrastructure.database import build_database_url, create_db_engine

pytestmark = pytest.mark.integration


def _settings_from_url(url: str) -> Settings:
    """Construye Settings a partir de un DSN EZConnect derivado del contenedor Oracle."""
    parsed = make_url(url)
    service = parsed.query.get("service_name") or parsed.database
    dsn = f"{parsed.host}:{parsed.port}/{service}"
    return Settings(
        oracle_user=parsed.username or "",
        oracle_password=parsed.password or "",
        oracle_dsn=dsn,
    )


def test_build_database_url_targets_service_not_sid() -> None:
    settings = Settings(
        oracle_user="app_req",
        oracle_password="change_me",
        oracle_dsn="oracle:1521/FREEPDB1",
    )

    assert "?service_name=FREEPDB1" in build_database_url(settings)
    assert build_database_url(settings).endswith("/?service_name=FREEPDB1")


def test_engine_built_from_ezeconnect_dsn_connects(oracle_url: str) -> None:
    settings = _settings_from_url(oracle_url)
    engine = create_db_engine(settings)
    try:
        with engine.connect() as connection:
            assert connection.execute(sa.text("SELECT 1 FROM DUAL")).scalar() == 1
    finally:
        engine.dispose()
