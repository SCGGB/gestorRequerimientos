from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.domain.requirement.enums import BenefitKind, SignatureRole
from app.domain.requirement.items import CollectionItem
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion

PreviewBlockType = Literal["parrafo", "lista", "no_aplica"]

NOT_APPLICABLE_TEXT = "No aplica"
FUTURE_REQUIREMENTS_NOT_APPLICABLE_TEXT = "No Aplica."


@dataclass(frozen=True, slots=True)
class PreviewSigner:
    """Firma de la version consultada para la vista previa."""

    name: str
    position: str | None = None


@dataclass(frozen=True, slots=True)
class PreviewFirmas:
    """Bloque de firmas de la version consultada; None cuando no existen (ADR-007)."""

    prepared_by: PreviewSigner | None = None
    reviewed_by: PreviewSigner | None = None
    authorized_by: PreviewSigner | None = None


@dataclass(frozen=True, slots=True)
class PreviewBlock:
    """Bloque de contenido ya normalizado; el renderizador no aplica reglas."""

    type: PreviewBlockType
    text: str | None = None
    items: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PreviewSection:
    """Seccion del machote con su numeroacion y bloques."""

    code: str
    number: str
    title: str
    blocks: tuple[PreviewBlock, ...] = ()


@dataclass(frozen=True, slots=True)
class PreviewVersionRow:
    """Fila de la tabla de control de versiones."""

    document_version: str
    date: str
    change_description: str | None = None
    reviewed_by: str | None = None
    prepared_by: str | None = None


@dataclass(frozen=True, slots=True)
class PreviewDocument:
    """DTO neutral de renderizado compuesto desde una version persistida."""

    folio: int
    ticket: str
    title: str
    document_version: str
    version_date: str
    sections: tuple[PreviewSection, ...] = ()
    version_control: tuple[PreviewVersionRow, ...] = ()
    signatures: PreviewFirmas = PreviewFirmas()


def format_date(value: date) -> str:
    """Formatea una fecha como dd-mm-aaaa (regla unica de la vista previa)."""
    return value.strftime("%d-%m-%Y")


def build_preview_document(
    requirement: Requirement, version: RequirementVersion
) -> PreviewDocument:
    """Compone el DTO neutral de renderizado desde la version persistida."""
    versions = tuple(sorted(requirement.versions, key=lambda item: item.number))
    return PreviewDocument(
        folio=requirement.folio,
        ticket=requirement.ticket,
        title=version.title,
        document_version=version.document_version,
        version_date=format_date(version.version_date),
        sections=_build_sections(version),
        version_control=tuple(_version_row(item) for item in versions),
        signatures=_signatures(version),
    )


def _version_row(version: RequirementVersion) -> PreviewVersionRow:
    return PreviewVersionRow(
        document_version=version.document_version,
        date=format_date(version.version_date),
        reviewed_by=_signature_name(version, SignatureRole.REVISO),
        prepared_by=_signature_name(version, SignatureRole.ELABORO),
    )


def _signature_name(
    version: RequirementVersion, role: SignatureRole
) -> str | None:
    signatures = version.signatures_by_role(role)
    if not signatures:
        return None
    return signatures[-1].name


def _signer(version: RequirementVersion, role: SignatureRole) -> PreviewSigner | None:
    signatures = version.signatures_by_role(role)
    if not signatures:
        return None
    signature = signatures[-1]
    return PreviewSigner(name=signature.name, position=signature.position)


def _signatures(version: RequirementVersion) -> PreviewFirmas:
    return PreviewFirmas(
        prepared_by=_signer(version, SignatureRole.ELABORO),
        reviewed_by=_signer(version, SignatureRole.REVISO),
        authorized_by=_signer(version, SignatureRole.AUTORIZO),
    )


def _build_sections(version: RequirementVersion) -> tuple[PreviewSection, ...]:
    return (
        PreviewSection(
            code="necesidad_actual",
            number="1",
            title="Necesidad Actual",
            blocks=(_paragraph(version.current_need),),
        ),
        PreviewSection(
            code="objetivos",
            number="2",
            title="Objetivos Generales",
            blocks=_collection_blocks(version.active_objectives()),
        ),
        PreviewSection(
            code="consideraciones",
            number="3",
            title="Consideraciones",
            blocks=_collection_blocks(version.active_considerations()),
        ),
        PreviewSection(
            code="beneficios",
            number="4",
            title="Beneficios Esperados",
        ),
        PreviewSection(
            code="beneficios_cualitativos",
            number="4.1",
            title="Beneficios Cualitativos",
            blocks=_benefit_blocks(version, BenefitKind.CUALITATIVO),
        ),
        PreviewSection(
            code="beneficios_cuantitativos",
            number="4.2",
            title="Beneficios Cuantitativos",
            blocks=_benefit_blocks(version, BenefitKind.CUANTITATIVO),
        ),
        PreviewSection(
            code="diagramas_contextuales",
            number="5",
            title="Diagramas Contextuales",
            blocks=_context_blocks(version),
        ),
        PreviewSection(
            code="usuarios_permisos",
            number="6",
            title="Usuarios y Permisos",
            blocks=(_paragraph(version.users_permissions),),
        ),
        PreviewSection(
            code="restricciones",
            number="7",
            title="Restricciones",
            blocks=_collection_blocks(version.active_restrictions()),
        ),
        PreviewSection(
            code="requisitos_futuros",
            number="8",
            title="Requisitos futuros",
            blocks=_future_requirement_blocks(version),
        ),
        PreviewSection(
            code="volumetria",
            number="9",
            title="Volumetria y Rendimiento",
            blocks=_collection_blocks(version.active_volumetry()),
        ),
        PreviewSection(
            code="riesgos",
            number="10",
            title="Riesgos Iniciales",
            blocks=_collection_blocks(version.active_risks()),
        ),
    )


def _paragraph(value: str | None) -> PreviewBlock:
    return PreviewBlock(type="parrafo", text=value or "")


def _context_blocks(version: RequirementVersion) -> tuple[PreviewBlock, ...]:
    blocks = [_paragraph(version.context_description)]
    if version.context_error_handling and version.context_error_handling.strip():
        blocks.append(_paragraph(version.context_error_handling))
    return tuple(blocks)


def _benefit_blocks(
    version: RequirementVersion, kind: BenefitKind
) -> tuple[PreviewBlock, ...]:
    return _collection_blocks(
        tuple(benefit for benefit in version.active_benefits() if benefit.kind == kind)
    )


def _collection_blocks(items: tuple[CollectionItem, ...]) -> tuple[PreviewBlock, ...]:
    contents = _contents(items)
    if not contents:
        return (PreviewBlock(type="no_aplica", text=NOT_APPLICABLE_TEXT),)
    return (PreviewBlock(type="lista", items=contents),)


def _contents(items: tuple[CollectionItem, ...]) -> tuple[str, ...]:
    ordered = sorted(items, key=lambda item: item.order)
    return tuple(item.content for item in ordered if item.content.strip())


def _future_requirement_blocks(
    version: RequirementVersion,
) -> tuple[PreviewBlock, ...]:
    if not version.future_requirements_applies:
        return (
            PreviewBlock(
                type="no_aplica", text=FUTURE_REQUIREMENTS_NOT_APPLICABLE_TEXT
            ),
        )
    blocks: list[PreviewBlock] = []
    if version.future_requirements_text and version.future_requirements_text.strip():
        blocks.append(_paragraph(version.future_requirements_text))
    contents = _contents(version.active_future_requirements())
    if contents:
        blocks.append(PreviewBlock(type="lista", items=contents))
    return tuple(blocks)
