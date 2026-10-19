import io
import re
import zipfile
from datetime import date
from pathlib import Path

from app.domain.requirement.enums import SignatureRole
from app.domain.requirement.preview import PreviewDocument, build_preview_document
from app.domain.requirement.signature import Signature
from app.infrastructure.adapters.document_renderer import DocxtplDocumentRenderer
from tests.factories import complete_version, requirement_with

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _render(document: PreviewDocument) -> bytes:
    renderer = DocxtplDocumentRenderer(str(FIXTURES))
    return renderer.render_docx(document, "v1")


def _part(data: bytes, name: str) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return archive.read(name).decode("utf-8")


def _document() -> PreviewDocument:
    version = complete_version(
        document_version="2.1",
        version_date=date(2026, 3, 5),
        current_need="Primera linea\nSegunda linea",
        context_description="Descripcion contextual",
        context_error_handling="Manejo de errores",
        users_permissions="Usuarios del sistema",
        considerations=(),
        future_requirements_applies=False,
    )
    version = version.with_signature(
        Signature(role=SignatureRole.ELABORO, name="Ana Elaboro", position="Analista")
    )
    requirement = requirement_with(version)
    return build_preview_document(requirement, version)


def test_render_includes_header_ticket_and_document_version() -> None:
    data = _render(_document())

    for header in ("word/header1.xml", "word/header2.xml"):
        part = _part(data, header)
        assert "T#1" in part
        assert "2.1" in part


def test_render_includes_sections_and_paragraph_content() -> None:
    part = _part(_render(_document()), "word/document.xml")

    assert "Necesidad Actual" in part
    assert "Primera linea" in part
    assert "Segunda linea" in part
    assert "Descripcion contextual" in part
    assert "Manejo de errores" in part
    assert "Usuarios del sistema" in part


def test_render_preserves_line_breaks() -> None:
    part = _part(_render(_document()), "word/document.xml")

    assert re.search(r"<w:br\s*/>", part) is not None


def test_render_empty_collection_shows_no_aplica() -> None:
    part = _part(_render(_document()), "word/document.xml")

    assert "No aplica" in part


def test_render_future_requirements_not_applicable() -> None:
    part = _part(_render(_document()), "word/document.xml")

    assert "No Aplica." in part


def test_render_includes_version_control_and_signatures() -> None:
    part = _part(_render(_document()), "word/document.xml")

    assert "2.1" in part
    assert "05-03-2026" in part
    assert "Ana Elaboro" in part
    assert "Analista" in part


def test_render_escapes_user_content() -> None:
    version = complete_version(current_need="a < b & c")
    document = build_preview_document(requirement_with(version), version)

    part = _part(_render(document), "word/document.xml")

    assert "a &lt; b &amp; c" in part
    assert "a < b & c" not in part
