from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.application.errors import ApplicationError, DataConflictError, UsernameTakenError
from app.application.ports.user_repository import UserRepository
from app.domain.auth.roles import Role
from app.domain.auth.user import User
from app.infrastructure.database import create_session_factory
from app.infrastructure.db import mappers
from app.infrastructure.db.tables import SYS_USUARIO, SYS_USUARIO_ROL

USERNAME_UNIQUE_CONSTRAINT = "SYS_USUARIO_USERNAME_UQ"


def _map_integrity_error(exc: IntegrityError) -> ApplicationError:
    if USERNAME_UNIQUE_CONSTRAINT in str(exc):
        return UsernameTakenError()
    return DataConflictError()


class SqlAlchemyUserRepository(UserRepository):
    """Persistencia de SYS_USUARIO y SYS_USUARIO_ROL con SQLAlchemy Core.

    Baja logica con ``ACTIVO='N'`` (sin DELETE); las asignaciones de roles se
    reemplazan por diferencia de conjuntos.
    """

    def __init__(self, engine: Engine) -> None:
        self._session_factory: sessionmaker[Session] = create_session_factory(engine)

    def get_by_username(self, username: str) -> User | None:
        with self._session_factory() as session:
            row = (
                session.execute(select(SYS_USUARIO).where(SYS_USUARIO.c.USERNAME == username))
                .mappings()
                .first()
            )
            if row is None:
                return None
            return self._load_user(session, dict(row))

    def get(self, user_id: int) -> User | None:
        with self._session_factory() as session:
            row = (
                session.execute(select(SYS_USUARIO).where(SYS_USUARIO.c.ID == user_id))
                .mappings()
                .first()
            )
            if row is None:
                return None
            return self._load_user(session, dict(row))

    def list_all(self) -> Sequence[User]:
        with self._session_factory() as session:
            rows = (
                session.execute(select(SYS_USUARIO).order_by(SYS_USUARIO.c.USERNAME))
                .mappings()
                .all()
            )
            return tuple(self._load_user(session, dict(row)) for row in rows)

    def save(self, user: User) -> User:
        try:
            with self._session_factory.begin() as session:
                user_id = self._upsert_user(session, user)
                self._replace_roles(session, user_id, user)
        except IntegrityError as exc:
            raise _map_integrity_error(exc) from exc
        saved = self.get(user_id)
        if saved is None:
            raise DataConflictError("El usuario guardado no pudo releerse.")
        return saved

    def _upsert_user(self, session: Session, user: User) -> int:
        now = datetime.now()
        row = mappers.user_to_row(user)
        row.pop("ID", None)
        if user.id is None:
            row.update(_insert_audit(now))
            result = session.execute(
                insert(SYS_USUARIO).values(**row).returning(SYS_USUARIO.c.ID)
            )
            return int(result.scalar_one())

        session.execute(
            update(SYS_USUARIO)
            .where(SYS_USUARIO.c.ID == user.id)
            .values(**row, **_update_audit(now))
        )
        return user.id

    def _replace_roles(self, session: Session, user_id: int, user: User) -> None:
        now = datetime.now()
        existing = self._load_roles(session, user_id)
        for role in user.roles - existing:
            session.execute(
                insert(SYS_USUARIO_ROL).values(
                    {
                        **mappers.user_role_to_row(user_id=user_id, role=role),
                        **_insert_audit(now),
                    }
                )
            )
        for role in existing - user.roles:
            session.execute(
                delete(SYS_USUARIO_ROL).where(
                    SYS_USUARIO_ROL.c.USUARIO_ID == user_id,
                    SYS_USUARIO_ROL.c.ROL == role.value,
                )
            )

    def _load_user(self, session: Session, row: dict[str, Any]) -> User:
        roles = self._load_roles(session, int(row["ID"]))
        return mappers.user_from_row(row, roles=roles)

    @staticmethod
    def _load_roles(session: Session, user_id: int) -> frozenset[Role]:
        values = session.execute(
            select(SYS_USUARIO_ROL.c.ROL).where(SYS_USUARIO_ROL.c.USUARIO_ID == user_id)
        ).scalars()
        return frozenset(Role(str(value)) for value in values)


def _insert_audit(now: datetime) -> dict[str, Any]:
    return {
        "CREATED_AT": now,
        "CREATED_BY": "SYSTEM",
        "UPDATED_AT": now,
        "UPDATED_BY": "SYSTEM",
    }


def _update_audit(now: datetime) -> dict[str, Any]:
    return {"UPDATED_AT": now, "UPDATED_BY": "SYSTEM"}
