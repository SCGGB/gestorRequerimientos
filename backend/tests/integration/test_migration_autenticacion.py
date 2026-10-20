from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.infrastructure.adapters.password_hasher import Pbkdf2PasswordHasher
from app.infrastructure.config import get_settings

BACKEND_DIR = Path(__file__).resolve().parents[2]
EXPECTED_TABLES = ("SYS_USUARIO", "SYS_USUARIO_ROL")
AUDIT_COLUMNS = {"CREATED_AT", "CREATED_BY", "UPDATED_AT", "UPDATED_BY"}

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def alembic_config(oracle_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", oracle_url.replace("%", "%%"))
    return config


def test_upgrade_creates_auth_schema(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")

    engine = sa.create_engine(oracle_url)
    try:
        inspector = sa.inspect(engine)
        for table in EXPECTED_TABLES:
            assert inspector.has_table(table), table
            column_names = {column["name"].upper() for column in inspector.get_columns(table)}
            assert column_names >= AUDIT_COLUMNS, table
    finally:
        engine.dispose()


def test_upgrade_seeds_admin_and_hash_verifies(
    alembic_config: Config, oracle_url: str
) -> None:
    command.upgrade(alembic_config, "head")
    settings = get_settings()
    assert settings.seed_admin_password is not None

    engine = sa.create_engine(oracle_url)
    try:
        with engine.connect() as connection:
            row = connection.execute(
                sa.text(
                    "SELECT ID, USERNAME, PASSWORD_HASH, ACTIVO, INTENTOS_FALLIDOS "
                    "FROM SYS_USUARIO WHERE USERNAME = :username"
                ),
                {"username": settings.seed_admin_username},
            ).one()
            user_id = int(row[0])
            password_hash = str(row[2])
            assert row[3] == "S"
            assert int(row[4]) == 0

            roles = {
                r[0]
                for r in connection.execute(
                    sa.text("SELECT ROL FROM SYS_USUARIO_ROL WHERE USUARIO_ID = :id"),
                    {"id": user_id},
                )
            }
            assert roles == {"ADMIN"}
    finally:
        engine.dispose()

    hasher = Pbkdf2PasswordHasher(settings.password_hash_iterations)
    assert hasher.verify(settings.seed_admin_password.get_secret_value(), password_hash)


def test_downgrade_drops_auth_tables(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "0003_documentos_generados")

    engine = sa.create_engine(oracle_url)
    try:
        inspector = sa.inspect(engine)
        for table in EXPECTED_TABLES:
            assert not inspector.has_table(table), table
        assert inspector.has_table("SYS_AUDITORIA")
    finally:
        engine.dispose()
