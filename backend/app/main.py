from fastapi import FastAPI

from app.api.routers import health, version
from app.infrastructure.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Gestor de Requerimientos API", version=settings.app_version)
    app.include_router(health.router)
    app.include_router(version.router)
    return app


app = create_app()
