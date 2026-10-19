from pydantic import BaseModel, Field

from app.application.use_cases.requirement.transition_requirement_state import (
    TransitionOutcome,
)
from app.domain.requirement.enums import RequirementStatus
from app.domain.requirement.validation import ValidationIssue, ValidationResult


class ValidationErrorSchema(BaseModel):
    path: str
    codigo: str
    mensaje: str
    seccion: str

    @classmethod
    def from_domain(cls, issue: ValidationIssue) -> "ValidationErrorSchema":
        return cls(
            path=issue.path,
            codigo=issue.code,
            mensaje=issue.message,
            seccion=issue.section,
        )


class ValidationResultResponse(BaseModel):
    valido: bool
    errores: list[ValidationErrorSchema] = Field(default_factory=list)
    advertencias: list[ValidationErrorSchema] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, result: ValidationResult) -> "ValidationResultResponse":
        return cls(
            valido=result.is_valid,
            errores=[
                ValidationErrorSchema.from_domain(issue) for issue in result.errors
            ],
            advertencias=[
                ValidationErrorSchema.from_domain(issue) for issue in result.warnings
            ],
        )


class ValidationRequest(BaseModel):
    a_estado: RequirementStatus | None = None


class StateTransitionRequest(BaseModel):
    a_estado: str
    motivo: str | None = None
    actor_id: int | None = None


class StateTransitionResponse(BaseModel):
    estado_anterior: str
    estado_actual: str
    transicion_valida: bool
    errores: list[ValidationErrorSchema] = Field(default_factory=list)

    @classmethod
    def from_outcome(cls, outcome: TransitionOutcome) -> "StateTransitionResponse":
        return cls(
            estado_anterior=outcome.previous_status.value,
            estado_actual=outcome.current_status.value,
            transicion_valida=outcome.is_valid,
            errores=[
                ValidationErrorSchema.from_domain(issue) for issue in outcome.errors
            ],
        )
