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
    jwt_ttl_hours: int = 8
    password_min_length: int = 8
    password_hash_iterations: int = 200_000
    login_max_failed_attempts: int = 5
    seed_admin_username: str | None = None
    seed_admin_password: SecretStr | None = None
    seed_admin_nombre: str = "Administrador"
    ai_provider: str = "none"

    templates_dir: str = "/app/templates"
    document_template_version: str = "v1"
    libreoffice_binary: str = "soffice"
    document_generation_timeout_seconds: int = 60
    document_max_bytes: int = 25_000_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
