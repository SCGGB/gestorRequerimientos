from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement._common import (
    load_editable_working_version,
    replace_version,
)
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion

_EDITABLE_FIELDS: tuple[str, ...] = (
    "title",
    "change_type_id",
    "system",
    "document_version",
    "version_date",
    "current_need",
    "context_description",
    "context_error_handling",
    "users_permissions",
    "future_requirements_applies",
    "future_requirements_text",
    "dynamic_fields",
)


@dataclass(frozen=True, slots=True)
class VersionEdit:
    """Campos de cabecera/narrativa a actualizar; ``None`` = no informado."""

    title: str | None = None
    change_type_id: int | None = None
    system: str | None = None
    document_version: str | None = None
    version_date: date | None = None
    current_need: str | None = None
    context_description: str | None = None
    context_error_handling: str | None = None
    users_permissions: str | None = None
    future_requirements_applies: bool | None = None
    future_requirements_text: str | None = None
    dynamic_fields: Mapping[str, Any] | None = None


class UpdateVersion:
    """Edita la cabecera/narrativa de la version de trabajo en BORRADOR."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        edit: VersionEdit,
    ) -> Requirement:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        updated = self._apply(version, edit)
        return self._repository.save(replace_version(requirement, version, updated))

    @staticmethod
    def _apply(version: RequirementVersion, edit: VersionEdit) -> RequirementVersion:
        changes = {
            field: value
            for field in _EDITABLE_FIELDS
            if (value := getattr(edit, field)) is not None
        }
        if not changes:
            return version
        return replace(version, **changes)
