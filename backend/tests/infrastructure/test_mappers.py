from datetime import date

import pytest

from app.domain.requirement.attachment import Attachment
from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.items import (
    Benefit,
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
from app.infrastructure.db import mappers


def test_dynamic_fields_empty_serializes_to_none() -> None:
    assert mappers.dynamic_fields_to_json({}) is None


def test_dynamic_fields_round_trip() -> None:
    fields = {"prioridad": "alta", "esfuerzo": 5, "tags": ["a", "b"]}

    serialized = mappers.dynamic_fields_to_json(fields)

    assert serialized is not None
    assert mappers.dynamic_fields_from_json(serialized) == fields


def test_dynamic_fields_none_or_empty_deserializes_to_empty_mapping() -> None:
    assert mappers.dynamic_fields_from_json(None) == {}
    assert mappers.dynamic_fields_from_json("") == {}


def test_dynamic_fields_invalid_json_raises() -> None:
    with pytest.raises(ValueError):
        mappers.dynamic_fields_from_json("no-es-json")


def test_dynamic_fields_non_object_raises() -> None:
    with pytest.raises(ValueError):
        mappers.dynamic_fields_from_json("[1, 2, 3]")


@pytest.mark.parametrize(
    ("item_type", "to_row", "from_row"),
    [
        (Objective, mappers.objective_to_row, mappers.objective_from_row),
        (Consideration, mappers.consideration_to_row, mappers.consideration_from_row),
        (Restriction, mappers.restriction_to_row, mappers.restriction_from_row),
        (Volumetry, mappers.volumetry_to_row, mappers.volumetry_from_row),
        (Risk, mappers.risk_to_row, mappers.risk_from_row),
        (
            FutureRequirementItem,
            mappers.future_requirement_to_row,
            mappers.future_requirement_from_row,
        ),
    ],
)
def test_collection_item_round_trip(item_type, to_row, from_row) -> None:
    item = item_type(content="contenido", order=3, active=False, id=12)

    row = to_row(item, version_id=99)

    assert row["VERSION_ID"] == 99
    assert row["ORDEN"] == 3
    assert row["ACTIVO"] == "N"
    assert from_row(row) == item


def test_benefit_round_trip_preserves_kind() -> None:
    benefit = Benefit(content="beneficio", order=1, kind=BenefitKind.CUANTITATIVO, id=7)

    row = mappers.benefit_to_row(benefit, version_id=5)

    assert row["TIPO"] == "CUANTITATIVO"
    assert mappers.benefit_from_row(row) == benefit


def test_signature_round_trip() -> None:
    signature = Signature(
        role=SignatureRole.REVISO,
        name="Luis",
        position="Lider de proyecto",
        version_id=5,
        position_id=3,
        id=8,
    )

    row = mappers.signature_to_row(signature, version_id=5)

    assert row["ROL"] == "REVISO"
    assert row["CARGO_ID"] == 3
    assert mappers.signature_from_row(row) == signature


def test_attachment_round_trip() -> None:
    attachment = Attachment(
        name="anexo.pdf",
        order=2,
        storage_key="objects/2026/anexo.pdf",
        mime_type="application/pdf",
        caption="Anexo de soporte",
        active=False,
        version_id=5,
        id=9,
    )

    row = mappers.attachment_to_row(attachment, version_id=5)

    assert row["ORDEN"] == 2
    assert row["ACTIVO"] == "N"
    assert mappers.attachment_from_row(row) == attachment


def test_change_type_round_trip() -> None:
    change_type = ChangeType(code="CORRECCION", name="Correccion", active=True, id=4)

    row = mappers.change_type_to_row(change_type)

    assert row["CODIGO"] == "CORRECCION"
    assert mappers.change_type_from_row(row) == change_type


def test_position_round_trip() -> None:
    position = Position(
        role=SignatureRole.ELABORO,
        name="Analista funcional",
        is_default=True,
        active=False,
        id=5,
    )

    row = mappers.position_to_row(position)

    assert row["ROL"] == "ELABORO"
    assert row["PREDETERMINADO"] == "S"
    assert mappers.position_from_row(row) == position


def test_version_scalars_round_trip() -> None:
    version = RequirementVersion(
        number=2,
        document_version="2.1",
        version_date=date(2026, 10, 13),
        title="Titulo de la version",
        requirement_id=100,
        change_type_id=6,
        system="Sistema",
        current_need="Necesidad actual",
        context_description="Contexto",
        context_error_handling="Manejo de errores",
        users_permissions="Usuarios y permisos",
        future_requirements_applies=True,
        future_requirements_text="Requisitos futuros",
        dynamic_fields={"clave": "valor"},
        frozen=True,
    )

    row = mappers.version_to_row(version, requirement_id=100)

    assert row["CONGELADA"] == "S"
    assert row["REQUISITOS_FUTUROS_APLICA"] == "S"
    assert mappers.version_from_row(row) == version


def test_version_with_children_round_trip() -> None:
    version = RequirementVersion(
        number=1,
        document_version="1.0",
        version_date=date(2026, 10, 13),
        title="Titulo",
        requirement_id=1,
        objectives=(Objective(content="objetivo", order=1, id=1),),
        considerations=(Consideration(content="consideracion", order=1, id=2),),
        benefits=(Benefit(content="beneficio", order=1, kind=BenefitKind.CUALITATIVO, id=3),),
        restrictions=(Restriction(content="restriccion", order=1, id=4),),
        volumetry=(Volumetry(content="volumetria", order=1, id=5),),
        risks=(Risk(content="riesgo", order=1, id=6),),
        future_requirements_items=(FutureRequirementItem(content="futuro", order=1, id=7),),
        signatures=(
            Signature(
                role=SignatureRole.ELABORO,
                name="Ana",
                position="Analista",
                version_id=1,
                id=8,
            ),
        ),
        attachments=(Attachment(name="anexo", order=1, storage_key="key", version_id=1, id=9),),
    )

    row = mappers.version_to_row(version, requirement_id=1)
    restored = mappers.version_from_row(
        row,
        objectives=[
            mappers.objective_from_row(mappers.objective_to_row(item, version_id=1))
            for item in version.objectives
        ],
        considerations=[
            mappers.consideration_from_row(mappers.consideration_to_row(item, version_id=1))
            for item in version.considerations
        ],
        benefits=[
            mappers.benefit_from_row(mappers.benefit_to_row(item, version_id=1))
            for item in version.benefits
        ],
        restrictions=[
            mappers.restriction_from_row(mappers.restriction_to_row(item, version_id=1))
            for item in version.restrictions
        ],
        volumetry=[
            mappers.volumetry_from_row(mappers.volumetry_to_row(item, version_id=1))
            for item in version.volumetry
        ],
        risks=[
            mappers.risk_from_row(mappers.risk_to_row(item, version_id=1))
            for item in version.risks
        ],
        future_requirements_items=[
            mappers.future_requirement_from_row(
                mappers.future_requirement_to_row(item, version_id=1)
            )
            for item in version.future_requirements_items
        ],
        signatures=[
            mappers.signature_from_row(mappers.signature_to_row(item, version_id=1))
            for item in version.signatures
        ],
        attachments=[
            mappers.attachment_from_row(mappers.attachment_to_row(item, version_id=1))
            for item in version.attachments
        ],
    )

    assert restored == version


def test_requirement_round_trip() -> None:
    requirement = Requirement(
        folio=42,
        status=RequirementStatus.EN_REVISION,
        current_version_id=None,
        id=3,
    )

    row = mappers.requirement_to_row(requirement)

    assert row["FOLIO"] == 42
    assert row["ESTADO"] == "EN_REVISION"
    assert mappers.requirement_from_row(row) == requirement
