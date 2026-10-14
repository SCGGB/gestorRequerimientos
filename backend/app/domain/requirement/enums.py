from enum import StrEnum


class RequirementStatus(StrEnum):
    BORRADOR = "BORRADOR"
    EN_REVISION = "EN_REVISION"
    VALIDADO = "VALIDADO"
    APROBADO = "APROBADO"
    GENERADO = "GENERADO"
    CANCELADO = "CANCELADO"


class BenefitKind(StrEnum):
    CUALITATIVO = "CUALITATIVO"
    CUANTITATIVO = "CUANTITATIVO"


class SignatureRole(StrEnum):
    ELABORO = "ELABORO"
    REVISO = "REVISO"
    AUTORIZO = "AUTORIZO"


class ActiveFlag(StrEnum):
    S = "S"
    N = "N"
