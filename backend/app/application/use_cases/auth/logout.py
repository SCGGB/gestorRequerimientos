from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.domain.auth.audit import AuditAction, AuditEntry


class LogoutUser:
    """Registra el cierre de sesion; la invalidacion del token es por expiracion."""

    def __init__(self, audit: AuditRecorderPort) -> None:
        self._audit = audit

    def execute(self, principal: Principal) -> None:
        self._audit.record(
            AuditEntry(
                entity="SYS_USUARIO",
                entity_id=None,
                action=AuditAction.LOGOUT,
                actor=principal.user_id,
            )
        )
