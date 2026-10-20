from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class AuditAction(StrEnum):
    """Acciones relevantes registradas en SYS_AUDITORIA."""

    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGIN_BLOCKED = "LOGIN_BLOCKED"
    LOGOUT = "LOGOUT"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    REQUIREMENT_CREATE = "REQUIREMENT_CREATE"
    VERSION_UPDATE = "VERSION_UPDATE"
    VERSION_FREEZE = "VERSION_FREEZE"
    STATE_TRANSITION = "STATE_TRANSITION"
    SIGNATURE_REGISTERED = "SIGNATURE_REGISTERED"
    DOCUMENT_GENERATED = "DOCUMENT_GENERATED"
    DOCUMENT_DOWNLOADED = "DOCUMENT_DOWNLOADED"
    COLLECTION_UPDATE = "COLLECTION_UPDATE"
    ATTACHMENT_UPDATE = "ATTACHMENT_UPDATE"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """Entrada de auditoria: entidad, accion, actor, detalle y marcas de tiempo."""

    entity: str
    action: AuditAction
    actor: str
    entity_id: int | None = None
    detail: Mapping[str, Any] | None = None
    created_at: datetime | None = None
