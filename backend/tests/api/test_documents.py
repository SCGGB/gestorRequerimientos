from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_audit_recorder,
    get_document_converter,
    get_document_renderer,
    get_requirement_document_repository,
    get_requirement_repository,
)
from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion
from tests.api.helpers import build_app
from tests.application.fakes import (
    FakeAuditRecorder,
    FakeDocumentConverter,
    FakeDocumentRenderer,
    InMemoryRequirementDocumentRepository,
    InMemoryRequirementRepository,
)
from tests.factories import complete_version

_DOCUMENT_KEYS = {
    "id",
    "formato",
    "version_id",
    "plantilla_version",
    "nombre_archivo",
    "mime_type",
    "tamano_bytes",
    "generado_at",
    "generado_by",
}


def _signed_version() -> RequirementVersion:
    version = complete_version()
    version = version.with_signature(
        Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista")
    )
    return version.with_signature(
        Signature(role=SignatureRole.AUTORIZO, name="Luis", position="Gerente")
    )


def _seed(
    repository: InMemoryRequirementRepository,
    *,
    folio: int = 1,
    status: RequirementStatus = RequirementStatus.APROBADO,
    signed: bool = True,
) -> int:
    version = _signed_version() if signed else complete_version()
    requirement = repository.save(
        Requirement(folio=folio, status=status, versions=(version,)), actor="tester"
    )
    assert requirement.id is not None
    return requirement.id


def _client(
    repository: InMemoryRequirementRepository,
    document_repository: InMemoryRequirementDocumentRepository,
    *,
    renderer: FakeDocumentRenderer | None = None,
    converter: FakeDocumentConverter | None = None,
) -> TestClient:
    app = build_app()
    app.dependency_overrides[get_requirement_repository] = lambda: repository
    app.dependency_overrides[get_requirement_document_repository] = (
        lambda: document_repository
    )
    app.dependency_overrides[get_audit_recorder] = lambda: FakeAuditRecorder()
    app.dependency_overrides[get_document_renderer] = (
        lambda: renderer or FakeDocumentRenderer()
    )
    app.dependency_overrides[get_document_converter] = (
        lambda: converter or FakeDocumentConverter()
    )
    return TestClient(app)


def test_generate_documents_returns_two_documents_and_transitions() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement_id = _seed(repository, folio=5)
    client = _client(repository, document_repository)

    response = client.post(f"/api/v1/requerimientos/{requirement_id}/documentos")

    assert response.status_code == 201
    body = response.json()
    assert len(body) == 2
    assert {document["formato"] for document in body} == {"DOCX", "PDF"}
    assert {document["nombre_archivo"] for document in body} == {
        "T#5-v1.0.docx",
        "T#5-v1.0.pdf",
    }
    assert all(document["plantilla_version"] == "v1" for document in body)
    assert all(document["generado_by"] == "tester" for document in body)
    assert all(document["version_id"] > 0 for document in body)
    assert all(set(document) == _DOCUMENT_KEYS for document in body)
    assert client.get(f"/api/v1/requerimientos/{requirement_id}").json()["estado"] == (
        "GENERADO"
    )


def test_generate_documents_rejected_when_state_not_allowed() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement_id = _seed(repository, status=RequirementStatus.BORRADOR)
    client = _client(repository, document_repository)

    response = client.post(f"/api/v1/requerimientos/{requirement_id}/documentos")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "invalid_state_transition"
    assert error["message"]
    assert client.get(f"/api/v1/requerimientos/{requirement_id}/documentos").json() == []
    assert (
        client.get(f"/api/v1/requerimientos/{requirement_id}").json()["estado"]
        == "BORRADOR"
    )


def test_generate_documents_rejected_without_required_signatures() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement_id = _seed(repository, signed=False)
    client = _client(repository, document_repository)

    response = client.post(f"/api/v1/requerimientos/{requirement_id}/documentos")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "document_generation_not_allowed"
    assert error["message"]
    assert client.get(f"/api/v1/requerimientos/{requirement_id}/documentos").json() == []


def test_generate_documents_invalid_payload_returns_422() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement_id = _seed(repository)
    client = _client(repository, document_repository)

    response = client.post(
        f"/api/v1/requerimientos/{requirement_id}/documentos",
        json={"version_id": "no-numerica"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_list_documents_returns_full_history_without_binary() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement_id = _seed(repository, folio=7)
    client = _client(repository, document_repository)
    client.post(f"/api/v1/requerimientos/{requirement_id}/documentos")
    client.post(f"/api/v1/requerimientos/{requirement_id}/documentos")

    response = client.get(f"/api/v1/requerimientos/{requirement_id}/documentos")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 4
    assert [document["formato"] for document in body].count("DOCX") == 2
    assert [document["formato"] for document in body].count("PDF") == 2
    assert len({document["id"] for document in body}) == 4
    generated_at = [document["generado_at"] for document in body]
    assert generated_at == sorted(generated_at, reverse=True)
    assert all(set(document) == _DOCUMENT_KEYS for document in body)


def test_download_document_returns_attachment_with_conventional_name() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    requirement_id = _seed(repository, folio=1234)
    client = _client(repository, document_repository)
    generated = client.post(
        f"/api/v1/requerimientos/{requirement_id}/documentos"
    ).json()
    docx = next(document for document in generated if document["formato"] == "DOCX")

    response = client.get(
        f"/api/v1/requerimientos/{requirement_id}/documentos/{docx['id']}/descarga"
    )

    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="T#1234-v1.0.docx"'
    )
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert response.content == b"docx-bytes"


def test_download_document_from_another_requirement_returns_404() -> None:
    repository = InMemoryRequirementRepository()
    document_repository = InMemoryRequirementDocumentRepository()
    owner_id = _seed(repository, folio=1)
    other_id = _seed(repository, folio=2)
    client = _client(repository, document_repository)
    generated = client.post(f"/api/v1/requerimientos/{owner_id}/documentos").json()

    response = client.get(
        f"/api/v1/requerimientos/{other_id}/documentos/{generated[0]['id']}/descarga"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "document_not_found"
