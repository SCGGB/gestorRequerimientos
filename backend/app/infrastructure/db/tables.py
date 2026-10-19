from __future__ import annotations

from typing import Any

from sqlalchemy import (
    CHAR,
    TIMESTAMP,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Identity,
    Index,
    LargeBinary,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

_ID = Numeric(19, 0)
_ORDER = Numeric(10, 0)


def _audit_columns() -> tuple[Column[Any], ...]:
    return (
        Column("CREATED_AT", TIMESTAMP, nullable=True),
        Column("CREATED_BY", String(100), nullable=True),
        Column("UPDATED_AT", TIMESTAMP, nullable=True),
        Column("UPDATED_BY", String(100), nullable=True),
    )


ROLES = ("ELABORO", "REVISO", "AUTORIZO")
STATUS = ("BORRADOR", "EN_REVISION", "VALIDADO", "APROBADO", "GENERADO", "CANCELADO")

REQ_TIPO_CAMBIO = Table(
    "REQ_TIPO_CAMBIO",
    metadata,
    Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
    Column("CODIGO", String(50), nullable=False),
    Column("NOMBRE", String(100), nullable=False),
    Column("ACTIVO", CHAR(1), nullable=False),
    *_audit_columns(),
    UniqueConstraint("CODIGO", name="REQ_TIPO_CAMBIO_CODIGO_UQ"),
    CheckConstraint("ACTIVO IN ('S','N')", name="REQ_TIPO_CAMBIO_ACTIVO_CK"),
)

REQ_CARGO = Table(
    "REQ_CARGO",
    metadata,
    Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
    Column("ROL", String(20), nullable=False),
    Column("NOMBRE", String(100), nullable=False),
    Column("PREDETERMINADO", CHAR(1), nullable=False),
    Column("ACTIVO", CHAR(1), nullable=False),
    *_audit_columns(),
    CheckConstraint("ROL IN ('ELABORO','REVISO','AUTORIZO')", name="REQ_CARGO_ROL_CK"),
    CheckConstraint("PREDETERMINADO IN ('S','N')", name="REQ_CARGO_PREDETERMINADO_CK"),
    CheckConstraint("ACTIVO IN ('S','N')", name="REQ_CARGO_ACTIVO_CK"),
    Index("REQ_CARGO_ROL_IX", "ROL"),
)

REQ_REQUERIMIENTO = Table(
    "REQ_REQUERIMIENTO",
    metadata,
    Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
    Column("FOLIO", _ID, nullable=False),
    Column("ESTADO", String(20), nullable=False),
    Column("VERSION_ACTUAL_ID", _ID, nullable=True),
    *_audit_columns(),
    UniqueConstraint("FOLIO", name="REQ_REQUERIMIENTO_FOLIO_UQ"),
    CheckConstraint(
        "ESTADO IN ('BORRADOR','EN_REVISION','VALIDADO','APROBADO','GENERADO','CANCELADO')",
        name="REQ_REQUERIMIENTO_ESTADO_CK",
    ),
)

REQ_VERSION = Table(
    "REQ_VERSION",
    metadata,
    Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
    Column(
        "REQUERIMIENTO_ID",
        _ID,
        ForeignKey("REQ_REQUERIMIENTO.ID", name="REQ_VERSION_REQUERIMIENTO_FK"),
        nullable=False,
    ),
    Column("NUMERO_VERSION", _ORDER, nullable=False),
    Column("VERSION_DOCUMENTO", String(20), nullable=False),
    Column("FECHA_VERSION", Date, nullable=False),
    Column("TITULO", String(300), nullable=False),
    Column(
        "TIPO_CAMBIO_ID",
        _ID,
        ForeignKey("REQ_TIPO_CAMBIO.ID", name="REQ_VERSION_TIPO_CAMBIO_FK"),
        nullable=True,
    ),
    Column("SISTEMA", String(200), nullable=True),
    Column("NECESIDAD_ACTUAL", Text, nullable=True),
    Column("CONTEXTO_DESCRIPCION", Text, nullable=True),
    Column("CONTEXTO_MANEJO_ERRORES", Text, nullable=True),
    Column("USUARIOS_PERMISOS", Text, nullable=True),
    Column("REQUISITOS_FUTUROS_APLICA", CHAR(1), nullable=False),
    Column("REQUISITOS_FUTUROS_TEXTO", Text, nullable=True),
    Column("CAMPOS_DINAMICOS", Text, nullable=True),
    Column("CONGELADA", CHAR(1), nullable=False),
    *_audit_columns(),
    UniqueConstraint(
        "REQUERIMIENTO_ID", "NUMERO_VERSION", name="REQ_VERSION_REQUERIMIENTO_NUMERO_UQ"
    ),
    CheckConstraint("CONGELADA IN ('S','N')", name="REQ_VERSION_CONGELADA_CK"),
    CheckConstraint(
        "REQUISITOS_FUTUROS_APLICA IN ('S','N')", name="REQ_VERSION_REQUISITOS_FUTUROS_CK"
    ),
    CheckConstraint("CAMPOS_DINAMICOS IS JSON", name="REQ_VERSION_CAMPOS_DINAMICOS_CK"),
    Index("REQ_VERSION_REQUERIMIENTO_IX", "REQUERIMIENTO_ID"),
)
# Colecciones
_COLLECTION_TABLES = (
    "REQ_OBJETIVO",
    "REQ_CONSIDERACION",
    "REQ_RESTRICCION",
    "REQ_VOLUMETRIA",
    "REQ_RIESGO",
    "REQ_REQUISITO_FUTURO",
)


def _collection_table(name: str, *, with_benefit_kind: bool = False) -> Table[Any]:
    cols: list[Column[Any]] = [
        Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
        Column(
            "VERSION_ID",
            _ID,
            ForeignKey("REQ_VERSION.ID", name=f"{name}_VERSION_FK"),
            nullable=False,
        ),
        Column("ORDEN", _ORDER, nullable=False),
        Column("CONTENIDO", Text, nullable=False),
        Column("ACTIVO", CHAR(1), nullable=False),
    ]
    if with_benefit_kind:
        cols.append(Column("TIPO", String(15), nullable=False))
    table = Table(
        name,
        metadata,
        *cols,
        *_audit_columns(),
        UniqueConstraint("VERSION_ID", "ORDEN", name=f"{name}_VERSION_ORDEN_UQ"),
        CheckConstraint("ACTIVO IN ('S','N')", name=f"{name}_ACTIVO_CK"),
        Index(f"{name}_VERSION_IX", "VERSION_ID"),
    )
    if with_benefit_kind:
        table.append_constraint(
            CheckConstraint("TIPO IN ('CUALITATIVO','CUANTITATIVO')", name=f"{name}_TIPO_CK")
        )
    return table


REQ_OBJETIVO = _collection_table("REQ_OBJETIVO")
REQ_CONSIDERACION = _collection_table("REQ_CONSIDERACION")
REQ_RESTRICCION = _collection_table("REQ_RESTRICCION")
REQ_VOLUMETRIA = _collection_table("REQ_VOLUMETRIA")
REQ_RIESGO = _collection_table("REQ_RIESGO")
REQ_REQUISITO_FUTURO = _collection_table("REQ_REQUISITO_FUTURO")
REQ_BENEFICIO = _collection_table("REQ_BENEFICIO", with_benefit_kind=True)

REQ_ANEXO = Table(
    "REQ_ANEXO",
    metadata,
    Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
    Column(
        "VERSION_ID", _ID, ForeignKey("REQ_VERSION.ID", name="REQ_ANEXO_VERSION_FK"), nullable=False
    ),
    Column("ORDEN", _ORDER, nullable=False),
    Column("NOMBRE", String(255), nullable=False),
    Column("TIPO_MIME", String(100), nullable=True),
    Column("STORAGE_KEY", String(500), nullable=False),
    Column("LEYENDA", String(255), nullable=True),
    Column("ACTIVO", CHAR(1), nullable=False),
    *_audit_columns(),
    CheckConstraint("ACTIVO IN ('S','N')", name="REQ_ANEXO_ACTIVO_CK"),
)

REQ_FIRMA = Table(
    "REQ_FIRMA",
    metadata,
    Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
    Column(
        "VERSION_ID", _ID, ForeignKey("REQ_VERSION.ID", name="REQ_FIRMA_VERSION_FK"), nullable=False
    ),
    Column("ROL", String(20), nullable=False),
    Column("NOMBRE", String(150), nullable=False),
    Column("CARGO", String(150), nullable=False),
    Column("CARGO_ID", _ID, ForeignKey("REQ_CARGO.ID", name="REQ_FIRMA_CARGO_FK"), nullable=True),
    *_audit_columns(),
    CheckConstraint("ROL IN ('ELABORO','REVISO','AUTORIZO')", name="REQ_FIRMA_ROL_CK"),
    Index("REQ_FIRMA_VERSION_IX", "VERSION_ID"),
)

DOCUMENT_FORMATS = ("DOCX", "PDF")

REQ_DOCUMENTO = Table(
    "REQ_DOCUMENTO",
    metadata,
    Column("ID", _ID, Identity(always=True), primary_key=True, nullable=False),
    Column(
        "REQUERIMIENTO_ID",
        _ID,
        ForeignKey("REQ_REQUERIMIENTO.ID", name="REQ_DOCUMENTO_REQUERIMIENTO_FK"),
        nullable=False,
    ),
    Column(
        "VERSION_ID",
        _ID,
        ForeignKey("REQ_VERSION.ID", name="REQ_DOCUMENTO_VERSION_FK"),
        nullable=False,
    ),
    Column("FORMATO", String(10), nullable=False),
    Column("PLANTILLA_VERSION", String(20), nullable=False),
    Column("NOMBRE_ARCHIVO", String(300), nullable=False),
    Column("MIME_TYPE", String(150), nullable=False),
    Column("TAMANO_BYTES", _ID, nullable=False),
    Column("CONTENIDO", LargeBinary, nullable=False),
    Column("GENERADO_AT", TIMESTAMP, nullable=False),
    Column("GENERADO_BY", String(200), nullable=False),
    *_audit_columns(),
    CheckConstraint(
        "FORMATO IN ('DOCX','PDF')", name="REQ_DOCUMENTO_FORMATO_CK"
    ),
    UniqueConstraint(
        "REQUERIMIENTO_ID",
        "VERSION_ID",
        "FORMATO",
        "GENERADO_AT",
        name="REQ_DOCUMENTO_UQ",
    ),
    Index("REQ_DOCUMENTO_REQUERIMIENTO_IX", "REQUERIMIENTO_ID"),
    Index("REQ_DOCUMENTO_VERSION_IX", "VERSION_ID"),
)
