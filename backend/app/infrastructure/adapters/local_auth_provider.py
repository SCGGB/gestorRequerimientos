from __future__ import annotations

from app.application.ports.auth import AuthProvider, Principal
from app.application.ports.token_service import TokenServicePort
from app.application.ports.user_repository import UserRepository

_BEARER_PREFIX = "Bearer "


class AuthProviderConfigurationError(RuntimeError):
    """El proveedor de autenticacion configurado no esta disponible."""


class LocalJwtAuthProvider(AuthProvider):
    """AuthProvider local (ADR-003): parsea el token y recarga el usuario de la BD.

    Devuelve ``None`` en cualquier fallo (sin token, token invalido, expirado o
    usuario inactivo); la dependencia de request traduce eso a 401.
    """

    def __init__(
        self,
        token_service: TokenServicePort,
        user_repository: UserRepository,
        authorization: str | None,
    ) -> None:
        self._token_service = token_service
        self._user_repository = user_repository
        self._authorization = authorization

    def current_principal(self) -> Principal | None:
        token = self._extract_bearer_token(self._authorization)
        if token is None:
            return None
        session = self._token_service.parse(token)
        if session is None:
            return None
        user = self._user_repository.get_by_username(session.user_id)
        if user is None or not user.active:
            return None
        return Principal(
            user_id=user.username,
            roles=frozenset(role.value for role in user.roles),
        )

    @staticmethod
    def _extract_bearer_token(authorization: str | None) -> str | None:
        if authorization is None or not authorization.startswith(_BEARER_PREFIX):
            return None
        token = authorization[len(_BEARER_PREFIX) :].strip()
        return token or None


def build_auth_provider(
    provider: str,
    *,
    token_service: TokenServicePort,
    user_repository: UserRepository,
    authorization: str | None,
) -> AuthProvider:
    """Construye el AuthProvider segun ``Settings.auth_provider``.

    ``local_jwt`` -> adaptador local; ``oidc`` -> error de configuracion claro
    (fase posterior de ADR-003).
    """
    if provider == "local_jwt":
        return LocalJwtAuthProvider(token_service, user_repository, authorization)
    raise AuthProviderConfigurationError(
        f"Proveedor de autenticacion '{provider}' no disponible en esta fase "
        "(ver ADR-003: OIDC es una fase posterior)."
    )
