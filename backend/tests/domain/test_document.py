from datetime import datetime

import pytest

from app.domain.requirement.document import (
    MIME_TYPES,
    GeneratedDocument,
    build_file_name,
)


@pytest.mark.parametrize(
    ("folio", "document_version", "expected"),
    [
        (1, "1.0", "T#1-v1.0.docx"),
        (42, "2.1", "T#42-v2.1.docx"),
        (1000, "10", "T#1000-v10.docx"),
    ],
)
def test_build_file_name_docx(folio: int, document_version: str, expected: str) -> None:
    assert build_file_name(folio, document_version, "DOCX") == expected


@pytest.mark.parametrize(
    ("folio", "document_version", "expected"),
    [
        (1, "1.0", "T#1-v1.0.pdf"),
        (7, "3.2", "T#7-v3.2.pdf"),
        (999, "12", "T#999-v12.pdf"),
    ],
)
def test_build_file_name_pdf(folio: int, document_version: str, expected: str) -> None:
    assert build_file_name(folio, document_version, "PDF") == expected


def test_mime_types_cover_formats() -> None:
    assert MIME_TYPES["DOCX"].endswith("wordprocessingml.document")
    assert MIME_TYPES["PDF"] == "application/pdf"


def test_generated_document_content_is_optional() -> None:
    document = GeneratedDocument(
        requirement_id=1,
        version_id=10,
        format="PDF",
        template_version="v1",
        file_name="T#1-v1.0.pdf",
        mime_type=MIME_TYPES["PDF"],
        size_bytes=2048,
        generated_at=datetime(2026, 10, 19, 12, 0, 0),
        generated_by="SYSTEM",
    )

    assert document.id is None
    assert document.content is None
