from dataclasses import dataclass

from app.domain.requirement.enums import RequirementStatus, SignatureRole
from app.domain.requirement.requirement import Requirement
from app.domain.requirement.version import RequirementVersion


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Hallazgo de validacion con ubicacion accionable."""

    path: str
    code: str
    message: str
    section: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Resultado inmutable de una validacion integral."""

    errors: tuple[ValidationIssue, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _issue(path: str, code: str, message: str, section: str) -> ValidationIssue:
    return ValidationIssue(path=path, code=code, message=message, section=section)


def validate_requirement(
    requirement: Requirement,
    *,
    target_state: RequirementStatus | None = None,
) -> ValidationResult:
    """Valida la version vigente del requerimiento (dry-run, sin efectos)."""
    version = requirement.current_version()
    if version is None:
        return ValidationResult(
            errors=(
                _issue(
                    "version",
                    "no_current_version",
                    "El requerimiento no tiene una version vigente.",
                    "Version vigente",
                ),
            )
        )

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    _validate_general_data(version, errors)
    _require_text(
        version.current_need,
        "necesidad_actual",
        "Necesidad actual",
        errors,
    )
    _require_active_items(
        len(version.active_objectives()),
        "objetivos",
        "Objetivos generales",
        errors,
    )
    _require_active_items(
        len(version.active_considerations()),
        "consideraciones",
        "Consideraciones",
        errors,
    )
    _require_active_items(
        len(version.active_benefits()),
        "beneficios",
        "Beneficios esperados",
        errors,
    )
    _require_text(
        version.context_description,
        "contexto_descripcion",
        "Diagramas contextuales",
        errors,
    )
    _require_text(
        version.users_permissions,
        "usuarios_permisos",
        "Usuarios y permisos",
        errors,
    )
    _require_active_items(
        len(version.active_restrictions()),
        "restricciones",
        "Restricciones",
        errors,
    )
    _validate_future_requirements(version, errors, warnings)
    _require_active_items(
        len(version.active_volumetry()),
        "volumetria",
        "Volumetria y rendimiento",
        errors,
    )
    _require_active_items(
        len(version.active_risks()),
        "riesgos",
        "Riesgos iniciales",
        errors,
    )
    if target_state is RequirementStatus.GENERADO:
        _validate_signatures(version, errors)

    return ValidationResult(errors=tuple(errors), warnings=tuple(warnings))


def _validate_general_data(
    version: RequirementVersion, errors: list[ValidationIssue]
) -> None:
    _require_text(
        version.title,
        "datos_generales.titulo",
        "Datos generales",
        errors,
    )
    if version.change_type_id is None:
        errors.append(
            _issue(
                "datos_generales.tipo_cambio",
                "required_field",
                "El tipo de cambio es obligatorio.",
                "Datos generales",
            )
        )
    _require_text(
        version.system,
        "datos_generales.sistema",
        "Datos generales",
        errors,
    )
    _require_text(
        version.document_version,
        "datos_generales.version_documento",
        "Datos generales",
        errors,
    )


def _require_text(
    value: str | None,
    path: str,
    section: str,
    errors: list[ValidationIssue],
) -> None:
    if value is None or not value.strip():
        errors.append(
            _issue(
                path,
                "required_field",
                f"El campo de '{section}' es obligatorio.",
                section,
            )
        )


def _require_active_items(
    count: int,
    path: str,
    section: str,
    errors: list[ValidationIssue],
) -> None:
    if count < 1:
        errors.append(
            _issue(
                path,
                "min_active_items",
                f"Debe existir al menos un elemento activo en '{section}'.",
                section,
            )
        )


def _validate_future_requirements(
    version: RequirementVersion,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    active_items = version.active_future_requirements()
    has_text = bool(version.future_requirements_text and version.future_requirements_text.strip())

    if version.future_requirements_applies:
        if not has_text and not active_items:
            errors.append(
                _issue(
                    "requisitos_futuros_texto",
                    "future_requirements_missing",
                    "Debe capturar el texto de requisitos futuros o al menos un elemento activo.",
                    "Requisitos futuros",
                )
            )
    elif has_text or active_items:
        warnings.append(
            _issue(
                "requisitos_futuros_texto",
                "future_requirements_orphan",
                "La seccion de requisitos futuros no aplica, pero contiene informacion capturada.",
                "Requisitos futuros",
            )
        )


def _validate_signatures(
    version: RequirementVersion, errors: list[ValidationIssue]
) -> None:
    for role in (SignatureRole.ELABORO, SignatureRole.AUTORIZO):
        signatures = version.signatures_by_role(role)
        if not any(signature.name.strip() for signature in signatures):
            errors.append(
                _issue(
                    f"signers.{role.value}.nombre",
                    "signatures_missing",
                    f"Falta el nombre de la firma {role.value} del control documental.",
                    "Control documental",
                )
            )
