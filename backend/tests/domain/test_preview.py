from datetime import date

from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.items import (
    Benefit,
    FutureRequirementItem,
    Objective,
)
from app.domain.requirement.preview import (
    PreviewDocument,
    PreviewSection,
    build_preview_document,
)
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from tests.factories import complete_version, requirement_with


def _section(document: PreviewDocument, code: str) -> PreviewSection:
    return next(item for item in document.sections if item.code == code)


def test_header_uses_ticket_title_document_version_and_formatted_date() -> None:
    version = complete_version(
        title="Gestion de contratos",
        document_version="2.1",
        version_date=date(2026, 3, 5),
    )
    requirement = requirement_with(version)

    document = build_preview_document(requirement, version)

    assert document.folio == 1
    assert document.ticket == "T#1"
    assert document.title == "Gestion de contratos"
    assert document.document_version == "2.1"
    assert document.version_date == "05-03-2026"


def test_sections_follow_machote_numbering_and_codes() -> None:
    document = build_preview_document(
        requirement_with(), complete_version()
    )

    numbers = [section.number for section in document.sections]
    codes = [section.code for section in document.sections]
    assert numbers == ["1", "2", "3", "4", "4.1", "4.2", "5", "6", "7", "8", "9", "10"]
    assert codes == [
        "necesidad_actual",
        "objetivos",
        "consideraciones",
        "beneficios",
        "beneficios_cualitativos",
        "beneficios_cuantitativos",
        "diagramas_contextuales",
        "usuarios_permisos",
        "restricciones",
        "requisitos_futuros",
        "volumetria",
        "riesgos",
    ]


def test_beneficios_container_has_title_and_no_blocks() -> None:
    section = _section(
        build_preview_document(requirement_with(), complete_version()), "beneficios"
    )
    assert section.number == "4"
    assert section.title == "Beneficios Esperados"
    assert section.blocks == ()


def test_only_active_items_in_order_and_empty_content_omitted() -> None:
    version = complete_version(
        objectives=(
            Objective(content="Tercero", order=3),
            Objective(content="Inactivo", order=2, active=False),
            Objective(content="   ", order=4),
            Objective(content="Primero", order=1),
        ),
    )
    document = build_preview_document(requirement_with(version), version)

    block = _section(document, "objetivos").blocks[0]
    assert block.type == "lista"
    assert block.items == ("Primero", "Tercero")


def test_empty_collection_keeps_title_and_returns_not_applicable() -> None:
    version = complete_version(objectives=())
    document = build_preview_document(requirement_with(version), version)

    section = _section(document, "objetivos")
    assert section.title == "Objetivos Generales"
    assert len(section.blocks) == 1
    assert section.blocks[0].type == "no_aplica"
    assert section.blocks[0].text == "No aplica"


def test_benefits_are_split_by_kind_with_independent_subsections() -> None:
    version = complete_version(
        benefits=(
            Benefit(content="Cualitativo", order=1, kind=BenefitKind.CUALITATIVO),
            Benefit(content="Cuantitativo", order=1, kind=BenefitKind.CUANTITATIVO),
            Benefit(
                content="Otro cualitativo",
                order=2,
                kind=BenefitKind.CUALITATIVO,
            ),
        ),
    )
    document = build_preview_document(requirement_with(version), version)

    cualitativos = _section(document, "beneficios_cualitativos").blocks[0]
    cuantitativos = _section(document, "beneficios_cuantitativos").blocks[0]
    assert cualitativos.items == ("Cualitativo", "Otro cualitativo")
    assert cuantitativos.items == ("Cuantitativo",)


def test_future_requirements_not_applying_returns_not_applicable() -> None:
    version = complete_version(
        future_requirements_applies=False,
        future_requirements_text="Texto ignorado",
        future_requirements_items=(FutureRequirementItem(content="Item", order=1),),
    )
    document = build_preview_document(requirement_with(version), version)

    blocks = _section(document, "requisitos_futuros").blocks
    assert len(blocks) == 1
    assert blocks[0].type == "no_aplica"
    assert blocks[0].text == "No Aplica."


def test_future_requirements_applying_returns_text_and_items() -> None:
    version = complete_version(
        future_requirements_applies=True,
        future_requirements_text="Texto futuro",
        future_requirements_items=(
            FutureRequirementItem(content="Segundo", order=2),
            FutureRequirementItem(content="Primero", order=1),
        ),
    )
    document = build_preview_document(requirement_with(version), version)

    blocks = _section(document, "requisitos_futuros").blocks
    assert [block.type for block in blocks] == ["parrafo", "lista"]
    assert blocks[0].text == "Texto futuro"
    assert blocks[1].items == ("Primero", "Segundo")


def test_future_requirements_applying_with_items_only_returns_list() -> None:
    version = complete_version(
        future_requirements_applies=True,
        future_requirements_text=None,
        future_requirements_items=(FutureRequirementItem(content="Item", order=1),),
    )
    document = build_preview_document(requirement_with(version), version)

    blocks = _section(document, "requisitos_futuros").blocks
    assert [block.type for block in blocks] == ["lista"]
    assert blocks[0].items == ("Item",)


def test_narrative_sections_are_paragraphs_and_context_is_optional() -> None:
    version = complete_version(
        current_need="Necesidad",
        context_description="Descripcion",
        context_error_handling=None,
        users_permissions="Usuarios",
    )
    document = build_preview_document(requirement_with(version), version)

    assert _section(document, "necesidad_actual").blocks[0].type == "parrafo"
    assert _section(document, "necesidad_actual").blocks[0].text == "Necesidad"
    context_blocks = _section(document, "diagramas_contextuales").blocks
    assert len(context_blocks) == 1
    assert context_blocks[0].text == "Descripcion"

    with_error_handling = complete_version(context_error_handling="Manejo de errores")
    document = build_preview_document(
        requirement_with(with_error_handling), with_error_handling
    )
    context_blocks = _section(document, "diagramas_contextuales").blocks
    assert [block.text for block in context_blocks] == [
        "Contexto",
        "Manejo de errores",
    ]


def test_version_control_lists_all_versions_ordered_with_null_description() -> None:
    first = complete_version(number=1, document_version="1.0", frozen=True)
    second = complete_version(
        number=2,
        document_version="2.0",
        version_date=date(2026, 2, 10),
        frozen=False,
    )
    requirement = Requirement(
        folio=7,
        status=RequirementStatus.BORRADOR,
        versions=(second, first),
    )

    document = build_preview_document(requirement, second)

    assert [row.document_version for row in document.version_control] == ["1.0", "2.0"]
    assert [row.date for row in document.version_control] == ["01-01-2026", "10-02-2026"]
    assert all(row.change_description is None for row in document.version_control)


def test_version_control_uses_signature_names_when_registered() -> None:
    version = complete_version(
        signatures=(
            Signature(
                role=SignatureRole.ELABORO,
                name="Ana Perez",
                position="Analista",
            ),
            Signature(role=SignatureRole.REVISO, name="Luis Soto", position="Jefe"),
        ),
    )
    document = build_preview_document(requirement_with(version), version)

    row = document.version_control[0]
    assert row.prepared_by == "Ana Perez"
    assert row.reviewed_by == "Luis Soto"
    assert row.change_description is None


def test_signatures_are_null_per_role_when_missing() -> None:
    document = build_preview_document(requirement_with(), complete_version())

    assert document.signatures.prepared_by is None
    assert document.signatures.reviewed_by is None
    assert document.signatures.authorized_by is None


def test_signatures_include_name_and_position_when_registered() -> None:
    version = complete_version(
        signatures=(
            Signature(
                role=SignatureRole.ELABORO,
                name="Ana Perez",
                position="Analista",
            ),
            Signature(
                role=SignatureRole.AUTORIZO,
                name="Maria Ruiz",
                position="Directora",
            ),
        ),
    )
    document = build_preview_document(requirement_with(version), version)

    assert document.signatures.prepared_by is not None
    assert document.signatures.prepared_by.name == "Ana Perez"
    assert document.signatures.prepared_by.position == "Analista"
    assert document.signatures.authorized_by is not None
    assert document.signatures.authorized_by.name == "Maria Ruiz"
    assert document.signatures.reviewed_by is None
