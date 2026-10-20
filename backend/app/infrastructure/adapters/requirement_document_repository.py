from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Column, insert, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.errors import DocumentNotFoundError
from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.domain.requirement.document import GeneratedDocument
from app.infrastructure.database import create_session_factory
from app.infrastructure.db import mappers
from app.infrastructure.db.tables import REQ_DOCUMENTO

_METADATA_COLUMNS: tuple[Column[Any], ...] = tuple(
    column for column in REQ_DOCUMENTO.columns if column.name != "CONTENIDO"
)


def _insert_audit(now: datetime, actor: str) -> dict[str, Any]:
    return {
        "CREATED_AT": now,
        "CREATED_BY": actor,
        "UPDATED_AT": now,
        "UPDATED_BY": actor,
    }


class SqlAlchemyRequirementDocumentRepository(RequirementDocumentRepository):
    def __init__(self, engine: Engine) -> None:
        self._session_factory: sessionmaker[Session] = create_session_factory(engine)

    def add(self, document: GeneratedDocument, *, actor: str) -> int:
        row = mappers.generated_document_to_row(document)
        row.pop("ID", None)
        row.update(_insert_audit(datetime.now(), actor))
        with self._session_factory.begin() as session:
            result = session.execute(
                insert(REQ_DOCUMENTO).values(**row).returning(REQ_DOCUMENTO.c.ID)
            )
            return int(result.scalar_one())

    def get(self, document_id: int) -> GeneratedDocument:
        with self._session_factory() as session:
            row = (
                session.execute(
                    select(REQ_DOCUMENTO).where(REQ_DOCUMENTO.c.ID == document_id)
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            raise DocumentNotFoundError()
        return mappers.generated_document_from_row(dict(row), with_content=True)

    def list_by_requirement(self, requirement_id: int) -> Sequence[GeneratedDocument]:
        statement = (
            select(*_METADATA_COLUMNS)
            .where(REQ_DOCUMENTO.c.REQUERIMIENTO_ID == requirement_id)
            .order_by(REQ_DOCUMENTO.c.GENERADO_AT.desc(), REQ_DOCUMENTO.c.ID.desc())
        )
        with self._session_factory() as session:
            rows = session.execute(statement).mappings().all()
        return tuple(
            mappers.generated_document_from_row(dict(row), with_content=False)
            for row in rows
        )
