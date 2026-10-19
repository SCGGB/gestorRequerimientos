"""documentos generados: tabla REQ_DOCUMENTO con BLOB DOCX/PDF

Revision ID: 0003_documentos_generados
Revises: 0002_modelo_requerimiento
Create Date: 2026-10-19

"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0003_documentos_generados"
down_revision: str | None = "0002_modelo_requerimiento"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ID = sa.Numeric(precision=19, scale=0)


def _audit_columns() -> list[sa.Column[Any]]:
    return [
        sa.Column("CREATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("CREATED_BY", sa.String(length=100), nullable=True),
        sa.Column("UPDATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("UPDATED_BY", sa.String(length=100), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "REQ_DOCUMENTO",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("REQUERIMIENTO_ID", _ID, nullable=False),
        sa.Column("VERSION_ID", _ID, nullable=False),
        sa.Column("FORMATO", sa.String(length=10), nullable=False),
        sa.Column("PLANTILLA_VERSION", sa.String(length=20), nullable=False),
        sa.Column("NOMBRE_ARCHIVO", sa.String(length=300), nullable=False),
        sa.Column("MIME_TYPE", sa.String(length=150), nullable=False),
        sa.Column("TAMANO_BYTES", _ID, nullable=False),
        sa.Column("CONTENIDO", sa.LargeBinary(), nullable=False),
        sa.Column("GENERADO_AT", sa.TIMESTAMP(), nullable=False),
        sa.Column("GENERADO_BY", sa.String(length=200), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="REQ_DOCUMENTO_PK"),
        sa.ForeignKeyConstraint(
            ["REQUERIMIENTO_ID"],
            ["REQ_REQUERIMIENTO.ID"],
            name="REQ_DOCUMENTO_REQUERIMIENTO_FK",
        ),
        sa.ForeignKeyConstraint(
            ["VERSION_ID"],
            ["REQ_VERSION.ID"],
            name="REQ_DOCUMENTO_VERSION_FK",
        ),
        sa.CheckConstraint("FORMATO IN ('DOCX','PDF')", name="REQ_DOCUMENTO_FORMATO_CK"),
        sa.UniqueConstraint(
            "REQUERIMIENTO_ID",
            "VERSION_ID",
            "FORMATO",
            "GENERADO_AT",
            name="REQ_DOCUMENTO_UQ",
        ),
    )
    op.create_index("REQ_DOCUMENTO_REQUERIMIENTO_IX", "REQ_DOCUMENTO", ["REQUERIMIENTO_ID"])
    op.create_index("REQ_DOCUMENTO_VERSION_IX", "REQ_DOCUMENTO", ["VERSION_ID"])


def downgrade() -> None:
    op.drop_index("REQ_DOCUMENTO_VERSION_IX", table_name="REQ_DOCUMENTO")
    op.drop_index("REQ_DOCUMENTO_REQUERIMIENTO_IX", table_name="REQ_DOCUMENTO")
    op.drop_table("REQ_DOCUMENTO")
