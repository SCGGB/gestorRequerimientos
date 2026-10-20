from __future__ import annotations

from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.audit_repository import AuditRecorderPort
from app.domain.auth.audit import AuditEntry
from app.infrastructure.database import create_session_factory
from app.infrastructure.db import mappers
from app.infrastructure.db.tables import SYS_AUDITORIA


class SqlAlchemyAuditRecorder(AuditRecorderPort):
    """Inserta entradas de auditoria en SYS_AUDITORIA (solo escritura)."""

    def __init__(self, engine: Engine) -> None:
        self._session_factory: sessionmaker[Session] = create_session_factory(engine)

    def record(self, entry: AuditEntry) -> None:
        row = mappers.audit_entry_to_row(entry)
        if row.get("CREATED_AT") is None:
            row["CREATED_AT"] = datetime.now()
        with self._session_factory.begin() as session:
            session.execute(insert(SYS_AUDITORIA).values(**row))
