"""modelo de requerimiento: contenedor, versiones, colecciones, firmas y anexos

Revision ID: 0002_modelo_requerimiento
Revises: 0001_base
Create Date: 2026-10-13

"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0002_modelo_requerimiento"
down_revision: str | None = "0001_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ID = sa.Numeric(precision=19, scale=0)
_ORDER = sa.Numeric(precision=10, scale=0)

_STATUS_CHECK = (
    "ESTADO IN ('BORRADOR','EN_REVISION','VALIDADO','APROBADO','GENERADO','CANCELADO')"
)
_ROLES = "('ELABORO','REVISO','AUTORIZO')"
_BENEFIT_KINDS = "('CUALITATIVO','CUANTITATIVO')"

_CHANGE_TYPES: tuple[tuple[str, str], ...] = (
    ("NUEVA_FUNCIONALIDAD", "Nueva funcionalidad"),
    ("CORRECCION", "Corrección"),
    ("REPORTE", "Reporte"),
    ("INTEGRACION", "Integración"),
    ("BASE_DATOS", "Base de datos"),
    ("MEJORA_TECNICA", "Mejora técnica"),
)

_DEFAULT_POSITIONS: tuple[tuple[str, str], ...] = (
    ("ELABORO", "Elaborador"),
    ("REVISO", "Revisor"),
    ("AUTORIZO", "Autorizador"),
)

_COLLECTION_TABLES: tuple[str, ...] = (
    "REQ_OBJETIVO",
    "REQ_CONSIDERACION",
    "REQ_RESTRICCION",
    "REQ_VOLUMETRIA",
    "REQ_RIESGO",
    "REQ_REQUISITO_FUTURO",
)


def _audit_columns() -> list[sa.Column[Any]]:
    return [
        sa.Column("CREATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("CREATED_BY", sa.String(length=100), nullable=True),
        sa.Column("UPDATED_AT", sa.TIMESTAMP(), nullable=True),
        sa.Column("UPDATED_BY", sa.String(length=100), nullable=True),
    ]


def _create_collection_table(table_name: str, *, with_benefit_kind: bool = False) -> None:
    columns: list[sa.Column[Any]] = [
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("VERSION_ID", _ID, nullable=False),
        sa.Column("ORDEN", _ORDER, nullable=False),
        sa.Column("CONTENIDO", sa.Text(), nullable=True),
        sa.Column("ACTIVO", sa.String(length=1), nullable=False),
    ]
    if with_benefit_kind:
        columns.append(sa.Column("TIPO", sa.String(length=15), nullable=False))

    constraints: list[sa.schema.SchemaItem] = [
        sa.PrimaryKeyConstraint("ID", name=f"{table_name}_PK"),
        sa.ForeignKeyConstraint(
            ["VERSION_ID"],
            ["REQ_VERSION.ID"],
            name=f"{table_name}_VERSION_FK",
        ),
        sa.CheckConstraint("ACTIVO IN ('S','N')", name=f"{table_name}_ACTIVO_CK"),
        sa.UniqueConstraint("VERSION_ID", "ORDEN", name=f"{table_name}_VERSION_ORDEN_UQ"),
    ]
    if with_benefit_kind:
        constraints.append(
            sa.CheckConstraint(f"TIPO IN {_BENEFIT_KINDS}", name=f"{table_name}_TIPO_CK")
        )

    op.create_table(table_name, *columns, *constraints, *_audit_columns())
    op.create_index(f"{table_name}_VERSION_IX", table_name, ["VERSION_ID"])


def _seed_change_types() -> None:
    for codigo, nombre in _CHANGE_TYPES:
        op.execute(
            sa.text(
                "INSERT INTO REQ_TIPO_CAMBIO "
                "(CODIGO, NOMBRE, ACTIVO, CREATED_AT, CREATED_BY, UPDATED_AT, UPDATED_BY) "
                f"VALUES ('{codigo}', '{nombre}', 'S', CURRENT_TIMESTAMP, 'SYSTEM', "
                "CURRENT_TIMESTAMP, 'SYSTEM')"
            )
        )


def _seed_positions() -> None:
    for rol, nombre in _DEFAULT_POSITIONS:
        op.execute(
            sa.text(
                "INSERT INTO REQ_CARGO "
                "(ROL, NOMBRE, PREDETERMINADO, ACTIVO, CREATED_AT, CREATED_BY, "
                "UPDATED_AT, UPDATED_BY) "
                f"VALUES ('{rol}', '{nombre}', 'S', 'S', CURRENT_TIMESTAMP, 'SYSTEM', "
                "CURRENT_TIMESTAMP, 'SYSTEM')"
            )
        )


def upgrade() -> None:
    op.create_table(
        "REQ_TIPO_CAMBIO",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("CODIGO", sa.String(length=50), nullable=False),
        sa.Column("NOMBRE", sa.String(length=100), nullable=False),
        sa.Column("ACTIVO", sa.String(length=1), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="REQ_TIPO_CAMBIO_PK"),
        sa.UniqueConstraint("CODIGO", name="REQ_TIPO_CAMBIO_CODIGO_UQ"),
        sa.CheckConstraint("ACTIVO IN ('S','N')", name="REQ_TIPO_CAMBIO_ACTIVO_CK"),
    )

    op.create_table(
        "REQ_CARGO",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("ROL", sa.String(length=20), nullable=False),
        sa.Column("NOMBRE", sa.String(length=100), nullable=False),
        sa.Column("PREDETERMINADO", sa.String(length=1), nullable=False),
        sa.Column("ACTIVO", sa.String(length=1), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="REQ_CARGO_PK"),
        sa.CheckConstraint(f"ROL IN {_ROLES}", name="REQ_CARGO_ROL_CK"),
        sa.CheckConstraint("PREDETERMINADO IN ('S','N')", name="REQ_CARGO_PREDETERMINADO_CK"),
        sa.CheckConstraint("ACTIVO IN ('S','N')", name="REQ_CARGO_ACTIVO_CK"),
    )
    op.create_index("REQ_CARGO_ROL_IX", "REQ_CARGO", ["ROL"])

    op.create_table(
        "REQ_REQUERIMIENTO",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("FOLIO", _ID, nullable=False),
        sa.Column("ESTADO", sa.String(length=20), nullable=False),
        sa.Column("VERSION_ACTUAL_ID", _ID, nullable=True),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="REQ_REQUERIMIENTO_PK"),
        sa.UniqueConstraint("FOLIO", name="REQ_REQUERIMIENTO_FOLIO_UQ"),
        sa.CheckConstraint(_STATUS_CHECK, name="REQ_REQUERIMIENTO_ESTADO_CK"),
    )

    op.create_table(
        "REQ_VERSION",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("REQUERIMIENTO_ID", _ID, nullable=False),
        sa.Column("NUMERO_VERSION", _ORDER, nullable=False),
        sa.Column("VERSION_DOCUMENTO", sa.String(length=20), nullable=False),
        sa.Column("FECHA_VERSION", sa.Date(), nullable=False),
        sa.Column("TITULO", sa.String(length=300), nullable=False),
        sa.Column("TIPO_CAMBIO_ID", _ID, nullable=True),
        sa.Column("SISTEMA", sa.String(length=200), nullable=True),
        sa.Column("NECESIDAD_ACTUAL", sa.Text(), nullable=True),
        sa.Column("CONTEXTO_DESCRIPCION", sa.Text(), nullable=True),
        sa.Column("CONTEXTO_MANEJO_ERRORES", sa.Text(), nullable=True),
        sa.Column("USUARIOS_PERMISOS", sa.Text(), nullable=True),
        sa.Column("REQUISITOS_FUTUROS_APLICA", sa.String(length=1), nullable=False),
        sa.Column("REQUISITOS_FUTUROS_TEXTO", sa.Text(), nullable=True),
        sa.Column("CAMPOS_DINAMICOS", sa.Text(), nullable=True),
        sa.Column("CONGELADA", sa.String(length=1), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="REQ_VERSION_PK"),
        sa.ForeignKeyConstraint(
            ["REQUERIMIENTO_ID"],
            ["REQ_REQUERIMIENTO.ID"],
            name="REQ_VERSION_REQUERIMIENTO_FK",
        ),
        sa.ForeignKeyConstraint(
            ["TIPO_CAMBIO_ID"],
            ["REQ_TIPO_CAMBIO.ID"],
            name="REQ_VERSION_TIPO_CAMBIO_FK",
        ),
        sa.UniqueConstraint(
            "REQUERIMIENTO_ID",
            "NUMERO_VERSION",
            name="REQ_VERSION_REQUERIMIENTO_NUMERO_UQ",
        ),
        sa.CheckConstraint("CONGELADA IN ('S','N')", name="REQ_VERSION_CONGELADA_CK"),
        sa.CheckConstraint(
            "REQUISITOS_FUTUROS_APLICA IN ('S','N')",
            name="REQ_VERSION_REQUISITOS_FUTUROS_CK",
        ),
        sa.CheckConstraint("CAMPOS_DINAMICOS IS JSON", name="REQ_VERSION_CAMPOS_DINAMICOS_CK"),
    )
    op.create_index("REQ_VERSION_REQUERIMIENTO_IX", "REQ_VERSION", ["REQUERIMIENTO_ID"])

    op.create_foreign_key(
        "REQ_REQUERIMIENTO_VERSION_FK",
        "REQ_REQUERIMIENTO",
        "REQ_VERSION",
        ["VERSION_ACTUAL_ID"],
        ["ID"],
    )

    for table_name in _COLLECTION_TABLES:
        _create_collection_table(table_name)
    _create_collection_table("REQ_BENEFICIO", with_benefit_kind=True)

    op.create_table(
        "REQ_ANEXO",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("VERSION_ID", _ID, nullable=False),
        sa.Column("ORDEN", _ORDER, nullable=False),
        sa.Column("NOMBRE", sa.String(length=255), nullable=False),
        sa.Column("TIPO_MIME", sa.String(length=100), nullable=True),
        sa.Column("STORAGE_KEY", sa.String(length=500), nullable=False),
        sa.Column("LEYENDA", sa.String(length=255), nullable=True),
        sa.Column("ACTIVO", sa.String(length=1), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="REQ_ANEXO_PK"),
        sa.ForeignKeyConstraint(["VERSION_ID"], ["REQ_VERSION.ID"], name="REQ_ANEXO_VERSION_FK"),
        sa.CheckConstraint("ACTIVO IN ('S','N')", name="REQ_ANEXO_ACTIVO_CK"),
    )

    op.create_table(
        "REQ_FIRMA",
        sa.Column("ID", _ID, sa.Identity(always=True), nullable=False),
        sa.Column("VERSION_ID", _ID, nullable=False),
        sa.Column("ROL", sa.String(length=20), nullable=False),
        sa.Column("NOMBRE", sa.String(length=150), nullable=False),
        sa.Column("CARGO", sa.String(length=150), nullable=False),
        sa.Column("CARGO_ID", _ID, nullable=True),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("ID", name="REQ_FIRMA_PK"),
        sa.ForeignKeyConstraint(["VERSION_ID"], ["REQ_VERSION.ID"], name="REQ_FIRMA_VERSION_FK"),
        sa.ForeignKeyConstraint(["CARGO_ID"], ["REQ_CARGO.ID"], name="REQ_FIRMA_CARGO_FK"),
        sa.CheckConstraint(f"ROL IN {_ROLES}", name="REQ_FIRMA_ROL_CK"),
    )
    op.create_index("REQ_FIRMA_VERSION_IX", "REQ_FIRMA", ["VERSION_ID"])

    _seed_change_types()
    _seed_positions()


def downgrade() -> None:
    op.drop_constraint(
        "REQ_REQUERIMIENTO_VERSION_FK",
        "REQ_REQUERIMIENTO",
        type_="foreignkey",
    )

    op.drop_index("REQ_FIRMA_VERSION_IX", table_name="REQ_FIRMA")
    op.drop_table("REQ_FIRMA")
    op.drop_table("REQ_ANEXO")

    for table_name in ("REQ_BENEFICIO", *_COLLECTION_TABLES):
        op.drop_index(f"{table_name}_VERSION_IX", table_name=table_name)
        op.drop_table(table_name)

    op.drop_index("REQ_VERSION_REQUERIMIENTO_IX", table_name="REQ_VERSION")
    op.drop_table("REQ_VERSION")
    op.drop_table("REQ_REQUERIMIENTO")
    op.drop_index("REQ_CARGO_ROL_IX", table_name="REQ_CARGO")
    op.drop_table("REQ_CARGO")
    op.drop_table("REQ_TIPO_CAMBIO")
