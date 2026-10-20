from collections.abc import Iterator
from os import environ
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine
from testcontainers.community.oracle import OracleDbContainer

BACKEND_DIR = Path(__file__).resolve().parents[2]

SEED_ADMIN_USERNAME = "admin-seed"
SEED_ADMIN_PASSWORD = "seed-password-123"


@pytest.fixture(scope="session", autouse=True)
def _seed_admin_env() -> Iterator[None]:
    """Fija credenciales de prueba de la semilla ANTES de cualquier upgrade.

    De ambito sesion (no funcion) para que tambien corra antes de fixtures de
    ambito modulo como ``migrated_engine``; usa os.environ (no monkeypatch)
    porque los valores deben persistir durante toda la sesion de pruebas.
    """
    previous = {
        key: environ.get(key)
        for key in ("SEED_ADMIN_USERNAME", "SEED_ADMIN_PASSWORD", "SEED_ADMIN_NOMBRE")
    }
    environ.setdefault("SEED_ADMIN_USERNAME", SEED_ADMIN_USERNAME)
    environ.setdefault("SEED_ADMIN_PASSWORD", SEED_ADMIN_PASSWORD)
    environ.setdefault("SEED_ADMIN_NOMBRE", "Administrador de Prueba")

    from app.infrastructure.config import get_settings

    get_settings.cache_clear()
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                environ.pop(key, None)
            else:
                environ[key] = value
        get_settings.cache_clear()


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
