from dataclasses import replace

from app.application.errors import VersionNotFoundError
from app.application.ports.requirement_repository import RequirementRepository
from app.domain.requirement.enums import SignatureRole
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion


class RegisterSignature:
    """Registra una firma sobre la version vigente en estado final (ADR-007)."""

    def __init__(self, repository: RequirementRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        *,
        role: SignatureRole,
        name: str,
        position: str,
        position_id: int | None = None,
    ) -> Signature:
        requirement = self._repository.get(requirement_id)
        if requirement.version_by_id(version_id) is None:
            raise VersionNotFoundError()
        requirement.ensure_signable(version_id)

        if role is SignatureRole.AUTORIZO:
            updated = requirement.authorize(
                version_id=version_id,
                name=name,
                position=position,
                position_id=position_id,
            )
        else:
            updated = self._append_signature(
                requirement, version_id, role, name, position, position_id
            )

        saved = self._repository.save(updated)
        version = saved.version_by_id(version_id)
        if version is None:
            raise VersionNotFoundError()
        return self._last_signature(version, role)

    @staticmethod
    def _append_signature(
        requirement: Requirement,
        version_id: int,
        role: SignatureRole,
        name: str,
        position: str,
        position_id: int | None,
    ) -> Requirement:
        current = requirement.current_version()
        if current is None:
            raise VersionNotFoundError()
        signature = Signature(
            role=role,
            name=name,
            position=position,
            version_id=version_id,
            position_id=position_id,
        )
        updated = current.with_signature(signature)
        return replace(
            requirement,
            versions=tuple(
                updated if candidate is current else candidate
                for candidate in requirement.versions
            ),
        )

    @staticmethod
    def _last_signature(version: RequirementVersion, role: SignatureRole) -> Signature:
        signatures = version.signatures_by_role(role)
        if not signatures:
            raise VersionNotFoundError()
        return signatures[-1]
