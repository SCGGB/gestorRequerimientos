from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy import Table, delete, func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session, sessionmaker

from app.application.errors import (
    ApplicationError,
    DataConflictError,
    DuplicateFolioError,
    RequirementNotFoundError,
)
from app.application.ports.requirement_repository import (
    RequirementRepository,
    RequirementSearchFilters,
)
from app.domain.requirement.items import CollectionItem
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion
from app.infrastructure.database import create_session_factory
from app.infrastructure.db import mappers
from app.infrastructure.db.tables import (
    REQ_ANEXO,
    REQ_BENEFICIO,
    REQ_CONSIDERACION,
    REQ_FIRMA,
    REQ_OBJETIVO,
    REQ_REQUERIMIENTO,
    REQ_REQUISITO_FUTURO,
    REQ_RESTRICCION,
    REQ_RIESGO,
    REQ_VERSION,
    REQ_VOLUMETRIA,
)

FOLIO_UNIQUE_CONSTRAINT = "REQ_REQUERIMIENTO_FOLIO_UQ"
# Desplazamiento temporal de ORDEN para el reorden en dos fases (UQ VERSION_ID+ORDEN);
# los ORDEN de dominio son numeros pequeños, muy por debajo de este umbral.
ORDER_SHIFT = 1_000_000
ToRow = Callable[..., dict[str, Any]]


class PersistableChild(Protocol):
    """Sub-recurso con id estable (coleccion, firma o anexo)."""

    @property
    def id(self) -> int | None: ...


def _insert_audit(now: datetime, actor: str) -> dict[str, Any]:
    return {
        "CREATED_AT": now,
        "CREATED_BY": actor,
        "UPDATED_AT": now,
        "UPDATED_BY": actor,
    }


def _update_audit(now: datetime, actor: str) -> dict[str, Any]:
    return {"UPDATED_AT": now, "UPDATED_BY": actor}


def _map_integrity_error(exc: IntegrityError) -> ApplicationError:
    if FOLIO_UNIQUE_CONSTRAINT in str(exc):
        return DuplicateFolioError()
    return DataConflictError()


class SqlAlchemyRequirementRepository(RequirementRepository):
    def __init__(self, engine: Engine) -> None:
        self._session_factory: sessionmaker[Session] = create_session_factory(engine)

    def save(self, requirement: Requirement, *, actor: str) -> Requirement:
        try:
            with self._session_factory.begin() as session:
                requirement_id = self._persist_requirement(session, requirement, actor)
        except IntegrityError as exc:
            raise _map_integrity_error(exc) from exc
        return self.get(requirement_id)

    def get(self, requirement_id: int) -> Requirement:
        with self._session_factory() as session:
            return self._load_translating(session, requirement_id)

    def get_by_folio(self, folio: int) -> Requirement | None:
        with self._session_factory() as session:
            requirement_id = session.execute(
                select(REQ_REQUERIMIENTO.c.ID).where(REQ_REQUERIMIENTO.c.FOLIO == folio)
            ).scalar_one_or_none()
            if requirement_id is None:
                return None
            return self._load(session, int(requirement_id))

    def list(self) -> Sequence[Requirement]:
        with self._session_factory() as session:
            ids = (
                session.execute(
                    select(REQ_REQUERIMIENTO.c.ID).order_by(REQ_REQUERIMIENTO.c.ID)
                )
                .scalars()
                .all()
            )
            return tuple(self._load(session, int(requirement_id)) for requirement_id in ids)

    def search(
        self,
        filters: RequirementSearchFilters,
        *,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Requirement], int]:
        conditions = []
        if filters.status is not None:
            conditions.append(REQ_REQUERIMIENTO.c.ESTADO == filters.status.value)
        if filters.folio is not None:
            conditions.append(REQ_REQUERIMIENTO.c.FOLIO == filters.folio)

        with self._session_factory() as session:
            count_statement = select(func.count()).select_from(REQ_REQUERIMIENTO)
            if conditions:
                count_statement = count_statement.where(*conditions)
            total = int(session.execute(count_statement).scalar_one())

            ids_statement = (
                select(REQ_REQUERIMIENTO.c.ID)
                .order_by(REQ_REQUERIMIENTO.c.ID)
                .offset(offset)
                .limit(limit)
            )
            if conditions:
                ids_statement = ids_statement.where(*conditions)
            ids = session.execute(ids_statement).scalars().all()

            items = tuple(
                self._load_translating(session, int(requirement_id)) for requirement_id in ids
            )
        return items, total

    def _load_translating(self, session: Session, requirement_id: int) -> Requirement:
        try:
            return self._load(session, requirement_id)
        except NoResultFound as exc:
            raise RequirementNotFoundError() from exc

    def _persist_requirement(
        self, session: Session, requirement: Requirement, actor: str
    ) -> int:
        now = datetime.now()
        requirement_id = self._upsert_container(session, requirement, now, actor)

        version_ids: dict[int, int] = {}
        for version in requirement.versions:
            version_ids[version.number] = self._persist_version(
                session, version, requirement_id, now, actor
            )

        current = requirement.current_version()
        if current is not None:
            session.execute(
                update(REQ_REQUERIMIENTO)
                .where(REQ_REQUERIMIENTO.c.ID == requirement_id)
                .values(VERSION_ACTUAL_ID=version_ids[current.number])
            )
        return requirement_id

    def _upsert_container(
        self, session: Session, requirement: Requirement, now: datetime, actor: str
    ) -> int:
        row = mappers.requirement_to_row(requirement)
        row.pop("VERSION_ACTUAL_ID", None)
        if requirement.id is None:
            row.pop("ID", None)
            row.update(_insert_audit(now, actor))
            result = session.execute(
                insert(REQ_REQUERIMIENTO)
                .values(**row)
                .returning(REQ_REQUERIMIENTO.c.ID)
            )
            return int(result.scalar_one())

        row.pop("ID", None)
        session.execute(
            update(REQ_REQUERIMIENTO)
            .where(REQ_REQUERIMIENTO.c.ID == requirement.id)
            .values(**row, **_update_audit(now, actor))
        )
        return requirement.id

    def _persist_version(
        self,
        session: Session,
        version: RequirementVersion,
        requirement_id: int,
        now: datetime,
        actor: str,
    ) -> int:
        row = mappers.version_to_row(version, requirement_id=requirement_id)
        if version.id is None:
            row.pop("ID", None)
            row.update(_insert_audit(now, actor))
            result = session.execute(
                insert(REQ_VERSION).values(**row).returning(REQ_VERSION.c.ID)
            )
            version_id = int(result.scalar_one())
        else:
            version_id = version.id
            row.pop("ID", None)
            session.execute(
                update(REQ_VERSION)
                .where(REQ_VERSION.c.ID == version_id)
                .values(**row, **_update_audit(now, actor))
            )

        self._replace_children(session, version_id, version, now, actor)
        return version_id

    def _replace_children(
        self,
        session: Session,
        version_id: int,
        version: RequirementVersion,
        now: datetime,
        actor: str,
    ) -> None:
        self._replace_collection(
            session,
            REQ_OBJETIVO,
            mappers.objective_to_row,
            version.objectives,
            version_id,
            now,
            actor,
        )
        self._replace_collection(
            session,
            REQ_CONSIDERACION,
            mappers.consideration_to_row,
            version.considerations,
            version_id,
            now,
            actor,
        )
        self._replace_collection(
            session,
            REQ_BENEFICIO,
            mappers.benefit_to_row,
            version.benefits,
            version_id,
            now,
            actor,
        )
        self._replace_collection(
            session,
            REQ_RESTRICCION,
            mappers.restriction_to_row,
            version.restrictions,
            version_id,
            now,
            actor,
        )
        self._replace_collection(
            session,
            REQ_VOLUMETRIA,
            mappers.volumetry_to_row,
            version.volumetry,
            version_id,
            now,
            actor,
        )
        self._replace_collection(
            session, REQ_RIESGO, mappers.risk_to_row, version.risks, version_id, now, actor
        )
        self._replace_collection(
            session,
            REQ_REQUISITO_FUTURO,
            mappers.future_requirement_to_row,
            version.future_requirements_items,
            version_id,
            now,
            actor,
        )
        self._replace_signatures(session, version, version_id, now, actor)
        self._replace_attachments(session, version, version_id, now, actor)

    def _replace_collection(
        self,
        session: Session,
        table: Table[Any],
        to_row: ToRow,
        items: Sequence[CollectionItem],
        version_id: int,
        now: datetime,
        actor: str,
    ) -> None:
        self._upsert_rows(
            session, table, to_row, items, version_id, now, actor, ordered=True
        )

    def _replace_signatures(
        self,
        session: Session,
        version: RequirementVersion,
        version_id: int,
        now: datetime,
        actor: str,
    ) -> None:
        self._upsert_rows(
            session,
            REQ_FIRMA,
            mappers.signature_to_row,
            version.signatures,
            version_id,
            now,
            actor,
            ordered=False,
        )

    def _replace_attachments(
        self,
        session: Session,
        version: RequirementVersion,
        version_id: int,
        now: datetime,
        actor: str,
    ) -> None:
        self._upsert_rows(
            session,
            REQ_ANEXO,
            mappers.attachment_to_row,
            version.attachments,
            version_id,
            now,
            actor,
            ordered=True,
        )

    def _upsert_rows(
        self,
        session: Session,
        table: Table[Any],
        to_row: ToRow,
        items: Sequence[PersistableChild],
        version_id: int,
        now: datetime,
        actor: str,
        *,
        ordered: bool,
    ) -> None:
        """Upsert por fila: conserva ids y auditoria; sin delete+insert total."""
        existing_ids = {
            int(row_id)
            for row_id in session.execute(
                select(table.c.ID).where(table.c.VERSION_ID == version_id)
            ).scalars()
        }
        incoming_ids = {item.id for item in items if item.id is not None}
        stale_ids = existing_ids - incoming_ids
        if stale_ids:
            session.execute(delete(table).where(table.c.ID.in_(stale_ids)))

        if ordered and existing_ids & incoming_ids:
            # Reorden en dos fases: primero saca las filas del rango final de
            # ORDEN (la UQ VERSION_ID+ORDEN se valida por sentencia) y luego
            # escriben los valores definitivos.
            session.execute(
                update(table)
                .where(table.c.VERSION_ID == version_id)
                .values(ORDEN=table.c.ORDEN - ORDER_SHIFT)
            )

        for item in items:
            row = to_row(item, version_id=version_id)
            row.pop("ID", None)
            if item.id is None:
                row.update(_insert_audit(now, actor))
                session.execute(insert(table).values(**row))
            else:
                session.execute(
                    update(table)
                    .where(table.c.ID == item.id)
                    .values(**row, **_update_audit(now, actor))
                )

    def _load(self, session: Session, requirement_id: int) -> Requirement:
        row = (
            session.execute(
                select(REQ_REQUERIMIENTO).where(REQ_REQUERIMIENTO.c.ID == requirement_id)
            )
            .mappings()
            .one()
        )
        versions = self._load_versions(session, requirement_id)
        return mappers.requirement_from_row(dict(row), versions=versions)

    def _load_versions(
        self, session: Session, requirement_id: int
    ) -> tuple[RequirementVersion, ...]:
        rows = (
            session.execute(
                select(REQ_VERSION)
                .where(REQ_VERSION.c.REQUERIMIENTO_ID == requirement_id)
                .order_by(REQ_VERSION.c.NUMERO_VERSION)
            )
            .mappings()
            .all()
        )
        return tuple(self._load_version(session, dict(row)) for row in rows)

    def _load_version(self, session: Session, row: Mapping[str, Any]) -> RequirementVersion:
        version_id = int(row["ID"])
        return mappers.version_from_row(
            row,
            objectives=[
                mappers.objective_from_row(item)
                for item in self._collection_rows(session, REQ_OBJETIVO, version_id)
            ],
            considerations=[
                mappers.consideration_from_row(item)
                for item in self._collection_rows(session, REQ_CONSIDERACION, version_id)
            ],
            benefits=[
                mappers.benefit_from_row(item)
                for item in self._collection_rows(session, REQ_BENEFICIO, version_id)
            ],
            restrictions=[
                mappers.restriction_from_row(item)
                for item in self._collection_rows(session, REQ_RESTRICCION, version_id)
            ],
            volumetry=[
                mappers.volumetry_from_row(item)
                for item in self._collection_rows(session, REQ_VOLUMETRIA, version_id)
            ],
            risks=[
                mappers.risk_from_row(item)
                for item in self._collection_rows(session, REQ_RIESGO, version_id)
            ],
            future_requirements_items=[
                mappers.future_requirement_from_row(item)
                for item in self._collection_rows(session, REQ_REQUISITO_FUTURO, version_id)
            ],
            signatures=[
                mappers.signature_from_row(item)
                for item in self._ordered_rows(session, REQ_FIRMA, version_id, REQ_FIRMA.c.ID)
            ],
            attachments=[
                mappers.attachment_from_row(item)
                for item in self._ordered_rows(
                    session, REQ_ANEXO, version_id, REQ_ANEXO.c.ORDEN
                )
            ],
        )

    @staticmethod
    def _collection_rows(
        session: Session, table: Table[Any], version_id: int
    ) -> Sequence[Mapping[str, Any]]:
        return SqlAlchemyRequirementRepository._ordered_rows(
            session, table, version_id, table.c.ORDEN
        )

    @staticmethod
    def _ordered_rows(
        session: Session, table: Table[Any], version_id: int, order_by: Any
    ) -> Sequence[Mapping[str, Any]]:
        rows = (
            session.execute(
                select(table).where(table.c.VERSION_ID == version_id).order_by(order_by)
            )
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]
