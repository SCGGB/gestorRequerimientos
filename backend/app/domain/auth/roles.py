from enum import StrEnum


class Role(StrEnum):
    """Roles del MVP (ADR-003)."""

    ELABORO = "ELABORO"
    REVISO = "REVISO"
    AUTORIZO = "AUTORIZO"
    ADMIN = "ADMIN"
