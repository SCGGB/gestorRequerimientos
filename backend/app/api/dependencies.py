from functools import lru_cache

from sqlalchemy.engine import Engine

from app.application.use_cases.check_health import CheckHealthUseCase
from app.application.use_cases.get_version import GetVersionUseCase
from app.infrastructure.adapters.database_health import SqlAlchemyDatabaseHealthAdapter
from app.infrastructure.config import get_settings
from app.infrastructure.database import create_db_engine


@lru_cache
def get_engine() -> Engine:
    return create_db_engine(get_settings())


def get_check_health_use_case() -> CheckHealthUseCase:
    adapter = SqlAlchemyDatabaseHealthAdapter(get_engine())
    return CheckHealthUseCase(adapter)


def get_get_version_use_case() -> GetVersionUseCase:
    return GetVersionUseCase(get_settings().app_version)
