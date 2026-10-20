"""autenticacion: tablas SYS_USUARIO y SYS_USUARIO_ROL + semilla ADMIN

Revision ID: 0004_usuarios_autenticacion
Revises: 0003_documentos_generados
Create Date: 2026-10-20

"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0004_usuarios_autenticacion"
down_revision: str | None = "0003_documentos_generados"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ID = sa.Numeric(precision=19, scale=0)
_ORDER = sa.Numeric(precision=10, scale=0)


def _audit_columns() -> list[sa.Column[Any]]:
    return [
        sa.Column("CREATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("CREATED_BY", sa.String(length=100), nullable=True),
        sa.Column("UPDATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("UPDATED_BY", sa.String(length=100), nullable=True),
    ]


def _seed_admin() -> None:
    from app.infrastructure.adapters.password_hasher import Pbkdf2PasswordHasher
    from app.infrastructure.config import get_settings

    settings = get_settings()
    username = settings.seed_admin_username
    password = settings.seed_admin_password
    if not username or password is None:
        raise RuntimeError(
            "La semilla del usuario ADMIN requiere SEED_ADMIN_USERNAME y "
            "SEED_ADMIN_PASSWORD en las variables de entorno."
        )

    hasher = Pbkdf2PasswordHasher(settings.password_hash_iterations)
    password_hash = hasher.hash(password.get_secret_value())

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO SYS_USUARIO "
            "(USERNAME, NOMBRE, PASSWORD_HASH, ACTIVO, INTENTOS_FALLIDOS, "
            "CREATED_AT, CREATED_BY) "
            "VALUES (:username, :nombre, :password_hash, 'S', 0, "
            "CURRENT_TIMESTAMP, :created_by)"
        ),
        {
            "username": username,
            "nombre": settings.seed_admin_nombre,
            "password_hash": password_hash,
            "created_by": username,
        },
    )
    connection.execute(
        sa.text(
            "INSERT INTO SYS_USUARIO_ROL (USUARIO_ID, ROL, CREATED_AT, CREATED_BY) "
            "VALUES ("
            "(SELECT ID FROM SYS_USUARIO WHERE USERNAME = :username), "
            "'ADMIN', CURRENT_TIMESTAMP, :created_by)"
        ),
        {"username": username, "created_by": username},
    )


def upgrade() -> None:
    op.create_table(
        "SYS_USUARIO",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("USERNAME", sa.String(length=100), nullable=False),
        sa.Column("NOMBRE", sa.String(length=150), nullable=False),
        sa.Column("PASSWORD_HASH", sa.String(length=255), nullable=False),
        sa.Column("ACTIVO", sa.CHAR(length=1), nullable=False),
        sa.Column("INTENTOS_FALLIDOS", _ORDER, nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="SYS_USUARIO_PK"),
        sa.UniqueConstraint("USERNAME", name="SYS_USUARIO_USERNAME_UQ"),
        sa.CheckConstraint("ACTIVO IN ('S','N')", name="SYS_USUARIO_ACTIVO_CK"),
        sa.CheckConstraint("INTENTOS_FALLIDOS >= 0", name="SYS_USUARIO_INTENTOS_CK"),
    )

    op.create_table(
        "SYS_USUARIO_ROL",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("USUARIO_ID", _ID, nullable=False),
        sa.Column("ROL", sa.String(length=20), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="SYS_USUARIO_ROL_PK"),
        sa.ForeignKeyConstraint(
            ["USUARIO_ID"],
            ["SYS_USUARIO.ID"],
            name="SYS_USUARIO_ROL_USUARIO_FK",
        ),
        sa.UniqueConstraint("USUARIO_ID", "ROL", name="SYS_USUARIO_ROL_UQ"),
        sa.CheckConstraint(
            "ROL IN ('ELABORO','REVISO','AUTORIZO','ADMIN')",
            name="SYS_USUARIO_ROL_ROL_CK",
        ),
    )
    op.create_index("SYS_USUARIO_ROL_USUARIO_IX", "SYS_USUARIO_ROL", ["USUARIO_ID"])

    _seed_admin()


def downgrade() -> None:
    op.drop_index("SYS_USUARIO_ROL_USUARIO_IX", table_name="SYS_USUARIO_ROL")
    op.drop_table("SYS_USUARIO_ROL")
    op.drop_table("SYS_USUARIO")
