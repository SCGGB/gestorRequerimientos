from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, TypeVar

from app.domain.requirement.attachment import Attachment
from app.domain.requirement.enums import SignatureRole
from app.domain.requirement.errors import RequirementNotEditableError
from app.domain.requirement.items import (
    Benefit,
    CollectionItem,
    Consideration,
    FutureRequirementItem,
    Objective,
    Restriction,
    Risk,
    Volumetry,
)
from app.domain.requirement.signature import Signature

ItemT = TypeVar("ItemT", bound=CollectionItem)


@dataclass(frozen=True, slots=True)
class RequirementVersion:
    """Contenido congelable de un requerimiento (una version documental)."""

    number: int
    document_version: str
    version_date: date
    title: str
    future_requirements_applies: bool = False
    requirement_id: int | None = None
    change_type_id: int | None = None
    system: str | None = None
    current_need: str | None = None
    context_description: str | None = None
    context_error_handling: str | None = None
    users_permissions: str | None = None
    future_requirements_text: str | None = None
    dynamic_fields: Mapping[str, Any] = field(default_factory=dict)
    frozen: bool = False
    objectives: tuple[Objective, ...] = ()
    considerations: tuple[Consideration, ...] = ()
    benefits: tuple[Benefit, ...] = ()
    restrictions: tuple[Restriction, ...] = ()
    volumetry: tuple[Volumetry, ...] = ()
    risks: tuple[Risk, ...] = ()
    future_requirements_items: tuple[FutureRequirementItem, ...] = ()
    signatures: tuple[Signature, ...] = ()
    attachments: tuple[Attachment, ...] = ()
    id: int | None = None

    def is_working(self) -> bool:
        """Una version de trabajo es la unica no congelada del requerimiento."""
        return not self.frozen

    def ensure_working(self) -> None:
        """Exige que la version no este congelada para admitir edicion."""
        if self.frozen:
            raise RequirementNotEditableError(
                "Una version congelada no admite edicion."
            )

    def freeze(self) -> "RequirementVersion":
        """Congela la version; si ya estaba congelada la devuelve igual."""
        if self.frozen:
            return self
        return replace(self, frozen=True)

    def with_signature(self, signature: Signature) -> "RequirementVersion":
        return replace(self, signatures=(*self.signatures, signature))

    def with_attachment(self, attachment: Attachment) -> "RequirementVersion":
        return replace(self, attachments=(*self.attachments, attachment))

    def active_objectives(self) -> tuple[Objective, ...]:
        return self._active(self.objectives)

    def active_considerations(self) -> tuple[Consideration, ...]:
        return self._active(self.considerations)

    def active_benefits(self) -> tuple[Benefit, ...]:
        return self._active(self.benefits)

    def active_restrictions(self) -> tuple[Restriction, ...]:
        return self._active(self.restrictions)

    def active_volumetry(self) -> tuple[Volumetry, ...]:
        return self._active(self.volumetry)

    def active_risks(self) -> tuple[Risk, ...]:
        return self._active(self.risks)

    def active_future_requirements(self) -> tuple[FutureRequirementItem, ...]:
        return self._active(self.future_requirements_items)

    def signatures_by_role(self, role: SignatureRole) -> tuple[Signature, ...]:
        return tuple(signature for signature in self.signatures if signature.role == role)

    @staticmethod
    def _active(items: tuple[ItemT, ...]) -> tuple[ItemT, ...]:
        return tuple(item for item in items if item.active)
