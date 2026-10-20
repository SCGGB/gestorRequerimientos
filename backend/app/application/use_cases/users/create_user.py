from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.password_hasher import PasswordHasherPort
from app.application.ports.user_repository import UserRepository
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.auth.roles import Role
from app.domain.auth.user import User


class CreateUser:
    """Alta de usuario local con roles y hash de contrasena (solo ADMIN via API)."""

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
        *,
        usuario: str,
        nombre: str,
        contrasena: str,
        roles: frozenset[Role],
        activo: bool = True,
    ) -> User:
        user = User(
            username=usuario,
            name=nombre,
            password_hash=self._password_hasher.hash(contrasena),
            roles=roles,
            active=activo,
        )
        saved = self._user_repository.save(user)
        self._audit.record(
            AuditEntry(
                entity="SYS_USUARIO",
                entity_id=saved.id,
                action=AuditAction.USER_CREATE,
                actor=principal.user_id,
                detail={
                    "usuario": saved.username,
                    "roles": sorted(role.value for role in saved.roles),
                    "activo": saved.active,
                },
            )
        )
        return saved
