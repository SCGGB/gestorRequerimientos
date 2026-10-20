from datetime import UTC, datetime, timedelta

from app.application.errors import (
    AccountLockedError,
    InvalidCredentialsError,
)
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.password_hasher import PasswordHasherPort
from app.application.ports.token_service import TokenServicePort
from app.application.ports.user_repository import UserRepository
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.auth.session import Session


class AuthenticateUser:
    """Autentica un usuario local, controla bloqueo y emite el token de sesion."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasherPort,
        token_service: TokenServicePort,
        audit: AuditRecorderPort,
        *,
        session_ttl_hours: int,
        max_failed_attempts: int,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._audit = audit
        self._session_ttl_hours = session_ttl_hours
        self._max_failed_attempts = max_failed_attempts

    def execute(self, usuario: str, contrasena: str) -> str:
        user = self._user_repository.get_by_username(usuario)
        if user is None:
            self._record_failed_login(usuario, motivo="usuario inexistente")
            raise InvalidCredentialsError()

        if user.is_locked(self._max_failed_attempts):
            self._audit.record(
                AuditEntry(
                    entity="SYS_USUARIO",
                    entity_id=user.id,
                    action=AuditAction.LOGIN_BLOCKED,
                    actor=usuario,
                    detail={"motivo": "maximo de intentos fallidos alcanzado"},
                )
            )
            raise AccountLockedError()

        if not self._password_hasher.verify(contrasena, user.password_hash):
            updated = user.record_failed_attempt()
            self._user_repository.save(updated)
            self._record_failed_login(
                usuario,
                motivo="clave incorrecta",
                entity_id=user.id,
                intentos=updated.failed_attempts,
            )
            raise InvalidCredentialsError()

        if not user.active:
            self._record_failed_login(usuario, motivo="usuario inactivo", entity_id=user.id)
            raise InvalidCredentialsError()

        self._user_repository.save(user.reset_failed_attempts())

        now = datetime.now(tz=UTC)
        session = Session(
            user_id=user.username,
            roles=user.roles,
            issued_at=now,
            expires_at=now + timedelta(hours=self._session_ttl_hours),
        )
        self._audit.record(
            AuditEntry(
                entity="SYS_USUARIO",
                entity_id=user.id,
                action=AuditAction.LOGIN_SUCCESS,
                actor=user.username,
            )
        )
        return self._token_service.issue(session)

    def _record_failed_login(
        self,
        usuario: str,
        *,
        motivo: str,
        entity_id: int | None = None,
        intentos: int | None = None,
    ) -> None:
        detail: dict[str, object] = {"motivo": motivo}
        if intentos is not None:
            detail["intentos"] = intentos
        self._audit.record(
            AuditEntry(
                entity="SYS_USUARIO",
                entity_id=entity_id,
                action=AuditAction.LOGIN_FAILED,
                actor=usuario,
                detail=detail,
            )
        )
