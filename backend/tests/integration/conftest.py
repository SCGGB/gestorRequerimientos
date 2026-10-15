from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine
from testcontainers.community.oracle import OracleDbContainer

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def oracle_url() -> Iterator[str]:
    with OracleDbContainer() as oracle:
        yield oracle.get_connection_url()


@pytest.fixture(scope="module")
def migrated_engine(oracle_url: str) -> Iterator[Engine]:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", oracle_url.replace("%", "%%"))
    command.upgrade(config, "head")

    engine = sa.create_engine(oracle_url)
    try:
        yield engine
    finally:
        engine.dispose()
