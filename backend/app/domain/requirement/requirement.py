from dataclasses import dataclass, replace
from datetime import date

from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.errors import (
    AuthorizationNotOnCurrentVersionError,
    DomainError,
    InvalidFolioError,
    InvalidStateTransitionError,
    MultipleWorkingVersionsError,
    RequirementNotEditableError,
    SignatureNotAllowedError,
)
from app.domain.requirement.items import CollectionItem
from app.domain.requirement.signature import Signature
from app.domain.requirement.version import RequirementVersion

_ALLOWED_TRANSITIONS: dict[RequirementStatus, frozenset[RequirementStatus]] = {
    RequirementStatus.BORRADOR: frozenset(
        {RequirementStatus.EN_REVISION, RequirementStatus.CANCELADO}
    ),
    RequirementStatus.EN_REVISION: frozenset(
        {
            RequirementStatus.VALIDADO,
            RequirementStatus.BORRADOR,
            RequirementStatus.CANCELADO,
        }
    ),
    RequirementStatus.VALIDADO: frozenset(
        {
            RequirementStatus.APROBADO,
            RequirementStatus.EN_REVISION,
            RequirementStatus.CANCELADO,
        }
    ),
    RequirementStatus.APROBADO: frozenset(
        {RequirementStatus.GENERADO, RequirementStatus.CANCELADO}
    ),
    RequirementStatus.GENERADO: frozenset(),
    RequirementStatus.CANCELADO: frozenset(),
}


def _detach[ItemT: CollectionItem](items: tuple[ItemT, ...]) -> tuple[ItemT, ...]:
    """Copia elementos activos con id nuevo para una version de trabajo sucesora."""
    return tuple(replace(item, id=None) for item in items if item.active)


@dataclass(frozen=True, slots=True)
class Requirement:
    """Contenedor estable del requerimiento (folio, estado y version vigente)."""

    folio: int
    status: RequirementStatus = RequirementStatus.BORRADOR
    current_version_id: int | None = None
    versions: tuple[RequirementVersion, ...] = ()
    id: int | None = None

    def __post_init__(self) -> None:
        if self.folio < 1:
            raise InvalidFolioError("El folio debe ser un entero positivo.")
        if len(self.working_versions()) > 1:
            raise MultipleWorkingVersionsError(
                "Solo puede existir una version de trabajo por requerimiento."
            )

    @property
    def ticket(self) -> str:
        """Ticket mostrado: prefijo fijo ``T#`` mas el folio."""
        return f"T#{self.folio}"

    def working_versions(self) -> tuple[RequirementVersion, ...]:
        return tuple(version for version in self.versions if version.is_working())

    def version_by_id(self, version_id: int) -> RequirementVersion | None:
        for version in self.versions:
            if version.id == version_id:
                return version
        return None

    def ensure_editable(self) -> None:
        """Exige que el requerimiento este en estado editable (BORRADOR)."""
        if self.status is not RequirementStatus.BORRADOR:
            raise RequirementNotEditableError(
                "Solo se puede editar un requerimiento en BORRADOR."
            )

    def ensure_signable(self, version_id: int) -> None:
        """Exige estado final y que la version sea la vigente (ADR-007)."""
        if self.status not in (
            RequirementStatus.APROBADO,
            RequirementStatus.GENERADO,
        ):
            raise SignatureNotAllowedError(
                "Solo se registran firmas con estado APROBADO o GENERADO."
            )
        current = self.current_version()
        if current is None or current.id != version_id:
            raise SignatureNotAllowedError(
                "Las firmas solo se registran sobre la version vigente."
            )

    def working_version(self) -> RequirementVersion | None:
        working = self.working_versions()
        return working[0] if working else None

    def current_version(self) -> RequirementVersion | None:
        """Version vigente: la apuntada por ``current_version_id`` o la de trabajo."""
        if self.current_version_id is not None:
            for version in self.versions:
                if version.id == self.current_version_id:
                    return version
        return self.working_version()

    def change_status(self, target: RequirementStatus) -> "Requirement":
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStateTransitionError(
                f"Transicion no permitida: {self.status} -> {target}"
            )
        return replace(self, status=target)

    def freeze_and_advance(
        self,
        *,
        document_version: str,
        version_date: date,
        title: str,
    ) -> "Requirement":
        """Congela la version de trabajo y crea la siguiente por copy-on-write."""
        working = self.working_version()
        if working is None:
            raise DomainError("No hay version de trabajo que congelar.")

        frozen_versions = tuple(
            version.freeze() if version is working else version for version in self.versions
        )
        next_number = max((version.number for version in self.versions), default=0) + 1
        successor = RequirementVersion(
            number=next_number,
            document_version=document_version,
            version_date=version_date,
            title=title,
            requirement_id=self.id,
            change_type_id=working.change_type_id,
            system=working.system,
            current_need=working.current_need,
            context_description=working.context_description,
            context_error_handling=working.context_error_handling,
            users_permissions=working.users_permissions,
            future_requirements_applies=working.future_requirements_applies,
            future_requirements_text=working.future_requirements_text,
            dynamic_fields=dict(working.dynamic_fields),
            objectives=_detach(working.active_objectives()),
            considerations=_detach(working.active_considerations()),
            benefits=_detach(working.active_benefits()),
            restrictions=_detach(working.active_restrictions()),
            volumetry=_detach(working.active_volumetry()),
            risks=_detach(working.active_risks()),
            future_requirements_items=_detach(working.active_future_requirements()),
        )
        return replace(
            self,
            versions=(*frozen_versions, successor),
            current_version_id=successor.id,
        )

    def authorize(
        self,
        *,
        version_id: int | None,
        name: str,
        position: str,
        position_id: int | None = None,
    ) -> "Requirement":
        """Registra la firma Autorizo unicamente sobre la version vigente."""
        current = self.current_version()
        if current is None or current.id != version_id:
            raise AuthorizationNotOnCurrentVersionError(
                "La firma Autorizo solo se registra en la version vigente."
            )
        signature = Signature(
            role=SignatureRole.AUTORIZO,
            name=name,
            position=position,
            version_id=current.id,
            position_id=position_id,
        )
        updated = current.with_signature(signature)
        return replace(
            self,
            versions=tuple(
                updated if version is current else version for version in self.versions
            ),
        )
