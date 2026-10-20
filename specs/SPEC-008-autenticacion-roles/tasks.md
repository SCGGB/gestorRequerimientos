# Tareas - SPEC-008

> Tareas atomicas, ordenadas por dependencia. Cada una referencia el requisito funcional (RF) y el
> criterio de aceptacion (CA) que cubre. Backend (dominio + application + api + infraestructura) +
> frontend (sesion, overlay de login y gestion de usuarios). El diseno completo (decisiones, matriz de
> autorizacion mapeada a TODOS los endpoints de `/api/v1`, contratos y estrategia de pruebas) esta en
> `specs/SPEC-008-autenticacion-roles/plan.md`.
>
> **Fuera de alcance** (no incluido en estas tareas): adaptador OIDC (fase posterior, ADR-003),
> historial de transiciones como tabla o pantalla, restablecimiento de contrasena por correo, purgado
> o consulta de `SYS_AUDITORIA`, firma electronica (ADR-005), y cambios a la maquina de estados
> (SPEC-005) o a la politica de firmas ADR-007.
>
> **Modelo de datos Oracle / migraciones Alembic:** nuevas tablas `SYS_USUARIO` y `SYS_USUARIO_ROL`;
> `SYS_AUDITORIA` no cambia de DDL pero se agrega su definicion a `tables.py` (hoy ausente); migracion
> `0004_usuarios_autenticacion` (`down_revision = "0003_documentos_generados"`) que crea las tablas y
> **siembra el usuario `ADMIN` inicial** desde variables de entorno. DDL solo via Alembic.
>
> **Dependencias nuevas: ninguna** (RF-15): JWT HS256 y hashing PBKDF2-HMAC-SHA256 con stdlib,
> justificados en `plan.md`, seccion "Enfoque".
>
> Convencion de commits: un commit al cierre de cada fase con prefijo `SPEC-008:`.

## Fase A — Dominio puro (sin FastAPI/SQLAlchemy/JWT)

Commit de fase: `SPEC-008: dominio auth (roles, autorizacion, usuario, sesion, auditoria)`

- [ ] T-01 (RF-02, RF-04, RF-05, RF-06, CA-04, CA-05, CA-06, CA-14) Roles del MVP y matriz de
  autorizacion como datos puros
  - Nuevo `backend/app/domain/auth/roles.py`: `Role(StrEnum)` con `ELABORO`, `REVISO`, `AUTORIZO`,
    `ADMIN` (ADR-003).
  - Nuevo `backend/app/domain/auth/authorization.py`: `Action(StrEnum)` (`READ`,
    `REQUIREMENT_WRITE`, `GENERATE_DOCUMENTS`, `DOWNLOAD_DOCUMENTS`, `MANAGE_USERS`);
    `REQUIRED_ROLES: dict[Action, frozenset[Role]]` copiando la matriz aprobada de la spec (`ADMIN`
    explicito en cada accion salvo firmas; sin herencia implicita); `required_roles(action)`,
    `ensure_authorized(roles, action)` (union de permisos, CA-14),
    `ensure_transition_allowed(roles, target_status)` (filas de transicion por estado destino) y
    `ensure_signature_allowed(roles, requested_role)` (cada rol solo la suya, `ADMIN` nunca). Importa
    `domain/requirement/enums` (mismo dominio); sin imports de FastAPI, SQLAlchemy ni librerias JWT.

- [ ] T-02 (RF-08, RF-09, RF-13, CA-01, CA-08, CA-09) Entidad `User` y sesion `Session`
  - Nuevo `backend/app/domain/auth/user.py`: `@dataclass(frozen=True, slots=True)` `User` (`id`,
    `username`, `name`, `password_hash`, `roles: frozenset[Role]`, `active`, `failed_attempts`) con
    `is_locked(max_attempts)`, `record_failed_attempt()` (devuelve `User` actualizado),
    `reset_failed_attempts()`, `ensure_can_be_deactivated_by(actor_username)` (no autodesactivacion)
    y `ensure_active()`. La verificacion de contrasena NO vive aqui (requiere el puerto de hashing).
  - Nuevo `backend/app/domain/auth/session.py`: `Session(user_id, roles, issued_at, expires_at)`,
    `SESSION_TTL = timedelta(hours=8)` e `is_expired(now)` puro; la serializacion JWT va en
    infraestructura (T-08).

- [ ] T-03 (RF-12, CA-11) Acciones de auditoria, entrada de auditoria y error de autorizacion
  - Nuevo `backend/app/domain/auth/audit.py`: `AuditAction(StrEnum)` (`LOGIN_SUCCESS`,
    `LOGIN_FAILED`, `LOGIN_BLOCKED`, `LOGOUT`, `USER_CREATE`, `USER_UPDATE`, `REQUIREMENT_CREATE`,
    `VERSION_UPDATE`, `VERSION_FREEZE`, `STATE_TRANSITION`, `SIGNATURE_REGISTERED`,
    `DOCUMENT_GENERATED`, `DOCUMENT_DOWNLOADED`, `COLLECTION_UPDATE`, `ATTACHMENT_UPDATE`) y
    `AuditEntry` (`entity: str`, `entity_id: int | None`, `action`, `actor: str`,
    `detail: Mapping[str, Any] | None`, `created_at: datetime`).
  - Nuevo `backend/app/domain/auth/errors.py`: `AccessDeniedError(DomainError)` con mensaje en
    espanol (el mapeo a 403 `forbidden` llega en T-24).

- [ ] T-04 (RF-02, RF-08, RF-09, RF-13, CA-01, CA-04, CA-05, CA-06, CA-08, CA-09, CA-14) Pruebas de
  dominio
  - Nuevo `backend/tests/domain/test_authorization.py`: matriz completa por accion (incluye `ADMIN`
    sin firmas, CA-06/CA-07/CA-08), union de permisos con dos roles (CA-14), `AccessDeniedError` sin
    permiso (CA-04), transiciones por estado destino (CA-05) y firma por rol pedido (CA-06).
  - Nuevo `backend/tests/domain/test_user.py`: bloqueo al 5to intento y reinicio (CA-09),
    autodesactivacion rechazada y `ensure_active` (CA-08).
  - Nuevo `backend/tests/domain/test_session.py`: `SESSION_TTL` de 8 horas e `is_expired` (CA-01).
  - Sin base de datos; export del paquete en `backend/app/domain/auth/__init__.py` (`__all__`).

## Fase B — Puertos, configuracion y adaptadores criptograficos

Commit de fase: `SPEC-008: puertos, configuracion y adaptadores PBKDF2/JWT`

- [ ] T-05 (RF-01, RF-08, RF-09, RF-12, RF-13, RF-18) Puertos nuevos de identidad y auditoria
  - Nuevo `backend/app/application/ports/user_repository.py`: `UserRepository(ABC)` con
    `get_by_username`, `get`, `list_all`, `save` (unicidad de `USERNAME` traducida a
    `UsernameTakenError`, T-15).
  - Nuevo `backend/app/application/ports/password_hasher.py`: `PasswordHasherPort(ABC)` con
    `hash(password)` y `verify(password, encoded)`.
  - Nuevo `backend/app/application/ports/token_service.py`: `TokenServicePort(ABC)` con
    `issue(session) -> str` y `parse(token) -> Session | None`.
  - Nuevo `backend/app/application/ports/audit_repository.py`: `AuditRecorderPort(ABC)` con
    `record(entry: AuditEntry) -> None`.
  - `backend/app/application/ports/auth.py` se conserva como punto de extension (RF-18): firma
    intacta de `Principal`/`AuthProvider`; decision registrada: `Principal.user_id` porta el
    `username` (identidad legible usada como `ACTOR`/`CREATED_BY`). Export en `ports/__init__.py`.

- [ ] T-06 (RF-09, RF-13, RF-16) Configuracion de autenticacion y semilla
  - `backend/app/infrastructure/config.py`: `jwt_ttl_hours: int = 8`, `password_min_length: int = 8`,
    `password_hash_iterations: int`, `login_max_failed_attempts: int = 5` y semilla
    `seed_admin_username: str | None`, `seed_admin_password: SecretStr | None`,
    `seed_admin_nombre: str = "Administrador"` (ademas de las existentes `auth_provider`,
    `jwt_secret`).
  - `.env.example` (raiz): seccion comentada con `SEED_ADMIN_*`, `JWT_TTL_HOURS`,
    `PASSWORD_MIN_LENGTH`, `LOGIN_MAX_FAILED_ATTEMPTS` y aviso explicito de que
    `SEED_ADMIN_PASSWORD` y `JWT_SECRET` son secretos: solo en `.env`, nunca en imagenes ni en git.

- [ ] T-07 (RF-09, RF-15) Adaptador de hashing PBKDF2 (stdlib)
  - Nuevo `backend/app/infrastructure/adapters/password_hasher.py`: `Pbkdf2PasswordHasher` con
    `hashlib.pbkdf2_hmac`, salt de `secrets.token_bytes`, iteraciones de
    `Settings.password_hash_iterations`, verificacion con `hmac.compare_digest` y formato
    auto-descriptivo `pbkdf2_sha256$<iteraciones>$<salt>$<hash>`. **Unico modulo de hashing; lo
    reutiliza la migracion 0004 (T-10).**
  - Nuevo `backend/tests/infrastructure/test_password_hasher.py`: el hash no contiene la clave en
    claro, `verify` positivo/negativo y formato auto-descriptivo (RF-15).

- [ ] T-08 (RF-01, RF-13, RF-15, CA-01, CA-03) Adaptador de token JWT HS256 (stdlib)
  - Nuevo `backend/app/infrastructure/adapters/jwt_token_service.py`: `JwtTokenService(TokenServicePort)`
    con header/payload JSON compacto, Base64URL y firma HMAC-SHA256 sobre `Settings.jwt_secret`;
    rechaza cualquier `alg` distinto de `HS256` (nunca `none`), firmas falsas y `exp` vencido
    (`parse` -> `None`).
  - Nuevo `backend/tests/infrastructure/test_jwt_token_service.py`: round-trip `issue`/`parse`
    (expiracion = `SESSION_TTL`, CA-01), token con firma falsa, con `alg` distinto y con `exp`
    vencido rechazados (CA-03).

## Fase C — Modelo de datos y migracion con semilla ADMIN

Commit de fase: `SPEC-008: tablas SYS_USUARIO/SYS_USUARIO_ROL y migracion 0004 con semilla ADMIN`

- [ ] T-09 (RF-08, RF-12, CA-08) Tablas de usuario y definicion de auditoria en `tables.py` y mappers
  - `backend/app/infrastructure/db/tables.py`: `SYS_USUARIO` (`ID` identity, `USERNAME` unique
    `SYS_USUARIO_USERNAME_UQ`, `NOMBRE`, `PASSWORD_HASH`, `ACTIVO` CHECK `S`/`N`,
    `INTENTOS_FALLIDOS` CHECK `>= 0` default 0, auditoria) y `SYS_USUARIO_ROL` (`ID` identity,
    `USUARIO_ID` FK -> `SYS_USUARIO.ID`, `ROL` CHECK de los 4 roles, auditoria; unico
    `SYS_USUARIO_ROL_UQ` (`USUARIO_ID`,`ROL`) e indice `SYS_USUARIO_ROL_USUARIO_IX`); sin columnas
    `ORDEN`/`ACTIVO` (es un conjunto, no coleccion ordenada). Agregar la definicion de
    `SYS_AUDITORIA` (hoy ausente; su DDL de `0001_base` no cambia).
  - `backend/app/infrastructure/db/mappers.py`: mappers fila <-> `User` (`SYS_USUARIO` +
    `SYS_USUARIO_ROL`) y fila <-> `AuditEntry`.

- [ ] T-10 (RF-10, RF-16, CA-10) Migracion Alembic `0004_usuarios_autenticacion` con semilla
  - Nuevo `backend/alembic/versions/0004_usuarios_autenticacion.py`, `down_revision =
    "0003_documentos_generados"`; `upgrade` crea `SYS_USUARIO` y `SYS_USUARIO_ROL` (columnas, checks,
    FKs, unicos, indices, auditoria) y **siembra el `ADMIN` inicial**: credenciales desde
    `get_settings()` (`SEED_ADMIN_USERNAME`, `SEED_ADMIN_PASSWORD`, `SEED_ADMIN_NOMBRE`); si faltan
    usuario o clave, la migracion falla con error claro en espanol (nunca un default implicito);
    el hash se genera reusando el helper del adaptador `Pbkdf2PasswordHasher` (una sola
    implementacion, T-07) y la insercion usa parametros bound (el secreto nunca via f-string);
    inserta la fila (`ACTIVO='S'`, `INTENTOS_FALLIDOS=0`) y la asignacion `SYS_USUARIO_ROL(ADMIN)`.
  - `downgrade` elimina `SYS_USUARIO_ROL` y `SYS_USUARIO` (no toca `SYS_AUDITORIA`). Patron de
    `0003_documentos_generados.py`.

- [ ] T-11 (RF-10, CA-10) Pruebas de integracion de la migracion y de la semilla
  - `backend/tests/integration/conftest.py`: fixture autouse que hace `os.environ.setdefault` de
    `SEED_ADMIN_USERNAME`/`SEED_ADMIN_PASSWORD` (valores de prueba) antes de `command.upgrade(...)`
    para `migrated_engine` y `test_migration*.py`.
  - Nuevo `backend/tests/integration/test_migration_autenticacion.py` (marcada `integration`,
    Testcontainers Oracle): `upgrade head` crea ambas tablas y el `ADMIN` sembrado autentica con las
    credenciales de entorno (CA-10); `downgrade` elimina ambas tablas; compatible con
    `test_downgrade_drops_sys_auditoria`.

## Fase D — Adaptadores de persistencia e identidad

Commit de fase: `SPEC-008: repositorios de usuario/auditoria y AuthProvider local`

- [ ] T-12 (RF-08, CA-08, CA-09) Repositorio de usuarios Oracle
  - Nuevo `backend/app/infrastructure/adapters/user_repository.py`: `SqlAlchemyUserRepository`
    (SQLAlchemy Core, mismo `Engine`/`sessionmaker`): lee/escribe `SYS_USUARIO` y `SYS_USUARIO_ROL`;
    baja logica con `ACTIVO='N'` (sin `DELETE`); asignaciones de roles reemplazadas por diferencia de
    conjuntos; `IntegrityError` de `USERNAME` traducido a `UsernameTakenError` (mismo patron que
    `DuplicateFolioError`).
  - Nuevo `backend/tests/integration/test_user_repository.py` (marcada `integration`): round-trip
    `User` multi-rol con contador de intentos; unicidad de `USERNAME` -> `UsernameTakenError`
    (CA-08, CA-09).

- [ ] T-13 (RF-12, CA-11) Grabador de auditoria Oracle
  - Nuevo `backend/app/infrastructure/adapters/audit_repository.py`: `SqlAlchemyAuditRecorder`
    inserta en `SYS_AUDITORIA` con `ACTOR` y `CREATED_BY` = actor y `DETALLE` serializado a JSON
    (`json.dumps`, `default=str` para fechas); `ENTIDAD_ID` puede ser `None` (login de usuario
    inexistente).
  - Nuevo `backend/tests/integration/test_audit_repository.py` (marcada `integration`): insercion
    real con `ACTOR` real, `DETALLE` JSON valido que incluye el `motivo` de una transicion y
    recuperacion por `ENTIDAD`/`ENTIDAD_ID` (CA-11).

- [ ] T-14 (RF-01, RF-08, RF-18) Adaptador local detras de `AuthProvider`
  - Nuevo `backend/app/infrastructure/adapters/local_auth_provider.py`:
    `LocalJwtAuthProvider(AuthProvider)`: recibe `token_service`, `user_repository` y el valor de la
    cabecera `Authorization` (lo entrega la dependencia de request, T-27); `current_principal()`
    parsea el token, recarga el usuario de la BD y devuelve `Principal(user_id=username,
    roles=frozenset(...))` solo si esta activo; `None` en cualquier fallo (sin token, token invalido,
    expirado o usuario inactivo) -> 401 en la dependencia.
  - Segun `Settings.auth_provider`: `local_jwt` -> este adaptador; `oidc` -> error de configuracion
    claro ("proveedor no disponible en esta fase", fase posterior de ADR-003, RF-18).

## Fase E — Casos de uso de autenticacion y usuarios (application)

Commit de fase: `SPEC-008: casos de uso de autenticacion y gestion de usuarios`

- [ ] T-15 (CA-02, CA-03, CA-04, CA-08, CA-09) Errores nuevos de aplicacion
  - `backend/app/application/errors.py` (misma familia `ApplicationError`): `NotAuthenticatedError`
    (401 `unauthenticated`), `InvalidCredentialsError` (401 `invalid_credentials`, mensaje unico que
    no revela existencia, CA-02), `AccountLockedError` (401 `account_locked`), `UserNotFoundError`
    (404 `user_not_found`), `UsernameTakenError` (409 `username_taken`) y `SelfDeactivationError`
    (409 `self_deactivation_not_allowed`). El mapeo HTTP llega en T-24.

- [ ] T-16 (RF-01, RF-09, CA-01, CA-02, CA-09) Caso de uso `AuthenticateUser`
  - Nuevo `backend/app/application/use_cases/auth/login.py`: `AuthenticateUser(user_repository,
    password_hasher, token_service, audit, *, session_ttl)`; `execute(usuario, contrasena)`:
    usuario inexistente o clave mala -> audit `LOGIN_FAILED` + `InvalidCredentialsError` (mensaje
    unico, CA-02) incrementando y persistiendo el contador (RF-09); bloqueado (`>= 5`) ->
    audit `LOGIN_BLOCKED` + `AccountLockedError` (CA-09); inactivo -> `InvalidCredentialsError` sin
    revelar; exito -> reinicia el contador, audit `LOGIN_SUCCESS` y emite token de 8h con los roles
    actuales (CA-01). Export en `use_cases/auth/__init__.py`.

- [ ] T-17 (RF-12, RF-14, CA-11) Casos de uso `LogoutUser` y `GetSession`
  - Nuevo `backend/app/application/use_cases/auth/logout.py`: `LogoutUser(audit)`;
    `execute(principal)` registra `LOGOUT` (la invalidacion es por expiracion, stateless).
  - Nuevo `backend/app/application/use_cases/auth/get_session.py`: `GetSession(user_repository)`;
    `execute(principal)` devuelve perfil y roles desde la BD (mecanismo de arranque del frontend
    para RF-14).
  - Pruebas en `backend/tests/application/` con fakes (ver T-23).

- [ ] T-18 (RF-08, RF-09, CA-08, CA-09) Casos de uso de gestion de usuarios
  - Nuevo `backend/app/application/use_cases/users/create_user.py`: `CreateUser(user_repository,
    password_hasher, audit)`; `execute(principal, ...)`: usuario duplicado -> `UsernameTakenError`;
    hash de la contrasena; audit `USER_CREATE` (RF-08, CA-08).
  - Nuevo `backend/app/application/use_cases/users/update_user.py`: `UpdateUser(...)`; 404 si no
    existe; desactivar a si mismo -> `SelfDeactivationError` (CA-08); cambiar contrasena -> hash;
    **siempre reinicia `INTENTOS_FALLIDOS`** (reinicio manual por edicion, CA-09); audit
    `USER_UPDATE` con detalle de campos cambiados (nunca la contrasena).
  - Nuevo `backend/app/application/use_cases/users/list_users.py`: `ListUsers(user_repository)` para
    la pantalla ADMIN (sin auditoria: RF-12 solo lista alta/baja/edicion).
  - Nuevo `backend/tests/application/test_authenticate_user.py` (fakes de repositorio/hash/token/
    auditoria): exito con roles y token de 8h (CA-01); credenciales malas/inexistentes con mensaje
    unico que no revela existencia e incremento de intentos (CA-02); bloqueo al 5to con
    `LOGIN_BLOCKED` (CA-09); inactivo rechazado; exito reinicia el contador.
  - Nuevo `backend/tests/application/test_manage_users.py`: alta con roles y audit `USER_CREATE`
    (CA-08); edicion reinicia intentos (CA-09); autodesactivacion rechazada; username duplicado.

## Fase F — Actor real y auditoria en los flujos existentes

Commit de fase: `SPEC-008: actor real y auditoria en los flujos existentes`

- [ ] T-19 (RF-11, RF-12, CA-11) Kwarg `principal`/`actor` en repositorios y casos de uso de
  requerimiento y versiones
  - `backend/app/application/ports/requirement_repository.py` y
    `backend/app/infrastructure/adapters/requirement_repository.py` (y
    `requirement_document_repository.py`): `save(..., *, actor: str)` para
    `CREATED_BY`/`UPDATED_BY` (los catalogos y datos historicos conservan `SYSTEM`); los adaptadores
    dejan de usar `SYSTEM_ACTOR` en flujos autenticados (RF-11).
  - `backend/app/application/use_cases/requirement/`: `CreateRequirement`, `UpdateVersion`,
    `FreezeAndAdvance`, `Add/Update/Delete/ReorderCollectionItem` y
    `Add/Update/Delete/ReorderAttachment` ganan `execute(..., principal: Principal)` y reenvian el
    actor (precedente: kwarg `actor` de SPEC-007); registra auditoria `REQUIREMENT_CREATE`,
    `VERSION_UPDATE`, `VERSION_FREEZE`, `COLLECTION_UPDATE` y `ATTACHMENT_UPDATE` a nivel
    `REQ_VERSION` (RF-12).
  - Actualizar los tests existentes de `tests/application/` afectados por las firmas nuevas.

- [ ] T-20 (RF-05, RF-12, RF-17, CA-05, CA-11) `TransitionRequirementState` sin `actor_id` y con
  motivo auditado
  - `backend/app/application/use_cases/requirement/transition_requirement_state.py`: **elimina
    `actor_id`**; `execute(..., principal, a_estado, motivo)`; primero
    `ensure_transition_allowed(principal.roles, target)` (403 sin persistir ni validar, antes de
    cargar el requerimiento, CA-05), luego la maquina de estados/validacion integra existente (400)
    y, en exito, `save(..., actor)` + audit `STATE_TRANSITION` con
    `detail={"estado_anterior", "estado_actual", "motivo"}` (CA-11).
  - Actualizar `backend/tests/application/test_transition_requirement_state.py`: 403 de rol sin
    cambios de estado; exito con actor real y `motivo` auditado.

- [ ] T-21 (RF-06, CA-06) `RegisterSignature` con control de rol sin cambiar ADR-007
  - `backend/app/application/use_cases/requirement/register_signature.py`:
    `ensure_signature_allowed(principal.roles, payload.rol)` antes de `ensure_signable` (403 si el
    rol no corresponde o si es `ADMIN`; la politica ADR-007 no cambia); `save(..., actor)` y audit
    `SIGNATURE_REGISTERED`.
  - Pruebas: rol correspondiente persiste; rol ajeno y `ADMIN` -> 403 sin persistir (CA-06).

- [ ] T-22 (RF-07, RF-11, RF-12, CA-11) Documentos generados con actor real y auditoria
  - `backend/app/application/use_cases/requirement/generate_documents.py`: el kwarg `actor` deja de
    tener default `SYSTEM_ACTOR` (recibe el `principal`); `save(..., actor)` para `GENERADO_BY` y
    audit `DOCUMENT_GENERATED`.
  - `backend/app/application/use_cases/requirement/get_document.py` (descarga): audit
    `DOCUMENT_DOWNLOADED` con el usuario autenticado.
  - Actualizar `backend/tests/application/test_generate_documents.py` y
    `test_document_queries.py` (firmas con `principal`; aserciones `SYSTEM` -> usuario de prueba).

- [ ] T-23 (RF-12, CA-11, CA-15) Pruebas de auditoria de casos de uso
  - Nuevo `backend/tests/application/test_auth_audit.py` (fakes): `LogoutUser` y las acciones de
    negocio registran `AuditEntry` con entidad/accion/actor/detalle correctos (transicion con
    `motivo`, CA-11); todo funciona sin ningun servicio de IA (`AI_PROVIDER=none`, CA-15).

## Fase G — API: enforcement por roles, routers y esquemas

Commit de fase: `SPEC-008: enforcement por roles y endpoints auth/usuarios`

- [ ] T-24 (CA-02, CA-03, CA-04, CA-08) Mapeo de los errores nuevos al envelope existente
  - `backend/app/api/errors.py`: mapear `NotAuthenticatedError`/`InvalidCredentialsError`/
    `AccountLockedError` a **401** (`unauthenticated`/`invalid_credentials`/`account_locked`),
    `AccessDeniedError` (dominio, via `_map_domain`) a **403** `forbidden`, `UserNotFoundError` a
    404 y `UsernameTakenError`/`SelfDeactivationError` a **409**, todos en el envelope existente
    `{"error": {"code", "message", "details"}}` con mensaje en espanol.
  - `401`/`403` no ejecutan la operacion ni dejan efectos parciales; `/transicionar` conserva su
    `400` especial (no envelope) para fallos de validacion, pero su `403` de rol si usa el envelope
    (CA-05).

- [ ] T-25 (RF-17, CA-11) Esquemas de autenticacion, usuarios y cambio de `/transicionar`
  - Nuevo `backend/app/api/schemas/auth.py`: `LoginRequest(usuario, contrasena)`, `LoginResponse`,
    `SesionResponse`; nuevo `backend/app/api/schemas/user.py`: `UsuarioCreate` (contrasena
    `min_length=8` -> 422 en forma, decision del plan), `UsuarioUpdate` (todo opcional) y
    `UsuarioResponse(id, usuario, nombre, roles, activo, intentos_fallidos)`. Re-export en
    `schemas/__init__.py`.
  - `backend/app/api/schemas/validation.py`: `StateTransitionRequest` pasa a `{ a_estado, motivo? }`
    y **elimina `actor_id`** (RF-17; un consumidor que aun lo envie no recibe 422: Pydantic ignora
    campos extra).

- [ ] T-26 (RF-01, RF-08, RF-14, CA-01, CA-08) Routers `auth.py` y `users.py`
  - Nuevo `backend/app/api/routers/auth.py` (`prefix="/api/v1"`, tag `autenticacion`, sin logica de
    negocio): `POST /auth/login` (**publica**, 200 `LoginResponse`), `POST /auth/logout` (204, audit
    `LOGOUT`) y `GET /auth/sesion` (200 `SesionResponse`, decision propia del plan para RF-14).
  - Nuevo `backend/app/api/routers/users.py` (`prefix="/api/v1"`, tag `usuarios`) con
    `dependencies=[Depends(require_action(Action.MANAGE_USERS))]` a nivel de router (solo ADMIN):
    `GET /usuarios` (listado con `intentos_fallidos`), `GET /usuarios/{id}` (200/404), `POST
    /usuarios` (201) y `PATCH /usuarios/{id}` (200).
  - `backend/app/main.py` y `backend/app/api/routers/__init__.py`: registrar ambos routers;
    factorias de los casos de uso en `dependencies.py` (patron existente).

- [ ] T-27 (RF-03, RF-04, CA-03, CA-04, CA-13, CA-14) Enforcement por dependencias sobre TODOS los
  endpoints de `/api/v1`
  - `backend/app/api/dependencies.py`: `get_auth_provider(request)` (instancia `LocalJwtAuthProvider`
    segun `Settings.auth_provider`, T-14), `get_current_principal(auth) -> Principal` (lanza
    `NotAuthenticatedError` si es `None`) y `require_action(action: Action) -> Principal` (aplica
    `ensure_authorized`, 403); factorias `get_token_service`, `get_password_hasher`,
    `get_user_repository`, `get_audit_recorder` y de los casos de uso nuevos.
  - Declarar `dependencies=[Depends(get_current_principal)]` en **todos** los routers bajo
    `/api/v1` (lectura y escritura) y `Depends(require_action(...))` por endpoint segun la matriz
    del plan (crear/editar version `E,AD`; documentos `A,AD`; descarga y lectura `todos`;
    `/usuarios` `AD` via router; etc.); `/health` y `/version` permanecen publicos (CA-13).
  - Las factorias de casos de uso existentes que escriben pasan a recibir
    `Annotated[Principal, Depends(get_current_principal)]` y lo reenvian al `execute(...)`.
  - Orden de enforcement: 401 -> 403 -> reglas de negocio (400/404/409); las tres filas dinamicas
    (transicion, firma, autodesactivacion) quedan en los casos de uso (T-18, T-20, T-21).

- [ ] T-28 (RF-01, RF-08, RF-14, CA-01, CA-02, CA-08, CA-09) Pruebas de API de login, sesion y
  usuarios
  - Nuevo `backend/tests/api/conftest.py`: fixture `client` + `client_as(*roles)` que sobreescribe
    `get_current_principal` con un `Principal` de prueba; las pruebas existentes que no miden auth
    usan por defecto un principal con todos los roles.
  - Nuevo `backend/tests/api/test_auth.py`: login 200 (CA-01), 401 `invalid_credentials` y
    `account_locked` (CA-02, CA-09), 422 por forma; logout 204; `GET /auth/sesion` (RF-14).
  - Nuevo `backend/tests/api/test_users.py`: CRUD bajo ADMIN (201/200), 403 para cualquier otro rol
    (CA-08), autodesactivacion 409 (CA-08), reinicio de intentos por PATCH (CA-09), 404 y 409
    `username_taken`.

- [ ] T-29 (RF-03, RF-04, RF-05, RF-06, RF-07, RF-11, CA-03, CA-04, CA-05, CA-06, CA-07, CA-11,
  CA-13, CA-14) Pruebas de enforcement y adaptacion de las pruebas existentes
  - Nuevo `backend/tests/api/test_auth_enforcement.py`: **401 con envelope** en endpoints de lectura
    y escritura sin token, con token invalido y con token expirado (CA-03); **403 con envelope y sin
    cambios persistidos** con rol insuficiente en escritura, transicion, firma y generacion (CA-04,
    CA-05, CA-06, CA-07); `/health` y `/version` 200 sin token (CA-13); union de dos roles (CA-14).
  - `backend/tests/api/test_transition.py` (adaptado): sin `actor_id`; 403 de rol con estado
    inalterado; exito con `motivo` auditado y `UPDATED_BY` = usuario de prueba (CA-11).
  - Ajuste de pruebas existentes (`tests/api/test_documents.py`, etc.): aserciones `SYSTEM` ->
    usuario de prueba via `client_as(...)`; firmas de casos de uso con `principal` (CA-11).

## Fase H — Documentacion del contrato

Commit de fase: `SPEC-008: documentar autenticacion, autorizacion y auditoria en api.md`

- [ ] T-30 (RF-03, RF-04, RF-08, RF-17, CA-11) Actualizar `doc/technical/api.md`
  - Nueva seccion `### Autenticacion y usuarios (SPEC-008)` con `/auth/login`, `/auth/logout`,
    `/auth/sesion` y `/usuarios` (metodos, exitos, errores 401/403/404/409 del envelope y esquemas
    `LoginRequest`/`LoginResponse`/`SesionResponse`/`UsuarioResponse`).
  - Autorizacion por endpoint (matriz del plan) y fila 401/403 en la tabla de codigos; cuerpo
    actualizado de `/transicionar` (sin `actor_id`; `motivo` persistido en `SYS_AUDITORIA.DETALLE`)
    con nota del cambio de contrato frente a SPEC-005; nota de que el actor real sustituye a
    `SYSTEM` en `CREATED_BY`/`UPDATED_BY`/`GENERADO_BY`.

## Fase I — Frontend: sesion, overlay de login y gestion de usuarios

Commit de fase: `SPEC-008: frontend de sesion, overlay de login y gestion de usuarios`

- [ ] T-31 (RF-14, CA-12) Cliente API con Bearer y manejo de 401/403
  - Nuevo `frontend/src/api/token.ts`: almacenamiento del token en `localStorage`
    (`get/set/clear`); sin refresh (la expiracion la resuelve el backend con 401).
  - `frontend/src/api/client.ts`: `send()` agrega `Authorization: Bearer <token>` cuando existe; ante
    `401` (envelope `unauthenticated`/`invalid_credentials`) emite un evento de sesion vencida (lo
    consume `AuthContext`, T-32) y lanza `ApiError` como hoy; `403` (`forbidden`) lanza `ApiError`
    con ese `code`. Contrato de `request<T>()`/`requestBlob()` sin cambios.
  - Nuevo `frontend/src/api/auth.ts` (`login`, `logout`, `session`) y
    `frontend/src/api/users.ts` (`listUsers`, `getUser`, `createUser`, `updateUser`); tipos
    `LoginResponse`, `Usuario`, `UsuarioPayload` en `api/types.ts` y export en `api/index.ts`.

- [ ] T-32 (RF-13, RF-14, CA-12) Contexto de sesion y overlay de login que conserva la vista
  - Nuevo `frontend/src/auth/AuthContext.tsx` + `useAuth()`: estado
    `checking | anonymous | authenticated` con `{usuario, nombre, roles}`; al arrancar, si hay token
    -> `GET /auth/sesion` (401 -> limpia y `anonymous`); `login()` guarda token y perfil; `logout()`
    limpia.
  - Nuevo `frontend/src/auth/LoginOverlay.tsx`: overlay a pantalla completa con usuario/contrasena y
    mensaje de error legible (`invalid_credentials`/`account_locked`).
  - `frontend/src/App.tsx`: montar `AuthProvider` y renderizar `LoginOverlay` **encima** del arbol
    sin desmontar `NavContext` ni la vista actual: la navegacion en estado se conserva (RF-13,
    CA-12).

- [ ] T-33 (RF-08, RF-14, CA-08, CA-09) Pantalla de gestion de usuarios y visibilidad ADMIN
  - Nuevo `frontend/src/features/users/UsersPage.tsx`: tabla (usuario, nombre, roles, activo,
    intentos/fallo de bloqueo) + formularios de alta y edicion con los componentes `ui` existentes
    (`Input`, `Select`, `Button`, `Badge`); exito/error con el envelope; la edicion muestra el aviso
    "reinicia los intentos de acceso" (CA-09) y la desactivacion del propio usuario aparece
    deshabilitada con el motivo (el backend tambien la rechaza, CA-08).
  - Nuevo `frontend/src/features/users/useUsers.ts`: hook patron `{ data, loading, error, reload }`
    de `useRequirementsList`.
  - `frontend/src/navigation/NavContext.tsx` y `frontend/src/components/layout/Sidebar.tsx`: nuevo
    `AppView { name: "users" }`/`SidebarKey`; el elemento "Gestion de usuarios" solo se renderiza si
    `roles` incluye `ADMIN` (el backend rechaza igual con 403).

- [ ] T-34 (RF-14, CA-12) Re-autenticacion sin perder trabajo y acciones condicionadas a roles
  - Tras re-autenticarse desde el overlay: reintenta el `flush()` pendiente de
    `frontend/src/hooks/useAutosave.ts` (el borrador en memoria apunta a la misma version) y la
    vista se refresca desde la BD; el borrador persistido no depende de la sesion (CA-12).
  - `401` en cualquier peticion -> overlay; `403` -> mensaje de acceso denegado en la operacion sin
    navegar fuera ni perder el wizard (RF-14).
  - `frontend/src/features/wizard/DocumentActions.tsx`: acciones de la matriz visibles condicionadas
    a roles (p. ej. "Generar DOCX/PDF" solo con AUTORIZO/ADMIN); el servidor es quien enforce.

- [ ] T-35 (RF-14, CA-08, CA-12) e2e de autenticacion (Playwright)
  - `frontend/e2e/support/backend.ts`: mocks nuevos de `POST /auth/login`, `GET /auth/sesion`,
    `POST /auth/logout` y de `/usuarios`; los mocks existentes de `/api/v1` deben responder con
    envelope `unauthenticated` cuando el test lo simule.
  - Nuevo `frontend/e2e/auth.spec.ts`: sin sesion -> overlay y navegacion conservada; 401 simulado ->
    overlay -> login -> la vista vuelve a cargar desde el backend mock con el borrador persistido
    (CA-12); 403 -> mensaje de acceso denegado; pantalla de usuarios visible solo para ADMIN (CA-08).
  - `frontend/e2e/wizard.spec.ts` y `frontend/e2e/layout.spec.ts` adaptados: seed del token/sesion
    mock al inicio.

## Fase J — Verificacion final

Commit de fase: `SPEC-008: verificacion final (calidad, integracion y e2e)`

- [ ] T-36 (RF-10, RF-11, RF-12, CA-10, CA-11) Integracion completa con Docker + Testcontainers
  - Desde `backend/` (ver `AGENTS.md`): `python -m pytest -m integration tests/integration` en
    verde: migracion `0004` + semilla `ADMIN` autenticable (T-11), repositorio de usuarios (T-12),
    repositorio de auditoria con `motivo` en `DETALLE` (T-13) y las pruebas de migracion existentes
    con el fixture autouse.

- [ ] T-37 (RF-15, CA-15, CA-16) Lint, tipos y unitarias backend
  - Desde `backend/`: `ruff check .`, `mypy --strict app` y `python -m pytest` en verde; la app y
    las pruebas de auth corren con `AI_PROVIDER=none` (CA-15); `GET /openapi.json` expone los
    endpoints nuevos con las columnas 401/403.

- [ ] T-38 (CA-16) Build frontend y e2e
  - Desde `frontend/`: `npm run build` (`tsc -b` + vite) y `npm run test:e2e` en verde (suite
    adaptada + `auth.spec.ts`).

- [ ] T-39 (RF-15, RF-16, RF-18, CA-15) Verificacion de alcance y evidencia para `verify.md`
  - Confirmar: `backend/pyproject.toml` y `frontend/package.json` **sin dependencias nuevas**
    (JWT/hashing con stdlib, RF-15); `docker-compose.yml` sin cambios de servicios (las variables
    nuevas fluyen por `env_file: .env`) y sin secretos en imagenes (RF-16); `ports/auth.py` sin
    cambios de firma y el dominio sin imports de JWT/OIDC (RF-18, sustituible por OIDC sin tocarlo);
    la aplicacion opera con `AI_PROVIDER=none` (CA-15). Recopilar evidencia en
    `specs/SPEC-008-autenticacion-roles/verify.md`.

## Trazabilidad CA → Tareas

| CA | Tareas |
|---|---|
| CA-01 | T-02, T-04, T-08, T-16, T-28 |
| CA-02 | T-15, T-16, T-24, T-28 |
| CA-03 | T-08, T-15, T-27, T-29 |
| CA-04 | T-01, T-04, T-15, T-24, T-27, T-29 |
| CA-05 | T-01, T-04, T-20, T-29 |
| CA-06 | T-01, T-04, T-21, T-29 |
| CA-07 | T-01, T-27, T-29 |
| CA-08 | T-01, T-02, T-04, T-12, T-15, T-18, T-24, T-26, T-28, T-33, T-35 |
| CA-09 | T-02, T-04, T-12, T-16, T-18, T-28, T-33 |
| CA-10 | T-09, T-10, T-11, T-36 |
| CA-11 | T-03, T-13, T-19, T-20, T-22, T-23, T-29, T-30, T-36 |
| CA-12 | T-31, T-32, T-34, T-35 |
| CA-13 | T-27, T-29 |
| CA-14 | T-01, T-04, T-27, T-29 |
| CA-15 | T-23, T-37, T-39 |
| CA-16 | T-37, T-38 |
