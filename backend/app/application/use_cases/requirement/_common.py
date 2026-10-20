from dataclasses import replace

from app.application.errors import VersionNotFoundError
from app.application.ports.auth import Principal
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.auth.roles import Role
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion


def principal_roles(principal: Principal) -> frozenset[Role]:
    """Convierte los roles del principal (textos) al enumerado del dominio."""
    return frozenset(Role(value) for value in principal.roles)


def load_editable_working_version(
    repository: RequirementRepository,
    requirement_id: int,
    version_id: int,
) -> tuple[Requirement, RequirementVersion]:
    """Carga el requerimiento y su version de trabajo editable (BORRADOR, no congelada)."""
    requirement = repository.get(requirement_id)
    requirement.ensure_editable()
    version = requirement.version_by_id(version_id)
    if version is None:
        raise VersionNotFoundError()
    version.ensure_working()
    return requirement, version


def replace_version(
    requirement: Requirement,
    version: RequirementVersion,
    updated: RequirementVersion,
) -> Requirement:
    """Devuelve el requerimiento con esa version sustituida."""
    return replace(
        requirement,
        versions=tuple(
            updated if candidate is version else candidate
            for candidate in requirement.versions
        ),
    )


def save_version(
    repository: RequirementRepository,
    requirement: Requirement,
    version: RequirementVersion,
    updated: RequirementVersion,
    *,
    actor: str,
) -> RequirementVersion:
    """Persiste el agregado y devuelve la version recargada por su id."""
    saved = repository.save(replace_version(requirement, version, updated), actor=actor)
    if version.id is None:
        return updated
    reloaded = saved.version_by_id(version.id)
    if reloaded is None:
        raise VersionNotFoundError()
    return reloaded
