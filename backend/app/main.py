from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routers import (
    attachments,
    catalogs,
    collections,
    health,
    requirements,
    signatures,
    version,
)
from app.infrastructure.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Gestor de Requerimientos API", version=settings.app_version)
    app.include_router(health.router)
    app.include_router(version.router)
    app.include_router(requirements.router)
    app.include_router(collections.router)
    app.include_router(signatures.router)
    app.include_router(attachments.router)
    app.include_router(catalogs.router)
    register_exception_handlers(app)
    return app


app = create_app()
