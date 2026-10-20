from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from itertools import count
from typing import Any, TypeVar

from app.application.errors import (
    DocumentNotFoundError,
    DuplicateFolioError,
    RequirementNotFoundError,
)
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.catalog_repository import ChangeTypeCatalog, PositionCatalog
from app.application.ports.document_converter import DocumentConverterPort
from app.application.ports.document_renderer import DocumentRendererPort
from app.application.ports.requirement_document_repository import (
    RequirementDocumentRepository,
)
from app.application.ports.requirement_repository import (
    RequirementRepository,
    RequirementSearchFilters,
)
from app.domain.auth.audit import AuditEntry
from app.domain.requirement.catalog import ChangeType, Position
from app.domain.requirement.document import GeneratedDocument
from app.domain.requirement.enums import SignatureRole
from app.domain.requirement.preview import PreviewDocument
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion

ItemT = TypeVar("ItemT")


class FakeAuditRecorder(AuditRecorderPort):
    """Registra las entradas de auditoria en memoria para las pruebas."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def record(self, entry: AuditEntry) -> None:
        self.entries.append(entry)

    def actions(self) -> tuple[str, ...]:
        return tuple(entry.action.value for entry in self.entries)

    def find(self, action: str) -> AuditEntry | None:
        for entry in self.entries:
            if entry.action.value == action:
                return entry
        return None


class InMemoryRequirementRepository(RequirementRepository):
    """Repositorio en memoria con ids estables (sin base de datos)."""

    def __init__(self) -> None:
        self._requirements: dict[int, Requirement] = {}
        self._ids = count(1)
        self.last_actor: str | None = None

    def save(self, requirement: Requirement, *, actor: str) -> Requirement:
        self.last_actor = actor
        # Check for duplicate folio before assigning/overwriting
        target_folio = requirement.folio
        for existing in self._requirements.values():
            if existing.folio == target_folio and (
                requirement.id is None or existing.id != requirement.id
            ):
                raise DuplicateFolioError()
        assigned = self._assign_requirement(requirement)
        if assigned.id is None:
            raise RuntimeError("El requerimiento debe tener id tras guardar.")
        self._requirements[assigned.id] = assigned
        return assigned

    def get(self, requirement_id: int) -> Requirement:
        try:
            return self._requirements[requirement_id]
        except KeyError:
            raise RequirementNotFoundError() from None

    def get_by_folio(self, folio: int) -> Requirement | None:
        for requirement in self._requirements.values():
            if requirement.folio == folio:
                return requirement
        return None

    def list(self) -> Sequence[Requirement]:
        return tuple(
            self._requirements[requirement_id]
            for requirement_id in sorted(self._requirements)
        )

    def search(
        self,
        filters: RequirementSearchFilters,
        *,
        offset: int,
        limit: int,
    ) -> tuple[Sequence[Requirement], int]:
        items = [
            requirement
            for requirement in self.list()
            if (filters.status is None or requirement.status is filters.status)
            and (filters.folio is None or requirement.folio == filters.folio)
        ]
        return tuple(items[offset : offset + limit]), len(items)

    def _assign_requirement(self, requirement: Requirement) -> Requirement:
        requirement_id = requirement.id
        if requirement_id is None:
            requirement_id = next(self._ids)
        versions = tuple(
            self._assign_version(version, requirement_id)
            for version in requirement.versions
        )
        return replace(requirement, id=requirement_id, versions=versions)

    def _assign_version(
        self, version: RequirementVersion, requirement_id: int
    ) -> RequirementVersion:
        version_id = version.id
        if version_id is None:
            version_id = next(self._ids)
        return replace(
            version,
            id=version_id,
            requirement_id=requirement_id,
            objectives=self._assign_ids(version.objectives),
            considerations=self._assign_ids(version.considerations),
            benefits=self._assign_ids(version.benefits),
            restrictions=self._assign_ids(version.restrictions),
            volumetry=self._assign_ids(version.volumetry),
            risks=self._assign_ids(version.risks),
            future_requirements_items=self._assign_ids(
                version.future_requirements_items
            ),
            signatures=self._assign_ids(version.signatures),
            attachments=self._assign_ids(version.attachments),
        )

    def _assign_ids(self, items: Sequence[ItemT]) -> tuple[Any, ...]:
        return tuple(
            replace(item, id=next(self._ids))  # type: ignore[call-overload]
            if getattr(item, "id", None) is None
            else item
            for item in items
        )


class InMemoryRequirementDocumentRepository(RequirementDocumentRepository):
    """Repositorio de documentos en memoria con ids estables."""

    def __init__(self) -> None:
        self._documents: dict[int, GeneratedDocument] = {}
        self._ids = count(1)

    def add(self, document: GeneratedDocument, *, actor: str) -> int:
        document_id = next(self._ids)
        self._documents[document_id] = replace(document, id=document_id, generated_by=actor)
        return document_id

    def get(self, document_id: int) -> GeneratedDocument:
        try:
            return self._documents[document_id]
        except KeyError:
            raise DocumentNotFoundError() from None

    def list_by_requirement(self, requirement_id: int) -> Sequence[GeneratedDocument]:
        items = [
            document
            for document in self._documents.values()
            if document.requirement_id == requirement_id
        ]
        items.sort(key=lambda document: (document.generated_at, document.id or 0), reverse=True)
        return tuple(replace(document, content=None) for document in items)


class FakeDocumentRenderer(DocumentRendererPort):
    def __init__(self, content: bytes = b"docx-bytes") -> None:
        self._content = content
        self.calls = 0

    def render_docx(self, document: PreviewDocument, template_version: str) -> bytes:
        self.calls += 1
        return self._content


class FakeDocumentConverter(DocumentConverterPort):
    def __init__(self, content: bytes = b"pdf-bytes") -> None:
        self._content = content
        self.calls = 0

    def to_pdf(self, docx: bytes) -> bytes:
        self.calls += 1
        return self._content


class FakeChangeTypeCatalog(ChangeTypeCatalog):
    def __init__(self, change_types: Sequence[ChangeType]) -> None:
        self._change_types = tuple(change_types)

    def list_active(self) -> Sequence[ChangeType]:
        return tuple(change_type for change_type in self._change_types if change_type.active)

    def get(self, change_type_id: int) -> ChangeType | None:
        for change_type in self._change_types:
            if change_type.id == change_type_id:
                return change_type
        return None


class FakePositionCatalog(PositionCatalog):
    def __init__(self, positions: Sequence[Position]) -> None:
        self._positions = tuple(positions)

    def list_by_role(self, role: SignatureRole) -> Sequence[Position]:
        return tuple(
            position
            for position in self._positions
            if position.role == role and position.active
        )

    def list_active(self) -> Sequence[Position]:
        return tuple(position for position in self._positions if position.active)

    def get(self, position_id: int) -> Position | None:
        for position in self._positions:
            if position.id == position_id:
                return position
        return None
