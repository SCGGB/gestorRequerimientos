from dataclasses import dataclass, field

from app.domain.requirement.enums import BenefitKind


@dataclass(frozen=True, slots=True)
class CollectionItem:
    """Elemento independiente de una coleccion ordenada y versionada."""

    content: str
    order: int
    active: bool = True
    id: int | None = None


@dataclass(frozen=True, slots=True)
class Objective(CollectionItem):
    """Objetivo general del requerimiento."""


@dataclass(frozen=True, slots=True)
class Consideration(CollectionItem):
    """Consideracion, regla o supuesto del requerimiento."""


@dataclass(frozen=True, slots=True)
class Restriction(CollectionItem):
    """Restriccion del requerimiento."""


@dataclass(frozen=True, slots=True)
class Volumetry(CollectionItem):
    """Elemento de volumetria y rendimiento."""


@dataclass(frozen=True, slots=True)
class Risk(CollectionItem):
    """Riesgo inicial del requerimiento."""


@dataclass(frozen=True, slots=True)
class FutureRequirementItem(CollectionItem):
    """Requisito futuro cuando la seccion aplica."""


@dataclass(frozen=True, slots=True)
class Benefit(CollectionItem):
    """Beneficio cualitativo o cuantitativo, discriminado por ``kind``."""

    kind: BenefitKind = field(kw_only=True)
