from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.config import Settings


def _split_oracle_dsn(dsn: str) -> tuple[str, str | None, str | None]:
    """Divide un DSN EZConnect (`host[:port][/servicio]`) en host, puerto y servicio."""
    host_port, _, service = dsn.partition("/")
    host, _, port = host_port.partition(":")
    return host, port or None, service or None


def build_database_url(settings: Settings) -> str:
    user = quote_plus(settings.oracle_user)
    password = quote_plus(settings.oracle_password.get_secret_value())
    host, port, service = _split_oracle_dsn(settings.oracle_dsn)

    authority = f"{user}:{password}@{host}"
    if port:
        authority = f"{authority}:{port}"

    url = f"oracle+oracledb://{authority}/"
    if service:
        url = f"{url}?service_name={quote_plus(service)}"
    return url


def create_db_engine(settings: Settings, url: str | None = None) -> Engine:
    connect_args: dict[str, Any] = {}
    if settings.oracle_wallet_dir:
        connect_args["config_dir"] = settings.oracle_wallet_dir
        connect_args["wallet_location"] = settings.oracle_wallet_dir
    return create_engine(
        url or build_database_url(settings),
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
