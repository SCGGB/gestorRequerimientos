from app.infrastructure.config import Settings
from app.infrastructure.database import build_database_url


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "oracle_user": "app_req",
        "oracle_password": "change_me",
        "oracle_dsn": "oracle:1521/FREEPDB1",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_build_database_url_uses_service_name() -> None:
    url = build_database_url(_settings())

    assert url == "oracle+oracledb://app_req:change_me@oracle:1521/?service_name=FREEPDB1"


def test_build_database_url_without_port() -> None:
    url = build_database_url(_settings(oracle_dsn="dbhost/FREEPDB1"))

    assert url == "oracle+oracledb://app_req:change_me@dbhost/?service_name=FREEPDB1"


def test_build_database_url_without_service() -> None:
    url = build_database_url(_settings(oracle_dsn="dbhost:1521"))

    assert url == "oracle+oracledb://app_req:change_me@dbhost:1521/"


def test_build_database_url_quotes_credentials_and_service() -> None:
    url = build_database_url(
        _settings(oracle_user="a@b", oracle_password="p@ss/word", oracle_dsn="host:1521/svc/x")
    )

    assert url == "oracle+oracledb://a%40b:p%40ss%2Fword@host:1521/?service_name=svc%2Fx"
