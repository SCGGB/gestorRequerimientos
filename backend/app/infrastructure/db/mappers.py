from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from app.domain.requirement.attachment import Attachment
from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.items import (
    Benefit,
    CollectionItem,
    Consideration,
    FutureRequirementItem,
    Objective,
    Restriction,
    Risk,
    Volumetry,
)
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion

Row = Mapping[str, Any]


def _flag_to_char(value: bool) -> str:
    return "S" if value else "N"


def _char_to_flag(value: object) -> bool:
    return value == "S"


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def dynamic_fields_to_json(fields: Mapping[str, Any]) -> str | None:
    """Serializa los campos dinamicos a JSON (o ``None`` si estan vacios)."""
    if not fields:
        return None
    return json.dumps(dict(fields), ensure_ascii=False)


def dynamic_fields_from_json(value: Any) -> Mapping[str, Any]:
    """Deserializa ``CAMPOS_DINAMICOS``; vacio o nulo devuelve un mapeo vacio."""
    if value is None or value == "":
        return {}
    if isinstance(value, Mapping):
        parsed: Any = dict(value)
    else:
        parsed = json.loads(str(value))
    if not isinstance(parsed, dict):
        raise ValueError("CAMPOS_DINAMICOS debe ser un objeto JSON.")
    return {str(key): item for key, item in parsed.items()}


# --- Catalogos -------------------------------------------------------------


def change_type_to_row(change_type: ChangeType) -> dict[str, Any]:
    row: dict[str, Any] = {
        "CODIGO": change_type.code,
        "NOMBRE": change_type.name,
        "ACTIVO": _flag_to_char(change_type.active),
    }
    if change_type.id is not None:
        row["ID"] = change_type.id
    return row


def change_type_from_row(row: Row) -> ChangeType:
    return ChangeType(
        id=_optional_int(row.get("ID")),
        code=str(row["CODIGO"]),
        name=str(row["NOMBRE"]),
        active=_char_to_flag(row["ACTIVO"]),
    )


def position_to_row(position: Position) -> dict[str, Any]:
    row: dict[str, Any] = {
        "ROL": position.role.value,
        "NOMBRE": position.name,
        "PREDETERMINADO": _flag_to_char(position.is_default),
        "ACTIVO": _flag_to_char(position.active),
    }
    if position.id is not None:
        row["ID"] = position.id
    return row


def position_from_row(row: Row) -> Position:
    return Position(
        id=_optional_int(row.get("ID")),
        role=SignatureRole(str(row["ROL"])),
        name=str(row["NOMBRE"]),
        is_default=_char_to_flag(row["PREDETERMINADO"]),
        active=_char_to_flag(row["ACTIVO"]),
    )


# --- Colecciones ordenadas -------------------------------------------------


def _item_to_row(item: CollectionItem, *, version_id: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "VERSION_ID": version_id,
        "ORDEN": item.order,
        "CONTENIDO": item.content,
        "ACTIVO": _flag_to_char(item.active),
    }
    if item.id is not None:
        row["ID"] = item.id
    return row


def _item_from_row[ItemT: CollectionItem](item_type: type[ItemT], row: Row) -> ItemT:
    return item_type(
        id=_optional_int(row.get("ID")),
        order=int(row["ORDEN"]),
        content=str(row["CONTENIDO"]),
        active=_char_to_flag(row["ACTIVO"]),
    )


def objective_to_row(objective: Objective, *, version_id: int) -> dict[str, Any]:
    return _item_to_row(objective, version_id=version_id)


def objective_from_row(row: Row) -> Objective:
    return _item_from_row(Objective, row)


def consideration_to_row(consideration: Consideration, *, version_id: int) -> dict[str, Any]:
    return _item_to_row(consideration, version_id=version_id)


def consideration_from_row(row: Row) -> Consideration:
    return _item_from_row(Consideration, row)


def restriction_to_row(restriction: Restriction, *, version_id: int) -> dict[str, Any]:
    return _item_to_row(restriction, version_id=version_id)


def restriction_from_row(row: Row) -> Restriction:
    return _item_from_row(Restriction, row)


def volumetry_to_row(volumetry: Volumetry, *, version_id: int) -> dict[str, Any]:
    return _item_to_row(volumetry, version_id=version_id)


def volumetry_from_row(row: Row) -> Volumetry:
    return _item_from_row(Volumetry, row)


def risk_to_row(risk: Risk, *, version_id: int) -> dict[str, Any]:
    return _item_to_row(risk, version_id=version_id)


def risk_from_row(row: Row) -> Risk:
    return _item_from_row(Risk, row)


def future_requirement_to_row(
    item: FutureRequirementItem, *, version_id: int
) -> dict[str, Any]:
    return _item_to_row(item, version_id=version_id)


def future_requirement_from_row(row: Row) -> FutureRequirementItem:
    return _item_from_row(FutureRequirementItem, row)


def benefit_to_row(benefit: Benefit, *, version_id: int) -> dict[str, Any]:
    row = _item_to_row(benefit, version_id=version_id)
    row["TIPO"] = benefit.kind.value
    return row


def benefit_from_row(row: Row) -> Benefit:
    return Benefit(
        id=_optional_int(row.get("ID")),
        order=int(row["ORDEN"]),
        content=str(row["CONTENIDO"]),
        active=_char_to_flag(row["ACTIVO"]),
        kind=BenefitKind(str(row["TIPO"])),
    )


# --- Firmas y anexos -------------------------------------------------------


def signature_to_row(signature: Signature, *, version_id: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "VERSION_ID": version_id,
        "ROL": signature.role.value,
        "NOMBRE": signature.name,
        "CARGO": signature.position,
        "CARGO_ID": signature.position_id,
    }
    if signature.id is not None:
        row["ID"] = signature.id
    return row


def signature_from_row(row: Row) -> Signature:
    return Signature(
        id=_optional_int(row.get("ID")),
        version_id=_optional_int(row.get("VERSION_ID")),
        role=SignatureRole(str(row["ROL"])),
        name=str(row["NOMBRE"]),
        position=str(row["CARGO"]),
        position_id=_optional_int(row.get("CARGO_ID")),
    )


def attachment_to_row(attachment: Attachment, *, version_id: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "VERSION_ID": version_id,
        "ORDEN": attachment.order,
        "NOMBRE": attachment.name,
        "TIPO_MIME": attachment.mime_type,
        "STORAGE_KEY": attachment.storage_key,
        "LEYENDA": attachment.caption,
        "ACTIVO": _flag_to_char(attachment.active),
    }
    if attachment.id is not None:
        row["ID"] = attachment.id
    return row


def attachment_from_row(row: Row) -> Attachment:
    return Attachment(
        id=_optional_int(row.get("ID")),
        version_id=_optional_int(row.get("VERSION_ID")),
        order=int(row["ORDEN"]),
        name=str(row["NOMBRE"]),
        mime_type=str(row["TIPO_MIME"]) if row.get("TIPO_MIME") is not None else None,
        storage_key=str(row["STORAGE_KEY"]),
        caption=str(row["LEYENDA"]) if row.get("LEYENDA") is not None else None,
        active=_char_to_flag(row["ACTIVO"]),
    )


# --- Version y contenedor --------------------------------------------------


def version_to_row(version: RequirementVersion, *, requirement_id: int) -> dict[str, Any]:
    row: dict[str, Any] = {
        "REQUERIMIENTO_ID": requirement_id,
        "NUMERO_VERSION": version.number,
        "VERSION_DOCUMENTO": version.document_version,
        "FECHA_VERSION": version.version_date,
        "TITULO": version.title,
        "TIPO_CAMBIO_ID": version.change_type_id,
        "SISTEMA": version.system,
        "NECESIDAD_ACTUAL": version.current_need,
        "CONTEXTO_DESCRIPCION": version.context_description,
        "CONTEXTO_MANEJO_ERRORES": version.context_error_handling,
        "USUARIOS_PERMISOS": version.users_permissions,
        "REQUISITOS_FUTUROS_APLICA": _flag_to_char(version.future_requirements_applies),
        "REQUISITOS_FUTUROS_TEXTO": version.future_requirements_text,
        "CAMPOS_DINAMICOS": dynamic_fields_to_json(version.dynamic_fields),
        "CONGELADA": _flag_to_char(version.frozen),
    }
    if version.id is not None:
        row["ID"] = version.id
    return row


def version_from_row(
    row: Row,
    *,
    objectives: Sequence[Objective] = (),
    considerations: Sequence[Consideration] = (),
    benefits: Sequence[Benefit] = (),
    restrictions: Sequence[Restriction] = (),
    volumetry: Sequence[Volumetry] = (),
    risks: Sequence[Risk] = (),
    future_requirements_items: Sequence[FutureRequirementItem] = (),
    signatures: Sequence[Signature] = (),
    attachments: Sequence[Attachment] = (),
) -> RequirementVersion:
    return RequirementVersion(
        id=_optional_int(row.get("ID")),
        requirement_id=_optional_int(row.get("REQUERIMIENTO_ID")),
        number=int(row["NUMERO_VERSION"]),
        document_version=str(row["VERSION_DOCUMENTO"]),
        version_date=row["FECHA_VERSION"],
        title=str(row["TITULO"]),
        change_type_id=_optional_int(row.get("TIPO_CAMBIO_ID")),
        system=str(row["SISTEMA"]) if row.get("SISTEMA") is not None else None,
        current_need=(
            str(row["NECESIDAD_ACTUAL"]) if row.get("NECESIDAD_ACTUAL") is not None else None
        ),
        context_description=(
            str(row["CONTEXTO_DESCRIPCION"])
            if row.get("CONTEXTO_DESCRIPCION") is not None
            else None
        ),
        context_error_handling=(
            str(row["CONTEXTO_MANEJO_ERRORES"])
            if row.get("CONTEXTO_MANEJO_ERRORES") is not None
            else None
        ),
        users_permissions=(
            str(row["USUARIOS_PERMISOS"]) if row.get("USUARIOS_PERMISOS") is not None else None
        ),
        future_requirements_applies=_char_to_flag(row["REQUISITOS_FUTUROS_APLICA"]),
        future_requirements_text=(
            str(row["REQUISITOS_FUTUROS_TEXTO"])
            if row.get("REQUISITOS_FUTUROS_TEXTO") is not None
            else None
        ),
        dynamic_fields=dynamic_fields_from_json(row.get("CAMPOS_DINAMICOS")),
        frozen=_char_to_flag(row["CONGELADA"]),
        objectives=tuple(objectives),
        considerations=tuple(considerations),
        benefits=tuple(benefits),
        restrictions=tuple(restrictions),
        volumetry=tuple(volumetry),
        risks=tuple(risks),
        future_requirements_items=tuple(future_requirements_items),
        signatures=tuple(signatures),
        attachments=tuple(attachments),
    )


def requirement_to_row(requirement: Requirement) -> dict[str, Any]:
    row: dict[str, Any] = {
        "FOLIO": requirement.folio,
        "ESTADO": requirement.status.value,
        "VERSION_ACTUAL_ID": requirement.current_version_id,
    }
    if requirement.id is not None:
        row["ID"] = requirement.id
    return row


def requirement_from_row(
    row: Row, *, versions: Sequence[RequirementVersion] = ()
) -> Requirement:
    return Requirement(
        id=_optional_int(row.get("ID")),
        folio=int(row["FOLIO"]),
        status=RequirementStatus(str(row["ESTADO"])),
        current_version_id=_optional_int(row.get("VERSION_ACTUAL_ID")),
        versions=tuple(versions),
    )
