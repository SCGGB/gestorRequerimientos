"""base: tabla SYS_AUDITORIA

Revision ID: 0001_base
Revises:
Create Date: 2026-10-12

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_base"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "SYS_AUDITORIA",
        sa.Column(
            "ID",
            sa.Numeric(precision=19, scale=0),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("ENTIDAD", sa.String(length=100), nullable=False),
        sa.Column("ENTIDAD_ID", sa.Numeric(precision=19, scale=0), nullable=True),
        sa.Column("ACCION", sa.String(length=50), nullable=False),
        sa.Column("ACTOR", sa.String(length=100), nullable=True),
        sa.Column("DETALLE", sa.Text(), nullable=True),
        sa.Column("CREATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("CREATED_BY", sa.String(length=100), nullable=True),
        sa.Column("UPDATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("UPDATED_BY", sa.String(length=100), nullable=True),
        sa.CheckConstraint("DETALLE IS JSON", name="SYS_AUDITORIA_DETALLE_CK"),
        sa.PrimaryKeyConstraint("ID", name="SYS_AUDITORIA_PK"),
    )
    op.create_index(
        "SYS_AUDITORIA_ENTIDAD_IX",
        "SYS_AUDITORIA",
        ["ENTIDAD", "ENTIDAD_ID"],
    )


def downgrade() -> None:
    op.drop_index("SYS_AUDITORIA_ENTIDAD_IX", table_name="SYS_AUDITORIA")
    op.drop_table("SYS_AUDITORIA")
