from __future__ import annotations

import itertools
from collections.abc import Iterator
from datetime import datetime

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine

from app.domain.requirement.document import DocumentFormat, GeneratedDocument
from app.domain.requirement.requirement import Requirement
from app.infrastructure.adapters.requirement_document_repository import (
    SqlAlchemyRequirementDocumentRepository,
)
from app.infrastructure.adapters.requirement_repository import (
    SqlAlchemyRequirementRepository,
)
from tests.factories import complete_version

pytestmark = pytest.mark.integration

EXPECTED_COLUMNS = {
    "ID",
    "REQUERIMIENTO_ID",
    "VERSION_ID",
    "FORMATO",
    "PLANTILLA_VERSION",
    "NOMBRE_ARCHIVO",
    "MIME_TYPE",
    "TAMANO_BYTES",
    "CONTENIDO",
    "GENERADO_AT",
    "GENERADO_BY",
    "CREATED_AT",
    "CREATED_BY",
    "UPDATED_AT",
    "UPDATED_BY",
}
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
BINARY_CONTENT = bytes(range(256)) * 4


def test_migration_creates_req_documento(migrated_engine: Engine) -> None:
    inspector = sa.inspect(migrated_engine)

    assert inspector.has_table("REQ_DOCUMENTO")
    columns = {column["name"].upper() for column in inspector.get_columns("REQ_DOCUMENTO")}
    assert columns >= EXPECTED_COLUMNS


@pytest.fixture(scope="module")
def folio_sequence() -> Iterator[int]:
    return itertools.count(910001)


@pytest.fixture()
def requirement_ids(
    migrated_engine: Engine, folio_sequence: Iterator[int]
) -> tuple[int, int]:
    repository = SqlAlchemyRequirementRepository(migrated_engine)
    requirement = Requirement(folio=next(folio_sequence), versions=(complete_version(),))
    saved = repository.save(requirement, actor="tester")
    assert saved.id is not None
    assert saved.current_version_id is not None
    return saved.id, saved.current_version_id


@pytest.fixture()
def repository(migrated_engine: Engine) -> SqlAlchemyRequirementDocumentRepository:
    return SqlAlchemyRequirementDocumentRepository(migrated_engine)


def _document(
    requirement_id: int,
    version_id: int,
    *,
    document_format: DocumentFormat = "DOCX",
    generated_at: datetime | None = None,
) -> GeneratedDocument:
    return GeneratedDocument(
        requirement_id=requirement_id,
        version_id=version_id,
        format=document_format,
        template_version="v1",
        file_name="T#1-v1.0.doc",
        mime_type=DOCX_MIME,
        size_bytes=len(BINARY_CONTENT),
        generated_at=generated_at or datetime(2026, 5, 1, 10, 30, 0),
        generated_by="SYSTEM",
        content=BINARY_CONTENT,
    )


def test_blob_round_trip(
    repository: SqlAlchemyRequirementDocumentRepository,
    requirement_ids: tuple[int, int],
) -> None:
    requirement_id, version_id = requirement_ids
    document_id = repository.add(_document(requirement_id, version_id), actor="tester")

    loaded = repository.get(document_id)

    assert loaded.id == document_id
    assert loaded.requirement_id == requirement_id
    assert loaded.version_id == version_id
    assert loaded.format == "DOCX"
    assert loaded.template_version == "v1"
    assert loaded.mime_type == DOCX_MIME
    assert loaded.size_bytes == len(BINARY_CONTENT)
    assert loaded.content == BINARY_CONTENT
    assert loaded.generated_at == datetime(2026, 5, 1, 10, 30, 0)


def test_list_by_requirement_returns_metadata_without_content(
    repository: SqlAlchemyRequirementDocumentRepository,
    requirement_ids: tuple[int, int],
) -> None:
    requirement_id, version_id = requirement_ids
    repository.add(
        _document(requirement_id, version_id, generated_at=datetime(2026, 5, 1, 8, 0)),
        actor="tester",
    )
    repository.add(
        _document(
            requirement_id,
            version_id,
            document_format="PDF",
            generated_at=datetime(2026, 5, 1, 9, 0),
        ),
        actor="tester",
    )

    documents = repository.list_by_requirement(requirement_id)

    assert [document.format for document in documents] == ["PDF", "DOCX"]
    assert all(document.content is None for document in documents)
    assert all(document.id is not None for document in documents)


def test_duplicate_regeneration_timestamp_is_rejected(
    repository: SqlAlchemyRequirementDocumentRepository,
    requirement_ids: tuple[int, int],
) -> None:
    requirement_id, version_id = requirement_ids
    repository.add(_document(requirement_id, version_id), actor="tester")

    with pytest.raises(sa.exc.IntegrityError):
        repository.add(_document(requirement_id, version_id), actor="tester")


def test_invalid_format_is_rejected(
    migrated_engine: Engine, requirement_ids: tuple[int, int]
) -> None:
    requirement_id, version_id = requirement_ids
    with pytest.raises(sa.exc.IntegrityError), migrated_engine.begin() as connection:
        connection.execute(
            sa.text(
                "INSERT INTO REQ_DOCUMENTO ("
                "REQUERIMIENTO_ID, VERSION_ID, FORMATO, PLANTILLA_VERSION, NOMBRE_ARCHIVO, "
                "MIME_TYPE, TAMANO_BYTES, CONTENIDO, GENERADO_AT, GENERADO_BY, "
                "CREATED_AT, CREATED_BY, UPDATED_AT, UPDATED_BY) "
                "VALUES (:requerimiento_id, :version_id, 'TXT', 'v1', 'archivo.txt', "
                "'text/plain', 1, :contenido, SYSTIMESTAMP, 'SYSTEM', "
                "SYSTIMESTAMP, 'SYSTEM', SYSTIMESTAMP, 'SYSTEM')"
            ),
            {
                "requerimiento_id": requirement_id,
                "version_id": version_id,
                "contenido": b"x",
            },
        )
