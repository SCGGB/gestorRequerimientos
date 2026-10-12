from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_version: str = "0.1.0"

    oracle_user: str = "app_req"
    oracle_password: SecretStr = SecretStr("change_me")
    oracle_dsn: str = "oracle:1521/FREEPDB1"
    oracle_wallet_dir: str | None = None

    storage_backend: Literal["local", "s3", "oci"] = "local"
    auth_provider: Literal["local_jwt", "oidc"] = "local_jwt"
    jwt_secret: SecretStr = SecretStr("change_me")
    ai_provider: str = "none"


@lru_cache
def get_settings() -> Settings:
    return Settings()
