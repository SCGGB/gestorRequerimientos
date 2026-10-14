from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[2]

EXPECTED_TABLES = (
    "REQ_TIPO_CAMBIO",
    "REQ_CARGO",
    "REQ_REQUERIMIENTO",
    "REQ_VERSION",
    "REQ_OBJETIVO",
    "REQ_CONSIDERACION",
    "REQ_RESTRICCION",
    "REQ_VOLUMETRIA",
    "REQ_RIESGO",
    "REQ_REQUISITO_FUTURO",
    "REQ_BENEFICIO",
    "REQ_ANEXO",
    "REQ_FIRMA",
)
AUDIT_COLUMNS = {"CREATED_AT", "CREATED_BY", "UPDATED_AT", "UPDATED_BY"}
EXPECTED_CHANGE_TYPE_CODES = {
    "NUEVA_FUNCIONALIDAD",
    "CORRECCION",
    "REPORTE",
    "INTEGRACION",
    "BASE_DATOS",
    "MEJORA_TECNICA",
}
EXPECTED_DEFAULT_ROLES = {"ELABORO", "REVISO", "AUTORIZO"}

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def alembic_config(oracle_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", oracle_url.replace("%", "%%"))
    return config


def _insert_requerimiento(connection: sa.Connection, folio: int) -> int:
    connection.execute(
        sa.text("INSERT INTO REQ_REQUERIMIENTO (FOLIO, ESTADO) VALUES (:folio, 'BORRADOR')"),
        {"folio": folio},
    )
    return int(
        connection.execute(
            sa.text("SELECT ID FROM REQ_REQUERIMIENTO WHERE FOLIO = :folio"),
            {"folio": folio},
        ).scalar_one()
    )


def _insert_version(
    connection: sa.Connection,
    requirement_id: int,
    dynamic_fields: str,
) -> None:
    connection.execute(
        sa.text(
            "INSERT INTO REQ_VERSION ("
            "REQUERIMIENTO_ID, NUMERO_VERSION, VERSION_DOCUMENTO, FECHA_VERSION, TITULO, "
            "REQUISITOS_FUTUROS_APLICA, CAMPOS_DINAMICOS, CONGELADA) "
            "VALUES (:requerimiento_id, 1, '1.0', SYSDATE, 'Titulo', 'N', :campos, 'N')"
        ),
        {"requerimiento_id": requirement_id, "campos": dynamic_fields},
    )


def test_upgrade_creates_requerimiento_schema(alembic_config: Config, oracle_url: str) -> None:
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


def test_upgrade_seeds_catalogs(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")

    engine = sa.create_engine(oracle_url)
    try:
        with engine.connect() as connection:
            codes = {
                row[0]
                for row in connection.execute(
                    sa.text("SELECT CODIGO FROM REQ_TIPO_CAMBIO WHERE ACTIVO = 'S'")
                )
            }
            default_roles = {
                row[0]
                for row in connection.execute(
                    sa.text(
                        "SELECT ROL FROM REQ_CARGO "
                        "WHERE PREDETERMINADO = 'S' AND ACTIVO = 'S'"
                    )
                )
            }
    finally:
        engine.dispose()

    assert codes == EXPECTED_CHANGE_TYPE_CODES
    assert default_roles == EXPECTED_DEFAULT_ROLES


def test_campos_dinamicos_accepts_valid_json(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")

    engine = sa.create_engine(oracle_url)
    try:
        with engine.begin() as connection:
            requirement_id = _insert_requerimiento(connection, 900001)
            _insert_version(connection, requirement_id, '{"clave": "valor", "n": 1}')

        with engine.connect() as connection:
            stored = connection.execute(
                sa.text(
                    "SELECT CAMPOS_DINAMICOS FROM REQ_VERSION "
                    "WHERE REQUERIMIENTO_ID = :requerimiento_id"
                ),
                {"requerimiento_id": requirement_id},
            ).scalar_one()
    finally:
        engine.dispose()

    assert "clave" in stored


def test_campos_dinamicos_rejects_invalid_json(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")

    engine = sa.create_engine(oracle_url)
    try:
        with pytest.raises(sa.exc.IntegrityError), engine.begin() as connection:
            requirement_id = _insert_requerimiento(connection, 900002)
            _insert_version(connection, requirement_id, "no-es-json")
    finally:
        engine.dispose()


def test_downgrade_drops_requerimiento_schema(alembic_config: Config, oracle_url: str) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")

    engine = sa.create_engine(oracle_url)
    try:
        inspector = sa.inspect(engine)
        for table in EXPECTED_TABLES:
            assert not inspector.has_table(table), table
    finally:
        engine.dispose()
