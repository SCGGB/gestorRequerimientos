from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.catalog_repository import ChangeTypeCatalog, PositionCatalog
from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.enums import SignatureRole
from app.infrastructure.database import create_session_factory
from app.infrastructure.db import mappers
from app.infrastructure.db.tables import REQ_CARGO, REQ_TIPO_CAMBIO


class SqlAlchemyChangeTypeCatalog(ChangeTypeCatalog):
    def __init__(self, engine: Engine) -> None:
        self._session_factory: sessionmaker[Session] = create_session_factory(engine)

    def list_active(self) -> Sequence[ChangeType]:
        with self._session_factory() as session:
            rows = (
                session.execute(
                    select(REQ_TIPO_CAMBIO)
                    .where(REQ_TIPO_CAMBIO.c.ACTIVO == "S")
                    .order_by(REQ_TIPO_CAMBIO.c.NOMBRE)
                )
                .mappings()
                .all()
            )
            return [mappers.change_type_from_row(dict(row)) for row in rows]

    def get(self, change_type_id: int) -> ChangeType | None:
        with self._session_factory() as session:
            row = (
                session.execute(
                    select(REQ_TIPO_CAMBIO).where(REQ_TIPO_CAMBIO.c.ID == change_type_id)
                )
                .mappings()
                .one_or_none()
            )
            return mappers.change_type_from_row(dict(row)) if row is not None else None


class SqlAlchemyPositionCatalog(PositionCatalog):
    def __init__(self, engine: Engine) -> None:
        self._session_factory: sessionmaker[Session] = create_session_factory(engine)

    def list_by_role(self, role: SignatureRole) -> Sequence[Position]:
        with self._session_factory() as session:
            rows = (
                session.execute(
                    select(REQ_CARGO)
                    .where(REQ_CARGO.c.ROL == role.value, REQ_CARGO.c.ACTIVO == "S")
                    .order_by(REQ_CARGO.c.NOMBRE)
                )
                .mappings()
                .all()
            )
            return [mappers.position_from_row(dict(row)) for row in rows]

    def list_active(self) -> Sequence[Position]:
        with self._session_factory() as session:
            rows = (
                session.execute(
                    select(REQ_CARGO)
                    .where(REQ_CARGO.c.ACTIVO == "S")
                    .order_by(REQ_CARGO.c.NOMBRE)
                )
                .mappings()
                .all()
            )
            return [mappers.position_from_row(dict(row)) for row in rows]

    def get(self, position_id: int) -> Position | None:
        with self._session_factory() as session:
            row = (
                session.execute(select(REQ_CARGO).where(REQ_CARGO.c.ID == position_id))
                .mappings()
                .one_or_none()
            )
            return mappers.position_from_row(dict(row)) if row is not None else None
