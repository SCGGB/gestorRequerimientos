from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

import pytest

from app.domain.requirement.enums import SignatureRole
from app.domain.requirement.preview import PreviewDocument, build_preview_document
from app.domain.requirement.signature import Signature
from app.infrastructure.adapters.document_converter import LibreofficeDocumentConverter
from app.infrastructure.adapters.document_renderer import DocxtplDocumentRenderer
from tests.factories import complete_version, requirement_with

pytestmark = pytest.mark.integration

BACKEND_DIR = Path(__file__).resolve().parents[2]
FIXTURES = BACKEND_DIR / "tests" / "fixtures"
KEY_TEXTS = (
    "necesidad clave",
    "contexto clave",
    "usuarios clave",
    "ana conversion",
)


def _libreoffice_binary() -> str:
    binary = os.environ.get("LIBREOFFICE_BINARY") or shutil.which("soffice")
    if binary is None:
        pytest.skip("LibreOffice no esta disponible en este entorno")
    return binary


def _preview_document() -> PreviewDocument:
    version = complete_version(
        document_version="1.0",
        version_date=date(2026, 5, 1),
        title="Requerimiento de conversion",
        current_need="Necesidad clave de conversion",
        context_description="Contexto clave de conversion",
        users_permissions="Usuarios clave de conversion",
    )
    version = version.with_signature(
        Signature(
            role=SignatureRole.ELABORO,
            name="Ana Conversion",
            position="Analista",
        )
    )
    return build_preview_document(requirement_with(version), version)


def _render_docx() -> bytes:
    renderer = DocxtplDocumentRenderer(str(FIXTURES))
    return renderer.render_docx(_preview_document(), "v1")


def _docx_text(data: bytes) -> str:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        return archive.read("word/document.xml").decode("utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def _pdf_text(pdf: bytes, tmp_path: Path) -> str:
    binary = shutil.which("pdftotext")
    if binary is None:
        pytest.skip("pdftotext no esta disponible para comparar el texto del PDF")
    source = tmp_path / "documento.pdf"
    source.write_bytes(pdf)
    target = tmp_path / "documento.txt"
    subprocess.run(
        [binary, "-enc", "UTF-8", str(source), str(target)],
        capture_output=True,
        check=True,
    )
    return target.read_text(encoding="utf-8", errors="replace")


def _converter() -> LibreofficeDocumentConverter:
    return LibreofficeDocumentConverter(
        binary=_libreoffice_binary(), timeout_seconds=120
    )


def test_converts_rendered_docx_to_valid_pdf() -> None:
    docx = _render_docx()

    pdf = _converter().to_pdf(docx)

    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf[-1024:]
    assert len(pdf) > 1024
    assert len(pdf) > len(docx) // 10


def test_pdf_preserves_key_texts_from_docx(tmp_path: Path) -> None:
    docx = _render_docx()
    docx_text = _normalize(_docx_text(docx))
    for key in KEY_TEXTS:
        assert key in docx_text

    pdf = _converter().to_pdf(docx)
    pdf_text = _normalize(_pdf_text(pdf, tmp_path))

    for key in KEY_TEXTS:
        assert key in pdf_text, key
