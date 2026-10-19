from datetime import datetime

from app.domain.requirement.document import GeneratedDocument
from app.infrastructure.db import mappers


def _row() -> dict[str, object]:
    return {
        "ID": 7,
        "REQUERIMIENTO_ID": 1,
        "VERSION_ID": 10,
        "FORMATO": "DOCX",
        "PLANTILLA_VERSION": "v1",
        "NOMBRE_ARCHIVO": "T#1-v1.0.docx",
        "MIME_TYPE": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "TAMANO_BYTES": 4096,
        "CONTENIDO": b"contenido-binario",
        "GENERADO_AT": datetime(2026, 10, 19, 12, 0, 0),
        "GENERADO_BY": "SYSTEM",
    }


def test_generated_document_from_row_maps_metadata_and_content() -> None:
    document = mappers.generated_document_from_row(_row(), with_content=True)

    assert document.id == 7
    assert document.requirement_id == 1
    assert document.version_id == 10
    assert document.format == "DOCX"
    assert document.template_version == "v1"
    assert document.file_name == "T#1-v1.0.docx"
    assert document.size_bytes == 4096
    assert document.content == b"contenido-binario"


def test_generated_document_from_row_without_content_is_none() -> None:
    row = _row()
    row.pop("CONTENIDO")

    document = mappers.generated_document_from_row(row, with_content=False)

    assert document.content is None


def test_generated_document_from_row_reads_lob_like_object() -> None:
    class _Lob:
        def read(self) -> bytes:
            return b"lob-bytes"

    row = _row()
    row["CONTENIDO"] = _Lob()

    document = mappers.generated_document_from_row(row, with_content=True)

    assert document.content == b"lob-bytes"


def test_generated_document_to_row_round_trip_metadata() -> None:
    document = GeneratedDocument(
        requirement_id=1,
        version_id=10,
        format="PDF",
        template_version="v1",
        file_name="T#1-v1.0.pdf",
        mime_type="application/pdf",
        size_bytes=2048,
        generated_at=datetime(2026, 10, 19, 12, 0, 0),
        generated_by="SYSTEM",
        content=b"pdf",
    )

    row = mappers.generated_document_to_row(document)

    assert row["FORMATO"] == "PDF"
    assert row["CONTENIDO"] == b"pdf"
    assert row["NOMBRE_ARCHIVO"] == "T#1-v1.0.pdf"
