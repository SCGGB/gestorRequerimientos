from dataclasses import replace

from app.application.errors import SelfDeactivationError, UserNotFoundError
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.password_hasher import PasswordHasherPort
from app.application.ports.user_repository import UserRepository
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.auth.roles import Role
from app.domain.auth.user import SelfDeactivationError as DomainSelfDeactivationError
from app.domain.auth.user import User


class UpdateUser:
    """Edicion de usuario; siempre reinicia INTENTOS_FALLIDOS (RF-09, CA-09)."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasherPort,
        audit: AuditRecorderPort,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._audit = audit

    def execute(
        self,
        principal: Principal,
        user_id: int,
        *,
        nombre: str | None = None,
        contrasena: str | None = None,
        roles: frozenset[Role] | None = None,
        activo: bool | None = None,
    ) -> User:
        user = self._user_repository.get(user_id)
        if user is None:
            raise UserNotFoundError()

        if activo is False:
            try:
                user.ensure_can_be_deactivated_by(principal.user_id)
            except DomainSelfDeactivationError as exc:
                raise SelfDeactivationError() from exc

        changed: dict[str, object] = {}
        updated = user
        if nombre is not None and nombre != user.name:
            updated = replace(updated, name=nombre)
            changed["nombre"] = nombre
        if contrasena is not None:
            updated = replace(
                updated, password_hash=self._password_hasher.hash(contrasena)
            )
            changed["contrasena"] = "cambiada"
        if roles is not None and roles != user.roles:
            updated = replace(updated, roles=roles)
            changed["roles"] = sorted(role.value for role in roles)
        if activo is not None and activo != user.active:
            updated = replace(updated, active=activo)
            changed["activo"] = activo

        updated = replace(updated, failed_attempts=0)
        if user.failed_attempts != 0:
            changed["intentos_fallidos"] = 0

        saved = self._user_repository.save(updated)
        self._audit.record(
            AuditEntry(
                entity="SYS_USUARIO",
                entity_id=saved.id,
                action=AuditAction.USER_UPDATE,
                actor=principal.user_id,
                detail={"usuario": saved.username, "cambios": changed},
            )
        )
        return saved
