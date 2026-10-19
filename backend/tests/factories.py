from datetime import date

from app.domain.requirement.enums import BenefitKind, RequirementStatus
from app.domain.requirement.items import (
    Benefit,
    Consideration,
    Objective,
    Restriction,
    Risk,
    Volumetry,
)
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion


def complete_version(**overrides: object) -> RequirementVersion:
    """Version de requerimiento completa y valida para pruebas."""
    defaults: dict[str, object] = {
        "number": 1,
        "document_version": "1.0",
        "version_date": date(2026, 1, 1),
        "title": "Titulo",
        "change_type_id": 1,
        "system": "SAP",
        "current_need": "Necesidad",
        "context_description": "Contexto",
        "users_permissions": "Usuarios",
        "objectives": (Objective(content="Objetivo", order=1),),
        "considerations": (Consideration(content="Consideracion", order=1),),
        "benefits": (
            Benefit(content="Beneficio", order=1, kind=BenefitKind.CUALITATIVO),
        ),
        "restrictions": (Restriction(content="Restriccion", order=1),),
        "volumetry": (Volumetry(content="Volumetria", order=1),),
        "risks": (Risk(content="Riesgo", order=1),),
    }
    defaults.update(overrides)
    return RequirementVersion(**defaults)  # type: ignore[arg-type]


def requirement_with(
    version: RequirementVersion | None = None,
    *,
    status: RequirementStatus = RequirementStatus.BORRADOR,
    **overrides: object,
) -> Requirement:
    """Requerimiento con una version; acepta una version existente o `overrides`."""
    if version is None:
        version = complete_version(**overrides)
    return Requirement(folio=1, status=status, versions=(version,))
