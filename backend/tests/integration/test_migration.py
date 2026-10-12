from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[2]

EXPECTED_TABLE = "SYS_AUDITORIA"
EXPECTED_COLUMNS = {
    "ID",
    "ENTIDAD",
    "ENTIDAD_ID",
    "ACCION",
    "ACTOR",
    "DETALLE",
    "CREATED_AT",
    "CREATED_BY",
    "UPDATED_AT",
    "UPDATED_BY",
}

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def alembic_config(oracle_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", oracle_url.replace("%", "%%"))
    return config


def test_upgrade_creates_sys_auditoria(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")

    engine = sa.create_engine(oracle_url)
    try:
        inspector = sa.inspect(engine)
        assert inspector.has_table(EXPECTED_TABLE)
        column_names = {
            column["name"].upper() for column in inspector.get_columns(EXPECTED_TABLE)
        }
        assert column_names >= EXPECTED_COLUMNS
    finally:
        engine.dispose()


def test_downgrade_drops_sys_auditoria(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")

    engine = sa.create_engine(oracle_url)
    try:
        inspector = sa.inspect(engine)
        assert not inspector.has_table(EXPECTED_TABLE)
    finally:
        engine.dispose()
