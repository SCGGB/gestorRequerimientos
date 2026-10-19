from datetime import date

from app.domain.requirement.enums import BenefitKind, RequirementStatus, SignatureRole
from app.domain.requirement.items import (
    Benefit,
    Consideration,
    FutureRequirementItem,
    Objective,
    Restriction,
    Risk,
    Volumetry,
)
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.signature import Signature
from app.domain.requirement.validation import validate_requirement
from app.domain.requirement.version import RequirementVersion


def _complete_version(**overrides: object) -> RequirementVersion:
    defaults: dict[str, object] = {
        "number": 1,
        "document_version": "1.0",
        "version_date": date(2026, 10, 13),
        "title": "Titulo",
        "change_type_id": 7,
        "system": "Sistema",
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


def _requirement(version: RequirementVersion | None = None) -> Requirement:
    versions = (version,) if version is not None else ()
    return Requirement(folio=1, versions=versions)


def test_complete_requirement_is_valid() -> None:
    result = validate_requirement(_requirement(_complete_version()))
    assert result.is_valid is True
    assert result.errors == ()


def test_missing_header_reports_errors_per_field() -> None:
    version = _complete_version(
        title="   ",
        change_type_id=None,
        system=None,
        document_version="",
        current_need=None,
    )
    result = validate_requirement(_requirement(version))

    paths = {issue.path for issue in result.errors}
    assert result.is_valid is False
    assert "datos_generales.titulo" in paths
    assert "datos_generales.tipo_cambio" in paths
    assert "datos_generales.sistema" in paths
    assert "datos_generales.version_documento" in paths
    assert "necesidad_actual" in paths
    for issue in result.errors:
        assert issue.code
        assert issue.message
        assert issue.section


def test_issue_exposes_path_code_message_and_section() -> None:
    result = validate_requirement(_requirement(_complete_version(objectives=())))
    issue = next(item for item in result.errors if item.path == "objetivos")
    assert issue.code == "min_active_items"
    assert issue.section == "Objetivos generales"
    assert issue.message


def test_only_active_items_count() -> None:
    version = _complete_version(
        objectives=(Objective(content="Objetivo", order=1, active=False),),
    )
    result = validate_requirement(_requirement(version))
    assert any(issue.path == "objetivos" for issue in result.errors)


def test_future_requirements_not_applying_is_valid() -> None:
    version = _complete_version(
        future_requirements_applies=False,
        future_requirements_text=None,
        future_requirements_items=(),
    )
    result = validate_requirement(_requirement(version))
    assert result.is_valid is True


def test_future_requirements_applying_without_content_is_rejected() -> None:
    version = _complete_version(
        future_requirements_applies=True,
        future_requirements_text="  ",
        future_requirements_items=(),
    )
    result = validate_requirement(_requirement(version))
    issue = next(
        item for item in result.errors if item.code == "future_requirements_missing"
    )
    assert issue.path == "requisitos_futuros_texto"
    assert issue.section == "Requisitos futuros"


def test_future_requirements_applying_with_active_item_is_valid() -> None:
    version = _complete_version(
        future_requirements_applies=True,
        future_requirements_text=None,
        future_requirements_items=(FutureRequirementItem(content="Futuro", order=1),),
    )
    result = validate_requirement(_requirement(version))
    assert result.is_valid is True


def test_orphan_future_requirements_is_a_warning() -> None:
    version = _complete_version(
        future_requirements_applies=False,
        future_requirements_text="Texto",
    )
    result = validate_requirement(_requirement(version))
    assert result.is_valid is True
    assert any(
        issue.code == "future_requirements_orphan" for issue in result.warnings
    )


def test_signatures_are_required_only_when_target_is_generado() -> None:
    version = _complete_version()
    base_result = validate_requirement(_requirement(version))
    assert base_result.is_valid is True

    target_result = validate_requirement(
        _requirement(version), target_state=RequirementStatus.GENERADO
    )
    paths = {issue.path for issue in target_result.errors}
    assert target_result.is_valid is False
    assert "signers.ELABORO.nombre" in paths
    assert "signers.AUTORIZO.nombre" in paths


def test_signatures_satisfied_when_target_is_generado() -> None:
    version = _complete_version(
        signatures=(
            Signature(role=SignatureRole.ELABORO, name="Ana", position="Analista"),
            Signature(role=SignatureRole.AUTORIZO, name="Luis", position="Jefe"),
        )
    )
    result = validate_requirement(
        _requirement(version), target_state=RequirementStatus.GENERADO
    )
    assert result.is_valid is True


def test_missing_current_version_is_reported() -> None:
    result = validate_requirement(_requirement())
    assert result.is_valid is False
    assert result.errors[0].code == "no_current_version"
