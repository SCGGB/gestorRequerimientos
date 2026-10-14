from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Table, delete, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.requirement_repository import RequirementRepository
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

SYSTEM_ACTOR = "SYSTEM"
ToRow = Callable[..., dict[str, Any]]


def _insert_audit(now: datetime) -> dict[str, Any]:
    return {
        "CREATED_AT": now,
        "CREATED_BY": SYSTEM_ACTOR,
        "UPDATED_AT": now,
        "UPDATED_BY": SYSTEM_ACTOR,
    }


def _update_audit(now: datetime) -> dict[str, Any]:
    return {"UPDATED_AT": now, "UPDATED_BY": SYSTEM_ACTOR}


class SqlAlchemyRequirementRepository(RequirementRepository):
    def __init__(self, engine: Engine) -> None:
        self._session_factory: sessionmaker[Session] = create_session_factory(engine)

    def save(self, requirement: Requirement) -> Requirement:
        with self._session_factory.begin() as session:
            requirement_id = self._persist_requirement(session, requirement)
        return self.get(requirement_id)

    def get(self, requirement_id: int) -> Requirement:
        with self._session_factory() as session:
            return self._load(session, requirement_id)

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

    def _persist_requirement(self, session: Session, requirement: Requirement) -> int:
        now = datetime.now()
        requirement_id = self._upsert_container(session, requirement, now)

        version_ids: dict[int, int] = {}
        for version in requirement.versions:
            version_ids[version.number] = self._persist_version(
                session, version, requirement_id, now
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
        self, session: Session, requirement: Requirement, now: datetime
    ) -> int:
        row = mappers.requirement_to_row(requirement)
        row.pop("VERSION_ACTUAL_ID", None)
        if requirement.id is None:
            row.pop("ID", None)
            row.update(_insert_audit(now))
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
            .values(**row, **_update_audit(now))
        )
        return requirement.id

    def _persist_version(
        self,
        session: Session,
        version: RequirementVersion,
        requirement_id: int,
        now: datetime,
    ) -> int:
        row = mappers.version_to_row(version, requirement_id=requirement_id)
        if version.id is None:
            row.pop("ID", None)
            row.update(_insert_audit(now))
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
                .values(**row, **_update_audit(now))
            )

        self._replace_children(session, version_id, version, now)
        return version_id

    def _replace_children(
        self,
        session: Session,
        version_id: int,
        version: RequirementVersion,
        now: datetime,
    ) -> None:
        self._replace_collection(
            session, REQ_OBJETIVO, mappers.objective_to_row, version.objectives, version_id, now
        )
        self._replace_collection(
            session,
            REQ_CONSIDERACION,
            mappers.consideration_to_row,
            version.considerations,
            version_id,
            now,
        )
        self._replace_collection(
            session, REQ_BENEFICIO, mappers.benefit_to_row, version.benefits, version_id, now
        )
        self._replace_collection(
            session,
            REQ_RESTRICCION,
            mappers.restriction_to_row,
            version.restrictions,
            version_id,
            now,
        )
        self._replace_collection(
            session, REQ_VOLUMETRIA, mappers.volumetry_to_row, version.volumetry, version_id, now
        )
        self._replace_collection(
            session, REQ_RIESGO, mappers.risk_to_row, version.risks, version_id, now
        )
        self._replace_collection(
            session,
            REQ_REQUISITO_FUTURO,
            mappers.future_requirement_to_row,
            version.future_requirements_items,
            version_id,
            now,
        )
        self._replace_signatures(session, version, version_id, now)
        self._replace_attachments(session, version, version_id, now)

    def _replace_collection(
        self,
        session: Session,
        table: Table[Any],
        to_row: ToRow,
        items: Sequence[CollectionItem],
        version_id: int,
        now: datetime,
    ) -> None:
        session.execute(delete(table).where(table.c.VERSION_ID == version_id))
        for item in items:
            row = to_row(item, version_id=version_id)
            row.pop("ID", None)
            row.update(_insert_audit(now))
            session.execute(insert(table).values(**row))

    def _replace_signatures(
        self,
        session: Session,
        version: RequirementVersion,
        version_id: int,
        now: datetime,
    ) -> None:
        session.execute(delete(REQ_FIRMA).where(REQ_FIRMA.c.VERSION_ID == version_id))
        for signature in version.signatures:
            row = mappers.signature_to_row(signature, version_id=version_id)
            row.pop("ID", None)
            row.update(_insert_audit(now))
            session.execute(insert(REQ_FIRMA).values(**row))

    def _replace_attachments(
        self,
        session: Session,
        version: RequirementVersion,
        version_id: int,
        now: datetime,
    ) -> None:
        session.execute(delete(REQ_ANEXO).where(REQ_ANEXO.c.VERSION_ID == version_id))
        for attachment in version.attachments:
            row = mappers.attachment_to_row(attachment, version_id=version_id)
            row.pop("ID", None)
            row.update(_insert_audit(now))
            session.execute(insert(REQ_ANEXO).values(**row))

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
