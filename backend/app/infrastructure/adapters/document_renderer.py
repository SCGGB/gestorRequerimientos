from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate, Listing

from app.application.errors import DocumentGenerationError
from app.application.ports.document_renderer import DocumentRendererPort
from app.domain.requirement.preview import (
    FUTURE_REQUIREMENTS_NOT_APPLICABLE_TEXT,
    NOT_APPLICABLE_TEXT,
    PreviewDocument,
    PreviewFirmas,
    PreviewSection,
    PreviewSigner,
    PreviewVersionRow,
)

_TEMPLATE_FILE = "ers_plantilla_{version}.docx"

_PARAGRAPH_CODES = ("necesidad_actual", "usuarios_permisos")
_COLLECTION_CODES = (
    "objetivos",
    "consideraciones",
    "beneficios_cualitativos",
    "beneficios_cuantitativos",
    "restricciones",
    "volumetria",
    "riesgos",
    "requisitos_futuros",
)


class DocxtplDocumentRenderer(DocumentRendererPort):
    def __init__(self, templates_dir: str) -> None:
        self._templates_dir = Path(templates_dir)

    def render_docx(self, document: PreviewDocument, template_version: str) -> bytes:
        template_path = self._templates_dir / _TEMPLATE_FILE.format(version=template_version)
        try:
            template = DocxTemplate(str(template_path))
            template.render(build_template_context(document), autoescape=True)
            buffer = io.BytesIO()
            template.save(buffer)
            return buffer.getvalue()
        except DocumentGenerationError:
            raise
        except Exception as exc:
            raise DocumentGenerationError(
                "No fue posible generar el documento DOCX."
            ) from exc


def build_template_context(document: PreviewDocument) -> dict[str, Any]:
    """Mapea el `PreviewDocument` al contexto de variables de la plantilla."""
    sections = {section.code: section for section in document.sections}
    context: dict[str, Any] = {
        "ticket": document.ticket,
        "document_version": document.document_version,
        "no_aplica": NOT_APPLICABLE_TEXT,
        "requisitos_futuros_no_aplica": FUTURE_REQUIREMENTS_NOT_APPLICABLE_TEXT,
        "contexto": _context_blocks(sections.get("diagramas_contextuales")),
        "versiones": [_version_row(row) for row in document.version_control],
        "firmas": _signatures(document.signatures),
    }
    for code in _PARAGRAPH_CODES:
        context[code] = _paragraph_text(sections.get(code))
    for code in _COLLECTION_CODES:
        context[code] = _list_items(sections.get(code))
    return context


def _paragraph_text(section: PreviewSection | None) -> Listing:
    if section is None:
        return Listing("")
    for block in section.blocks:
        if block.type == "parrafo":
            return Listing(block.text or "")
    return Listing("")


def _list_items(section: PreviewSection | None) -> list[Listing]:
    if section is None:
        return []
    for block in section.blocks:
        if block.type == "lista":
            return [Listing(item) for item in block.items]
    return []


def _context_blocks(section: PreviewSection | None) -> dict[str, Any]:
    paragraphs: list[str] = []
    if section is not None:
        paragraphs = [block.text or "" for block in section.blocks if block.type == "parrafo"]
    description = paragraphs[0] if paragraphs else ""
    error_handling = paragraphs[1] if len(paragraphs) > 1 else ""
    return {
        "descripcion": Listing(description),
        "manejo_errores": bool(error_handling.strip()),
        "manejo_errores_texto": Listing(error_handling),
    }


def _version_row(row: PreviewVersionRow) -> dict[str, str]:
    return {
        "version": row.document_version,
        "fecha": row.date,
        "descripcion_cambio": row.change_description or "",
        "reviso": row.reviewed_by or "",
        "elaboro": row.prepared_by or "",
    }


def _signatures(signatures: PreviewFirmas) -> dict[str, dict[str, str]]:
    return {
        "elaboro": _signer(signatures.prepared_by),
        "reviso": _signer(signatures.reviewed_by),
        "autorizo": _signer(signatures.authorized_by),
    }


def _signer(signer: PreviewSigner | None) -> dict[str, str]:
    if signer is None:
        return {"nombre": "", "cargo": ""}
    return {"nombre": signer.name, "cargo": signer.position or ""}
