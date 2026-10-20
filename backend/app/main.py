from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routers import (
    attachments,
    auth,
    catalogs,
    collections,
    documents,
    health,
    requirements,
    signatures,
    users,
    validation,
    version,
)
from app.infrastructure.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Gestor de Requerimientos API", version=settings.app_version)
    app.include_router(health.router)
    app.include_router(version.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(requirements.router)
    app.include_router(validation.router)
    app.include_router(signatures.router)
    app.include_router(attachments.router)
    app.include_router(collections.router)
    app.include_router(catalogs.router)
    app.include_router(documents.router)
    register_exception_handlers(app)
    return app


app = create_app()
