# Plan tecnico - SPEC-008-autenticacion-roles

## Enfoque

La spec se traduce a la arquitectura hexagonal (ADR-002) en cinco frentes, en este orden:

1. **Modelo y migracion**: tablas `SYS_USUARIO` y `SYS_USUARIO_ROL`, alta de `SYS_AUDITORIA` en
   `tables.py` (ya creada por `0001_base`) y migracion `0004` encadenada desde `0003_documentos_generados`
   que ademas siembra el `ADMIN` inicial (RF-10, RF-12, CA-10).
2. **Dominio y aplicacion**: entidades y reglas puras de autenticacion/autorizacion/auditoria, puertos
   (`UserRepository`, `PasswordHasherPort`, `TokenServicePort`, `AuditRecorderPort`, `AuthProvider`) y
   casos de uso (login, logout, sesion, CRUD de usuarios) (RF-01, RF-02, RF-08, RF-09, RF-18).
3. **Enforcement**: identidad y autorizacion por dependencias FastAPI sobre la matriz de la spec, con los
   chequeos dinamicos (transicion, firma, autodesactivacion) en casos de uso (RF-03, RF-04, RF-05, RF-06,
   RF-07).
4. **API y contrato**: routers `/auth` y `/usuarios`, mapeo de la matriz a TODOS los endpoints de
   `/api/v1`, cambio de contrato de `/transicionar` y errores 401/403 en el envelope existente
   (RF-17, CA-03, CA-04).
5. **Frontend**: login como overlay, gestion de usuarios, adjuntar token, manejo de 401/403 y
   conservacion del borrador persistido (RF-13, RF-14, CA-12).

Decisiones de diseno:

- **Autenticacion local JWT tras `AuthProvider` (ADR-003)**: token HS256 de 8 horas sin refresh
  (decision 7). El token transporta **solo identidad** (`sub` = usuario, `roles`, `iat`, `exp`), nunca
  datos de negocio; en cada peticion el adaptador verifica firma y expiracion y **recarga el usuario
  desde `SYS_USUARIO`** para confirmar que sigue activo y tomar sus roles actuales: la BD es la fuente
  de verdad (los `roles` del token son informativos y no se confian) y un usuario desactivado deja de
  operar con su siguiente peticion (RF-08, RF-13, decision 7).
- **Sin dependencias nuevas (RF-15)**: JWT con stdlib (`hmac`, `hashlib.sha256`, `base64`, `json`) y
  contrasenas con `hashlib.pbkdf2_hmac` (PBKDF2-HMAC-SHA256, salt aleatorio, formato
  `pbkdf2_sha256$<iteraciones>$<salt>$<hash>`, verificacion con `hmac.compare_digest`). Justificacion:
  solo se necesita HS256 y un KDF de clave unica; PyJWT/passlib/bcrypt serian dependencias nuevas sin
  ventaja funcional para el MVP y bcrypt requiere binarios C (regla 6 de `AGENTS.md`).
- **Matriz en dominio puro, enforcement en dependencias**: `domain/auth/authorization.py` codifica la
  matriz aprobada como datos puros (`Action`, `required_roles`, `ensure_*`). FastAPI solo aplica:
  `get_current_principal` (401, a nivel de router en todo `/api/v1`) y `require_action(Action.X)` (403,
  por endpoint para la matriz estatica). Los chequeos que dependen del cuerpo o del estado actual
  (transicion por estado destino, firma por `rol` del cuerpo, no autodesactivacion) se ejecutan en el
  caso de uso antes de persistir (RF-04, RF-05, RF-06; NFR "las reglas de autorizacion viven en
  dominio/aplicacion").
- **Identidad explicita**: los casos de uso que escriben reciben `principal: Principal` como argumento
  keyword de `execute(...)` (precedente: el kwarg `actor` que SPEC-007 ya dejo en
  `GenerateRequirementDocuments`); el router reenvia la identidad resuelta por la dependencia. Se
  descarta el actor ambiental (`ContextVar`) por fragilidad con los endpoints sincronos de FastAPI
  (corren en threadpool con contexto copiado) y por opacidad. Los adaptadores dejan de usar
  `SYSTEM_ACTOR` en flujos autenticados (RF-11, CA-11).
- **Auditoria por puerto**: los casos de uso relevantes inyectan `AuditRecorderPort` y registran la
  accion con `ACTOR` real; el adaptador escribe en `SYS_AUDITORIA` con `DETALLE` JSON (incluido el
  `motivo` de la transicion) (RF-12, CA-11). Solo escritura desde el flujo normal (sin consulta/purgado).
- **`/transicionar` sin `actor_id`**: el campo se elimina del body; el actor es siempre la identidad
  autenticada y el `motivo` se persiste en `SYS_AUDITORIA.DETALLE` (RF-17, decision 8).
- **Bootstrap**: la semilla del `ADMIN` vive en la migracion `0004` y lee credenciales de `Settings`
  (variables de entorno), con fallo explicito si faltan (RF-10, RF-16, CA-10, decision 5).
- **Frontend**: `AuthContext` + overlay de login que no desmonta la vista actual (la ruta/navegacion en
  estado se conserva), cliente API con cabecera `Authorization: Bearer` y manejo de 401/403; pantallas
  disenadas aqui con los tokens institucionales de `src/index.css` (no hay Stitch para login/gestion,
  decision 11).

| Frente | RF/CA principales |
|---|---|
| Token/identidad + `AuthProvider` | RF-01, RF-13, RF-18, CA-01, CA-12 |
| Enforcement y matriz | RF-02..RF-07, CA-03..CA-07, CA-14 |
| Usuarios y bloqueo | RF-08, RF-09, CA-08, CA-09 |
| Semilla `ADMIN` | RF-10, RF-16, CA-10 |
| Actor real + auditoria | RF-11, RF-12, RF-17, CA-11 |
| Frontend | RF-13, RF-14, CA-12 |
| Sin IA / calidad | RF-15, CA-15, CA-16 |

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic

Nuevas tablas en `backend/app/infrastructure/db/tables.py` (SQLAlchemy Core, mismo `MetaData`,
patron de `0002_modelo_requerimiento.py`):

`SYS_USUARIO`:

| Columna | Tipo | Notas |
|---|---|---|
| `ID` | `Numeric(19,0)` PK | `NUMBER GENERATED ALWAYS AS IDENTITY` (helper `_ID`) |
| `USERNAME` | `String(50)` NOT NULL | login unico; unico `SYS_USUARIO_USERNAME_UQ` |
| `NOMBRE` | `String(150)` NOT NULL | nombre visible |
| `PASSWORD_HASH` | `String(200)` NOT NULL | salida de PBKDF2 (nunca claro) |
| `ACTIVO` | `CHAR(1)` NOT NULL | CHECK `IN ('S','N')` |
| `INTENTOS_FALLIDOS` | `Numeric(3,0)` NOT NULL | default `0`; CHECK `>= 0` |
| `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY` | audit | helper `_audit_columns()` |

`SYS_USUARIO_ROL` (conjunto de roles asignados; multi-rol, decision 2):

| Columna | Tipo | Notas |
|---|---|---|
| `ID` | `Numeric(19,0)` PK | identity (consistente con el resto del esquema) |
| `USUARIO_ID` | `Numeric(19,0)` NOT NULL FK | → `SYS_USUARIO.ID` |
| `ROL` | `String(20)` NOT NULL | CHECK `IN ('ELABORO','REVISO','AUTORIZO','ADMIN')` |
| `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY` | audit | helper `_audit_columns()` |

- Claves/indices: `SYS_USUARIO_USERNAME_UQ` (`USERNAME`),
  `SYS_USUARIO_ROL_UQ` (`USUARIO_ID`, `ROL`), `SYS_USUARIO_ROL_USUARIO_IX` (`USUARIO_ID`).
- Sin columnas `ORDEN`/`ACTIVO`: los roles no son una coleccion ordenada sino un conjunto con
  unicidad por usuario+rol (convenciones.md solo aplica `ORDEN`/`ACTIVO` a colecciones ordenadas).
- No existe tabla `SYS_ROL`: el catalogo de roles es fijo en codigo (dominio), como la matriz
  (decision 1). No hay columna de "bloqueo hasta": el bloqueo es el contador `INTENTOS_FALLIDOS >= 5`
  y el reinicio es manual por `ADMIN` (RF-09); no se crea una tabla de intentos de login porque cada
  intento fallido/bloqueado queda ademas auditado en `SYS_AUDITORIA` (decision propia, la opcion mas
  simple coherente con "contador de intentos fallidos" de la spec).
- `SYS_AUDITORIA` **no cambia** (creada en `0001_base` con `ENTIDAD`, `ENTIDAD_ID`, `ACCION`,
  `ACTOR`, `DETALLE IS JSON`, auditoria e indice `SYS_AUDITORIA_ENTIDAD_IX`); solo se agrega su
  definicion de tabla a `tables.py` (hoy ausente) para poder insertar desde SQLAlchemy Core.

Migracion nueva `backend/alembic/versions/0004_usuarios_autenticacion.py`:

- `revision = "0004_usuarios_autenticacion"`, `down_revision = "0003_documentos_generados"`;
  `target_metadata` sigue en `None` (mismo patron que las anteriores). DDL solo via Alembic.
- `upgrade`: crea `SYS_USUARIO` y `SYS_USUARIO_ROL` (columnas, checks, FKs, unicos, indices,
  auditoria) y **siembra el `ADMIN` inicial** (RF-10):
  - Credenciales desde `get_settings()` (`SEED_ADMIN_USERNAME`, `SEED_ADMIN_PASSWORD`,
    `SEED_ADMIN_NOMBRE`): si `SEED_ADMIN_USERNAME` o `SEED_ADMIN_PASSWORD` estan vacios, la
    migracion falla con error claro en espanol (la aplicacion nunca debe quedar sin medio de acceso
    inicial ni con un secreto por defecto implicito) (RF-10, RF-16, CA-10, decision 5).
  - El hash se genera reusando el mismo helper del adaptador de hashing (una sola implementacion);
    la insercion usa parametros bound (el secreto nunca via f-string).
  - Inserta la fila `SYS_USUARIO` (`ACTIVO='S'`, `INTENTOS_FALLIDOS=0`) y la asignacion
    `SYS_USUARIO_ROL(ADMIN)`.
- `downgrade`: elimina `SYS_USUARIO_ROL` y `SYS_USUARIO` (la semilla cae con su tabla); no toca
  `SYS_AUDITORIA` mas alla del orden inverso (compatible con `test_downgrade_drops_sys_auditoria`).
- La semilla se ejecuta en el mismo `alembic upgrade head` que el resto del esquema (no hay script
  manual ni logica de arranque, decision 5). La spec habla de "migracion base"; se resuelve
  encadenando desde `0003` para no reescribir el historial de revisiones (decision propia).

## Dominio y casos de uso

### Dominio (puro) - `backend/app/domain/auth/` (nuevo paquete)

Sin imports de FastAPI, SQLAlchemy, JWT ni librerias de hashing:

- `roles.py` - `Role(StrEnum)`: `ELABORO`, `REVISO`, `AUTORIZO`, `ADMIN` (RF-02, ADR-003).
- `authorization.py` - matriz de la spec como datos puros:
  - `Action(StrEnum)`: `READ`, `REQUIREMENT_WRITE`, `GENERATE_DOCUMENTS`, `DOWNLOAD_DOCUMENTS`,
    `MANAGE_USERS`.
  - `REQUIRED_ROLES: dict[Action, frozenset[Role]]` copiando la matriz aprobada (`ADMIN` explicito en
    cada accion salvo firmas; sin herencia implicita) (RF-04).
  - `required_roles(action)`, `ensure_authorized(roles, action)` (RF-04, RF-14 union de permisos,
    CA-14).
  - `ensure_transition_allowed(roles, target_status)` -> filas de transicion de la matriz
    (`EN_REVISION`->ELABORO; `VALIDADO`->REVISO; `APROBADO`/`GENERADO`/`CANCELADO`->AUTORIZO; todos
    con `ADMIN`) (RF-05, CA-05).
  - `ensure_signature_allowed(roles, requested_role)` -> ELABORO/REVISO/AUTORIZO solo la suya y
    `ADMIN` nunca (RF-06, CA-06). Importa `domain/requirement/enums` (mismo dominio).
- `errors.py` - `AccessDeniedError(DomainError)` con mensaje en espanol; se mapea a **403
  `forbidden`** en `api/errors.py`.
- `user.py` - `@dataclass(frozen=True, slots=True)` `User`: `id: int | None`, `username: str`,
  `name: str`, `password_hash: str`, `roles: frozenset[Role]`, `active: bool`,
  `failed_attempts: int`, con reglas puras: `is_locked(max_attempts)`, `record_failed_attempt()`
  (devuelve `User` actualizado, inmutabilidad tipo `replace`), `reset_failed_attempts()`,
  `ensure_can_be_deactivated_by(actor_username)` (no autodesactivacion, RF-08/decision 4) y
  `ensure_active()` (RF-08). La verificacion de contrasena NO vive aqui (necesita el puerto de
  hashing).
- `session.py` - `Session(user_id, roles, issued_at, expires_at)` con `SESSION_TTL = timedelta(hours=8)`
  y `is_expired(now)` puro; el serializado JWT va en infraestructura (RF-13, decision 7).
- `audit.py` - `AuditAction(StrEnum)` (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGIN_BLOCKED`, `LOGOUT`,
  `USER_CREATE`, `USER_UPDATE`, `REQUIREMENT_CREATE`, `VERSION_UPDATE`, `VERSION_FREEZE`,
  `STATE_TRANSITION`, `SIGNATURE_REGISTERED`, `DOCUMENT_GENERATED`, `DOCUMENT_DOWNLOADED`,
  `COLLECTION_UPDATE`, `ATTACHMENT_UPDATE`) y `AuditEntry` (`entity: str`, `entity_id: int | None`,
  `action: AuditAction`, `actor: str`, `detail: Mapping[str, Any] | None`, `created_at: datetime`)
  (RF-12).

### Aplicacion

**Errores nuevos** (`backend/app/application/errors.py`, misma familia `ApplicationError`):

| Error | HTTP | `code` |
|---|---|---|
| `NotAuthenticatedError` | 401 | `unauthenticated` |
| `InvalidCredentialsError` | 401 | `invalid_credentials` (mensaje unico: no revela existencia, CA-02) |
| `AccountLockedError` | 401 | `account_locked` (mensaje claro de bloqueo, RF-09/CA-09; ver decision en Riesgos) |
| `UserNotFoundError` | 404 | `user_not_found` |
| `UsernameTakenError` | 409 | `username_taken` |
| `SelfDeactivationError` | 409 | `self_deactivation_not_allowed` (CA-08) |
| `AccessDeniedError` (dominio) | 403 | `forbidden` (mapeo nuevo en `_map_domain`) |

`NotAuthenticatedError` la lanza la dependencia `get_current_principal` cuando no hay token valido
o el usuario esta inactivo; `AccessDeniedError` la lanza `require_action`/los casos de uso.

**Casos de uso** (`backend/app/application/use_cases/auth/` y `.../users/`, nuevos):

| Modulo | Caso de uso | Responsabilidad (RF/CA) |
|---|---|---|
| `auth/login.py` | `AuthenticateUser(user_repository, password_hasher, token_service, audit, *, session_ttl)` | `execute(usuario, contrasena)`: usuario inexistente/clave mala -> audit `LOGIN_FAILED` + `InvalidCredentialsError` (mensaje unico, CA-02); bloqueado (>=5) -> audit `LOGIN_BLOCKED` + `AccountLockedError` (CA-09); inactivo -> `InvalidCredentialsError` (sin revelar); clave mala -> incrementa intentos y persiste (RF-09); exito -> reinicia contador, audit `LOGIN_SUCCESS`, emite token de 8h con roles actuales (RF-01, CA-01) |
| `auth/logout.py` | `LogoutUser(audit)` | `execute(principal)`: audit `LOGOUT`; la invalidacion es por expiracion (stateless, decision 7) (RF-12) |
| `auth/get_session.py` | `GetSession(user_repository)` | `execute(principal)`: devuelve perfil/roles desde la BD para `GET /auth/sesion` (RF-14) |
| `users/create_user.py` | `CreateUser(user_repository, password_hasher, audit)` | `execute(principal, ...)`: solo ADMIN (garantiza la dependencia de rol), usuario duplicado -> `UsernameTakenError`, hash de contrasena, audit `USER_CREATE` (RF-08, CA-08) |
| `users/update_user.py` | `UpdateUser(user_repository, password_hasher, audit)` | `execute(principal, user_id, ...)`: 404 si no existe; desactivar a si mismo -> `SelfDeactivationError`; cambiar contrasena -> hash; **siempre reinicia `INTENTOS_FALLIDOS`** (reinicio manual por edicion, RF-09/CA-09); audit `USER_UPDATE` con detalle de campos cambiados (nunca la contrasena) (RF-08, CA-08) |
| `users/list_users.py` | `ListUsers(user_repository)` | listado para la pantalla ADMIN (RF-08); sin auditoria (RF-12 solo lista alta/baja/edicion) |

**Casos de uso existentes afectados** (`use_cases/requirement/`), cambios transversales:

- `execute(...)` gana el kwarg `principal: Principal` (o `actor: str` derivado) en toda operacion que
  escribe: `CreateRequirement`, `UpdateVersion`, `FreezeAndAdvance`, `ChangeStatus`,
  `TransitionRequirementState`, `RegisterSignature`, `Add/Update/Delete/ReorderCollectionItem`,
  `Add/Update/Delete/ReorderAttachment`, `GenerateRequirementDocuments`, `GetRequirementDocument`
  (descarga) (RF-11, RF-12, CA-11).
- `TransitionRequirementState`: **elimina `actor_id`**; primero `ensure_transition_allowed(principal.roles,
  target)` (403 sin persistir ni validar, CA-05), luego la maquina de estados/validacion integra
  existente (400) y, en exito, audit `STATE_TRANSITION` con
  `detail={"estado_anterior", "estado_actual", "motivo"}` (RF-12, RF-17, CA-11).
- `RegisterSignature`: `ensure_signature_allowed(principal.roles, payload.rol)` antes de
  `ensure_signable` (403 si rol no corresponde o es ADMIN; la politica ADR-007 no cambia) (RF-06,
  CA-06); audit `SIGNATURE_REGISTERED`.
- `CreateRequirement`/`UpdateVersion`/`FreezeAndAdvance`: audit `REQUIREMENT_CREATE`,
  `VERSION_UPDATE`, `VERSION_FREEZE`; colecciones y anexos audit `COLLECTION_UPDATE` /
  `ATTACHMENT_UPDATE` a nivel `REQ_VERSION` (interpretacion de "edicion de requerimiento y
  versiones" de RF-12, ver decisiones).
- `GenerateRequirementDocuments`: `actor` deja de tener default `SYSTEM_ACTOR` y ademas registra
  `DOCUMENT_GENERATED`; `GetRequirementDocument` registra `DOCUMENT_DOWNLOADED` (RF-07, RF-11,
  RF-12).
- Todas las firmas `Repository.save(...)` ganan el kwarg `actor` para `CREATED_BY`/`UPDATED_BY`
  (RF-11); los catalogos y datos sembrados historicos conservan `SYSTEM`.

Export en `__init__.py` de cada paquete (`__all__`), patron de SPEC-007.

## Puertos y adaptadores afectados

### Puertos (`backend/app/application/ports/`)

- `auth.py` (existente, se conserva como punto de extension, RF-18):
  - `Principal(user_id, roles)` se mantiene tal cual (SPEC-003); **decision**: `user_id` porta el
    `username` (identidad legible usada como `ACTOR`/`CREATED_BY`), sin renombrar para no romper el
    contrato ya verificado de SPEC-003.
  - `AuthProvider.current_principal() -> Principal | None` se mantiene; el adaptador local pasa a
    devolver `None` cuando no hay token, expiro o el usuario esta inactivo (401 en la dependencia).
- `user_repository.py` (nuevo) - `UserRepository(ABC)`: `get_by_username(username) -> User | None`,
  `get(user_id) -> User`, `list_all() -> Sequence[User]`, `save(user) -> User` (insert/update;
  unicidad de username traducida a `UsernameTakenError`) (RF-08).
- `password_hasher.py` (nuevo) - `PasswordHasherPort(ABC)`: `hash(password) -> str`,
  `verify(password, encoded) -> bool` (RF-09).
- `token_service.py` (nuevo) - `TokenServicePort(ABC)`: `issue(session: Session) -> str`,
  `parse(token: str) -> Session | None` (firma, `alg` fijo y expiracion; `None` si no valida)
  (RF-01, RF-13).
- `audit_repository.py` (nuevo) - `AuditRecorderPort(ABC)`: `record(entry: AuditEntry) -> None`
  (RF-12).
- `requirement_repository.py`: `save(requirement, *, actor: str)` (RF-11). El resto sin cambios.

Export en `ports/__init__.py`.

### Adaptadores (`backend/app/infrastructure/adapters/`)

- `password_hasher.py` - `Pbkdf2PasswordHasher`: stdlib `hashlib.pbkdf2_hmac`, salt de
  `secrets.token_bytes`, iteraciones de `Settings.password_hash_iterations`, verificacion con
  `hmac.compare_digest`; formato auto-descriptivo `pbkdf2_sha256$...` para poder migrar el algoritmo
  despues. **Es el unico modulo de hashing y lo reutiliza la migracion `0004`** (RF-09, RF-10).
- `jwt_token_service.py` - `JwtTokenService(TokenServicePort)`: header/payload JSON compacto,
  Base64URL, firma HMAC-SHA256 con `Settings.jwt_secret`; rechaza cualquier `alg` distinto de
  `HS256` (nunca `none`) y tokens con `exp` vencido; sin dependencias nuevas (RF-15).
- `local_auth_provider.py` - `LocalJwtAuthProvider(AuthProvider)`: constructor con token_service,
  user_repository y la cabecera `Authorization` que entrega la dependencia de request; parsea el
  token, recarga el usuario de la BD y devuelve `Principal(user_id=username, roles=roles)` solo si
  esta activo; `None` en cualquier fallo (RF-01, RF-08). Se instancia segun `Settings.auth_provider`:
  `local_jwt` -> este adaptador; `oidc` -> error de configuracion claro ("proveedor no disponible en
  esta fase", fase posterior de ADR-003, RF-18).
- `user_repository.py` - `SqlAlchemyUserRepository` (SQLAlchemy Core, mismo `Engine`/`sessionmaker`):
  lee/escribe `SYS_USUARIO` y `SYS_USUARIO_ROL` (baja = `ACTIVO='N'`, sin `DELETE`; las asignaciones
  se reemplazan por diferencia de conjuntos); traduce `IntegrityError` de `USERNAME` a
  `UsernameTakenError` (mismo patron que `DuplicateFolioError`).
- `audit_repository.py` - `SqlAlchemyAuditRecorder`: inserta en `SYS_AUDITORIA` con `ACTOR` y
  `CREATED_BY` = actor y `DETALLE` serializado a JSON (`json.dumps`, `default=str` para fechas);
  `ENTIDAD_ID` puede ser `None` (login de usuario inexistente).
- `requirement_repository.py` / `requirement_document_repository.py`: reemplazan `SYSTEM_ACTOR` por
  el `actor` recibido (RF-11).
- `mappers.py`: mappers `SYS_USUARIO` fila <-> `User` y `SYS_AUDITORIA` fila <-> `AuditEntry`.

### Cableado (`backend/app/api/dependencies.py`)

- Factorias nuevas (patron `Annotated[..., Depends(...)]` existente): `get_auth_provider(request)`,
  `get_token_service`, `get_password_hasher`, `get_user_repository`, `get_audit_recorder`,
  `get_auth_provider` sustituye al stub documentado en SPEC-003 verify; casos de uso
  `get_authenticate_use_case`, `get_logout_use_case`, `get_session_use_case`,
  `get_create_user_use_case`, `get_update_user_use_case`, `get_list_users_use_case`.
- Dependencias de enforcement:
  - `get_current_principal(auth: AuthProvider) -> Principal` - lanza `NotAuthenticatedError` (401) si
    es `None`. Declarada como `dependencies=[Depends(get_current_principal)]` en **todos** los
    routers bajo `/api/v1` (lectura y escritura); `health` y `version` no la llevan (CA-13).
  - `require_action(action: Action) -> Principal` - dependencia que resuelve el principal y aplica
    `ensure_authorized(principal.roles, action)` (403 si falta el permiso, CA-04). Se declara por
    endpoint en la matriz estatica. `FastAPI` cachea dependencias por peticion: la verificacion del
    token se hace una sola vez.
- Todas las factorias de casos de uso existentes que escriben pasan a recibir
  `Annotated[Principal, Depends(get_current_principal)]` y lo reenvian al `execute(...)`.

## API (endpoints, contratos, errores)

### Routers nuevos

`backend/app/api/routers/auth.py` (`prefix="/api/v1"`, tag `autenticacion`) y
`backend/app/api/routers/users.py` (`prefix="/api/v1"`, tag `usuarios`), registrados en
`backend/app/main.py` (`users` ademas con `dependencies=[Depends(require_action(Action.MANAGE_USERS))]`
a nivel de router).

| Metodo | Ruta | Sesion | Exito | Descripcion |
|---|---|---|---|---|
| POST | `/api/v1/auth/login` | No (publica) | 200 `LoginResponse` | `{usuario, contrasena}` -> `{token, tipo_token: "Bearer", expira_en, usuario}` (CA-01) |
| POST | `/api/v1/auth/logout` | Si | 204 | audit `LOGOUT`; el token se invalida solo por expiracion (decision 7) |
| GET | `/api/v1/auth/sesion` | Si | 200 `SesionResponse` | perfil+roles desde la BD; es el mecanismo de arranque del frontend para RF-14 (decision propia) |
| GET | `/api/v1/usuarios` | Si (ADMIN) | 200 `list[UsuarioResponse]` | listado con `intentos_fallidos` (para ver bloqueados) |
| GET | `/api/v1/usuarios/{id}` | Si (ADMIN) | 200 `UsuarioResponse` | detalle para la pantalla de edicion |
| POST | `/api/v1/usuarios` | Si (ADMIN) | 201 `UsuarioResponse` | alta: `{usuario, nombre, contrasena, roles[], activo?}` (CA-08) |
| PATCH | `/api/v1/usuarios/{id}` | Si (ADMIN) | 200 `UsuarioResponse` | edicion opcional de `{nombre, contrasena, roles, activo}`; reinicia intentos siempre (CA-09) |

Esquemas nuevos `backend/app/api/schemas/auth.py` y `schemas/user.py` (re-export en
`schemas/__init__.py`): `LoginRequest(usuario, contrasena)`, `LoginResponse`, `SesionResponse`,
`UsuarioCreate` (contrasena `min_length=8` -> 422), `UsuarioUpdate` (todo opcional),
`UsuarioResponse(id, usuario, nombre, roles, activo, intentos_fallidos)`. Validacion de forma en
Pydantic (422 `validation_error`); la longitud minima de contrasena vive aqui (decision: el dominio
no la duplica).

### Matriz de autorizacion mapeada a todos los endpoints de `/api/v1`

Leyenda de roles: `E`=ELABORO, `R`=REVISO, `A`=AUTORIZO, `AD`=ADMIN; "todos" = cualquier usuario
autenticado (union de permisos, CA-14). Todas las rutas exigen sesion valida salvo las marcadas
"publica" (RF-03, CA-03); `GET /health` y `GET /version` (raiz, fuera de `/api/v1`) permanecen
publicas (RF-03, CA-13).

| Metodo | Ruta | Roles requeridos | Base en la matriz |
|---|---|---|---|
| GET | `/health`, `/version` | publica | decision 9 |
| POST | `/auth/login` | publica | RF-01 |
| POST | `/auth/logout` | todos | RF-12 |
| GET | `/auth/sesion` | todos | RF-14 |
| GET/POST/PATCH | `/usuarios`, `/usuarios/{id}` | AD | gestion de usuarios |
| POST | `/requerimientos` | E, AD | crear/editar |
| GET | `/requerimientos` (listado), `/requerimientos/{id}` | todos | lectura |
| GET | `.../versiones`, `.../versiones/{vid}`, `.../vista-previa` | todos | lectura |
| PATCH | `.../versiones/{vid}` (cabecera/narrativa) | E, AD | crear/editar |
| POST | `.../versiones` (congelar) | E, AD | crear/editar |
| POST | `.../versiones/{vid}/validar` | todos | lectura (dry-run, no persiste; decision propia) |
| POST | `.../transicionar` | por `a_estado`: `EN_REVISION`->E,AD; `VALIDADO`->R,AD; `APROBADO`/`GENERADO`/`CANCELADO`->A,AD | filas de transicion (chequeo en caso de uso) |
| POST | `.../estado` (legacy) | mismo criterio por estado destino que `/transicionar` | decision propia |
| POST | `.../versiones/{vid}/firmas` | por `rol` del body: E, R o A segun corresponda; **AD nunca** (403) | filas de firma (chequeo en caso de uso) |
| POST/PATCH/DELETE/PUT | `.../versiones/{vid}/{c}` y `/{c}/{itemId}`, `/{c}/orden` | E, AD | crear/editar version |
| POST/PATCH/DELETE/PUT | `.../versiones/{vid}/anexos`, `/anexos/{aid}`, `/anexos/orden` | E, AD | crear/editar version |
| GET | `/catalogos/tipos-cambio`, `/catalogos/cargos` | todos | lectura |
| POST | `.../documentos` | A, AD | generar documentos (RF-07) |
| GET | `.../documentos` (historico) | todos | lectura |
| GET | `.../documentos/{did}/descarga` | todos | descargar (RF-07) |

Notas de enforcement (RF-04, CA-04):

- Orden: **401** (sin sesion) -> **403** (matriz) -> reglas de negocio (400/404/409). El 403 se
  evalua antes de persistir cualquier cosa y, en transiciones, antes de cargar/validar el
  requerimiento (rol por `a_estado` solo con el body).
- La descarga de documentos es lectura/autenticado (cualquier rol); la generacion exige A/AD.
- La matriz estatica se aplica con `Depends(require_action(...))` por endpoint; las tres filas
  dinamicas (transicion, firma, autodesactivacion) en el caso de uso con `principal`.

### Cambio de contrato de `/transicionar` (RF-17, decision 8)

- `StateTransitionRequest` pasa a `{ a_estado: str, motivo?: str }`; **se elimina `actor_id`**.
- El router reenvia `principal` al caso de uso; el actor registrado (`UPDATED_BY`, `SYS_AUDITORIA.ACTOR`)
  es siempre la identidad autenticada y el `motivo` se persiste en `DETALLE` (JSON) (CA-11).
- Un consumidor que aun envie `actor_id` no falla (Pydantic ignora campos extra por defecto) pero el
  campo desaparece del contrato y de OpenAPI; se actualiza el frontend y `doc/technical/api.md` en
  esta misma spec (riesgo de contrato, decision 12).

### Errores (envelope existente de `backend/app/api/errors.py`)

| Excepcion | HTTP | `code` |
|---|---|---|
| `NotAuthenticatedError` | 401 | `unauthenticated` |
| `InvalidCredentialsError` | 401 | `invalid_credentials` |
| `AccountLockedError` | 401 | `account_locked` |
| `AccessDeniedError` | 403 | `forbidden` |
| `UserNotFoundError` | 404 | `user_not_found` |
| `UsernameTakenError` | 409 | `username_taken` |
| `SelfDeactivationError` | 409 | `self_deactivation_not_allowed` |

Todos viajan en `{"error": {"code", "message", "details"}}` con `message` en espanol; 401/403 no
ejecutan la operacion y no dejan efectos parciales. `/transicionar` conserva su `400` especial (no
usa el envelope) para fallos de validacion, pero el `403` de rol si usa el envelope (CA-05).

Documentacion: `doc/technical/api.md` - seccion nueva `### Autenticacion y usuarios (SPEC-008)`
(login/logout/sesion/usuarios), nueva columna/seccion de autorizacion por endpoint, fila 401/403 en
la tabla de codigos, actualizacion del body de `/transicionar` y nota del cambio de contrato frente
a SPEC-005.

## Frontend (pantallas, componentes, estado)

No existe referencia Stitch para estas pantallas: se disenana con los tokens institucionales de
`frontend/src/index.css` (`@theme`), como decidio la spec (decision 11).

### Cliente y tipos

- `frontend/src/api/token.ts` (nuevo): almacenamiento del token en `localStorage`
  (`get/set/clear`); sin refresh, la expiracion la resuelve el backend con 401 (decision 7).
- `frontend/src/api/client.ts`: `send()` agrega `Authorization: Bearer <token>` cuando existe; si la
  respuesta es `401` (envelope `unauthenticated`/`invalid_credentials`) emite un evento de sesion
  vencida (lo consume `AuthContext` para abrir el overlay) y lanza `ApiError` como hoy; `403`
  (`forbidden`) lanza `ApiError` con ese `code` para que la UI muestre "Acceso denegado". El
  contrato de `request<T>()`/`requestBlob()` no cambia.
- `frontend/src/api/auth.ts`: `login(usuario, contrasena)`, `logout()`, `session()`.
- `frontend/src/api/users.ts`: `listUsers()`, `getUser(id)`, `createUser(payload)`,
  `updateUser(id, payload)`. Tipos nuevos en `api/types.ts` (`LoginResponse`, `Usuario`,
  `UsuarioPayload`) y export en `api/index.ts`.

### Contexto de sesion y overlay de login (RF-13, RF-14, CA-12)

- `frontend/src/auth/AuthContext.tsx` + `useAuth()`: estado `checking | anonymous | authenticated`
  con `{usuario, nombre, roles}`; al arrancar, si hay token -> `GET /auth/sesion` (401 -> limpia y
  `anonymous`); `login()` guarda token y perfil; `logout()` limpia.
- `frontend/src/auth/LoginOverlay.tsx`: overlay a pantalla completa con usuario/contrasena y mensaje
  de error (`invalid_credentials`/`account_locked` legibles). Se renderiza **encima** del arbol de
  `App.tsx` sin desmontar `NavContext`/la vista actual: la ruta (vista en estado) se conserva
  (RF-13, CA-12).
- Tras re-autenticarse: se reintenta el `flush()` pendiente de `useAutosave` (el borrador en memoria
  apunta a la misma version) y la vista se refresca desde la BD; el borrador **persistido** nunca
  depende de la sesion, asi que se conserva intacto (CA-12).
- `401` en cualquier peticion -> overlay; `403` -> mensaje de acceso denegado en la operacion sin
  navegar fuera ni perder el wizard (RF-14).

### Gestion de usuarios (RF-08, CA-08, CA-09)

- `frontend/src/features/users/UsersPage.tsx`: tabla (usuario, nombre, roles, activo,
  intentos/fallo de bloqueo) + formularios de alta y edicion (`components/ui` existentes:
  `Input`, `Select`, `Button`, `Badge`); al guardar, exito/error con el envelope; la edicion
  muestra el aviso "reinicia los intentos de acceso" y la desactivacion del propio usuario se
  muestra deshabilitada con el motivo (el backend tambien la rechaza).
- `frontend/src/features/users/useUsers.ts`: hook patron `{ data, loading, error, reload }` de
  `useRequirementsList`.
- `navigation/NavContext.tsx`: nuevo `AppView { name: "users" }` y entrada en `SidebarKey`; el
  elemento "Gestion de usuarios" del `Sidebar` solo se renderiza si `roles` incluye `ADMIN`
  (el backend rechaza igual con 403).
- Acciones de la matriz visibles condicionadas a roles (p. ej. "Generar DOCX/PDF" solo con
  AUTORIZO/ADMIN en `DocumentActions.tsx`); el servidor es quien realmente enforce.

### e2e (Playwright)

- `frontend/e2e/support/backend.ts`: mocks nuevos de `POST /auth/login`, `GET /auth/sesion`,
  `POST /auth/logout` y de `/usuarios`; los mocks existentes de `/api/v1` deben responder con
  envelope `unauthenticated` cuando el test lo simule.
- `frontend/e2e/auth.spec.ts` (nuevo): sin sesion -> overlay y navegacion conservada; 401 simulado
  -> overlay -> login -> la vista vuelve a cargar desde el "backend" mock con el borrador
  persistido (CA-12); 403 -> mensaje de acceso denegado; pantalla de usuarios visible solo para
  ADMIN (CA-08).
- `wizard.spec.ts`/`layout.spec.ts` adaptados: seed del token/sesion mock al inicio.

## Docker / configuracion

- `backend/app/infrastructure/config.py` - nuevas `Settings` (ademas de las existentes
  `auth_provider`, `jwt_secret`):
  - `jwt_ttl_hours: int = 8` (RF-13), `password_min_length: int = 8`,
    `password_hash_iterations: int` (valor fijado por el adaptador, p. ej. 600_000),
    `login_max_failed_attempts: int = 5` (RF-09).
  - Semilla: `seed_admin_username: str | None`, `seed_admin_password: SecretStr | None`,
    `seed_admin_nombre: str = "Administrador"` (RF-16).
- `.env.example` (raiz): seccion nueva comentada con aviso explicito de que
  `SEED_ADMIN_PASSWORD` y `JWT_SECRET` son secretos, van solo en `.env` (nunca en imagenes ni en
  git):

  ```
  # Autenticacion y semilla ADMIN (SPEC-008) - obligatorias para `alembic upgrade head`
  SEED_ADMIN_USERNAME=admin
  SEED_ADMIN_PASSWORD=cambieme_en_primer_arranque
  SEED_ADMIN_NOMBRE=Administrador
  JWT_TTL_HOURS=8
  PASSWORD_MIN_LENGTH=8
  LOGIN_MAX_FAILED_ATTEMPTS=5
  ```

- `docker-compose.yml`: **sin cambios de servicios**; el `backend` ya usa `env_file: .env`, asi que
  las variables nuevas fluyen automaticamente. Se verifica `AUTH_PROVIDER=local_jwt` y
  `AI_PROVIDER=none` (RF-15). Nada de secretos en `docker/backend.Dockerfile`.
- Ejecucion de la migracion de semilla (RF-10, CA-10): una sola vez, con el entorno levantado y
  `.env` poblado:

  ```
  docker compose exec backend alembic upgrade head
  ```

  (o `alembic upgrade head` desde `backend/` fuera de compose). La siembra del `ADMIN` ocurre dentro
  de `0004`; no hay script aparte. Si faltan `SEED_ADMIN_*`, la migracion falla con instrucciones.
- Pruebas de integracion: `tests/integration/conftest.py` gana un fixture autouse que hace
  `os.environ.setdefault` de `SEED_ADMIN_USERNAME`/`SEED_ADMIN_PASSWORD` con valores de prueba antes
  de `command.upgrade(...)` (tanto `migrated_engine` como `test_migration*.py`).
- `backend/pyproject.toml`: **sin dependencias nuevas** (JWT y hashing con stdlib; justificado en
  Enfoque, RF-15). Ningun cambio en `frontend/package.json`.

## Estrategia de pruebas

### Backend unitarias

- `tests/domain/test_authorization.py`: matriz completa por accion (incluye `ADMIN` sin firmas,
  CA-06/CA-07/CA-08), union de permisos con dos roles (CA-14), 403 (`AccessDeniedError`) sin permiso
  (CA-04), transiciones por estado destino (CA-05) y firma por rol pedido (CA-06).
- `tests/domain/test_user.py`: bloqueo al 5to intento y reinicio (CA-09), no autodesactivacion
  (CA-08), `ensure_active` (CA-08).
- `tests/domain/test_session.py`: `SESSION_TTL` de 8 horas e `is_expired` (CA-01, RF-13).
- `tests/application/test_authenticate_user.py` (fakes de repositorio/hash/token/auditoria): exito
  con roles (CA-01) y expiracion del token emitido = 8h; credenciales malas/inexistentes con mensaje
  unico que no revela existencia (CA-02) e incremento de intentos; bloqueo al 5to (CA-09) y
  `LOGIN_BLOCKED`; usuario inactivo rechazado; exito reinicia el contador.
- `tests/application/test_manage_users.py`: alta con roles y audit `USER_CREATE` (CA-08);
  edicion reinicia intentos (CA-09); autodesactivacion rechazada (CA-08); username duplicado.
- `tests/application/test_auth_audit.py`: logout y las acciones de negocio registran `AuditEntry`
  con entidad/accion/detalle (transicion con `motivo`, CA-11) y sin dependencias de IA (CA-15).
- `tests/infrastructure/test_password_hasher.py`: hash no contiene la clave en claro, verify
  positivo/negativo, formato auto-descriptivo (RF-09).
- `tests/infrastructure/test_jwt_token_service.py`: round-trip `issue`/`parse`, rechazo de token
  con firma falsa, `alg` distinto de HS256 y `exp` vencido (CA-01, CA-03).

### Backend API (`dependency_overrides` de `tests/api/`)

- `tests/api/conftest.py` nuevo: fixture `client` + `client_as(*roles)` que sobreescribe
  `get_current_principal` con un `Principal` de prueba; las pruebas existentes que no miden auth
  usan por defecto un principal con todos los roles (y dejan de asertar `SYSTEM` -> asertan el
  usuario de prueba).
- `tests/api/test_auth.py`: login 200/401 (`invalid_credentials`, `account_locked`)/422 (CA-01,
  CA-02, CA-09); logout 204; `GET /auth/sesion` (RF-14).
- `tests/api/test_auth_enforcement.py`: **401 con envelope** en endpoints de lectura y escritura sin
  token, con token invalido y con token expirado (CA-03); **403 con envelope y sin cambios
  persistidos** con rol insuficiente en escritura, transicion, firma y generacion (CA-04, CA-05,
  CA-06, CA-07); `/health` y `/version` 200 sin token (CA-13); union de permisos (CA-14).
- `tests/api/test_transition.py` (adaptado): sin `actor_id` en el body; 403 de rol con
  `estado` inalterado; exito con `motivo` auditado y `UPDATED_BY` = usuario de prueba (CA-11).
- `tests/api/test_users.py`: CRUD bajo ADMIN, 403 para cualquier otro rol, autodesactivacion 409
  (CA-08), reinicio de intentos por PATCH (CA-09).

### Backend integracion (`-m integration`, Testcontainers Oracle)

- `tests/integration/test_migration_autenticacion.py`: `alembic upgrade head` crea `SYS_USUARIO` y
  `SYS_USUARIO_ROL` y **siembra el `ADMIN`** que puede autenticarse con las credenciales de entorno
  (CA-10, RF-16); `downgrade` elimina ambas tablas.
- `tests/integration/test_user_repository.py`: persistencia de usuarios con roles multi-rol y
  contador de intentos (round-trip `User`), unicidad de `USERNAME` -> `UsernameTakenError`
  (CA-08, CA-09).
- `tests/integration/test_audit_repository.py`: insercion real en `SYS_AUDITORIA` con `ACTOR` real,
  `DETALLE` JSON valido que incluye el `motivo` de una transicion y recuperable por
  `ENTIDAD`/`ENTIDAD_ID` (CA-11).
- `tests/integration/test_migration.py` (adaptado): funciona con el fixture autouse de credenciales
  de semilla.

### Frontend

- `npm run build` (`tsc -b` + vite) sin errores.
- `npm run test:e2e`: `auth.spec.ts` nuevo + `wizard.spec.ts`/`layout.spec.ts` adaptados (CA-08,
  CA-12).

### Verificacion final (CA-16)

Desde `backend/`: `ruff check .`, `mypy --strict app`, `python -m pytest`; integracion con Docker;
desde `frontend/`: `npm run build` y `npm run test:e2e`. Las pruebas de auth corren con
`AI_PROVIDER=none` (CA-15). Evidencia en `verify.md`.

## Riesgos y decisiones (ADRs relacionados)

| Riesgo/decision | Gestion |
|---|---|
| Romper el contrato de `/transicionar` (eliminacion de `actor_id`) | Cambio documentado en la spec (RF-17, decision 12); frontend y `doc/technical/api.md` actualizados en la misma spec; el campo extra se ignora, asi que consumidores viejos no reciben 422 |
| Secretos de la semilla `ADMIN` (decision 13) | `SEED_ADMIN_*` y `JWT_SECRET` solo por variables de entorno, fuera de imagenes y de git; aviso en `.env.example`; la migracion falla si faltan en lugar de usar un default silencioso |
| Bloqueo tras 5 intentos: enumeracion de cuentas y denegacion | Credenciales invalidas devuelven siempre el mismo `invalid_credentials` (CA-02); el bloqueo responde `account_locked` con mensaje claro para que el usuario sepa que debe contactar a `ADMIN` (RF-09/CA-09 exigen claridad; se acepta que el estado de bloqueo sea visible a quien ya conoce el usuario); contador sin bloqueo pesado de filas (concurrencia extrema puede desincronizar el conteo, aceptable en MVP) |
| Pantallas de login/gestion sin referencia Stitch (decision 11) | Se disenana con tokens institucionales de `src/index.css`; sin base visual que contradiga la spec |
| JWT y hashing con stdlib en vez de PyJWT/bcrypt (RF-15) | Solo HS256 con `alg` fijo y rechazo de `none`, firma comparada con `compare_digest`, PBKDF2 con salt; sin dependencias nuevas; pruebas de round-trip y de tokens falsos |
| Sesion stateless: `logout` no invalida el token emitido | Aceptado (decision 7): la invalidacion es por expiracion de 8h y el `LOGOUT` queda auditado; un denylist exigiria persistencia de sesiones (fuera del MVP) |
| El `AuthProvider` consulta la BD en cada peticion | Una query por peticion a `SYS_USUARIO` (precio de que la BD sea fuente de verdad y de que la desactivacion surta efecto inmediato); deuda: caché corta si el volumen lo exige |
| Orden de enforcement vs respuestas existentes | 401 -> 403 -> 400/404/409; el 403 de transicion se evalua solo con el body, antes de cargar el requerimiento; `/transicionar` conserva su `400` especial no-envelope para errores de validacion |
| Pruebas existentes sin token y con `SYSTEM` | `tests/api/conftest.py` con principal por defecto para las pruebas de negocio; aserciones `SYSTEM` -> usuario de prueba; firmas de casos de uso actualizadas con `principal`/`actor`; migracion de pruebas con fixture autouse de `SEED_ADMIN_*` |
| Interpretacion de "edicion de versiones" en RF-12 | Se audit tambien colecciones y anexos a nivel `REQ_VERSION` (`COLLECTION_UPDATE`/`ATTACHMENT_UPDATE`): cubre ambas lecturas de la spec y es sobreauditar, nunca infraauditar (decision propia) |
| `GET /auth/sesion` no esta en la spec | Endpoint minimo añadido como decision propia: es la unica forma de validar el token y recuperar roles al recargar sin exponer el `JWT_SECRET` al frontend (RF-14/CA-12) |
| Contratos de fila de auditoria (`ENTIDAD`/`ACCION`) | `ENTIDAD` = nombre de tabla/entidad, `ACCION` = codigo estable en ingles (`AuditAction`), `DETALLE` = JSON con claves en espanol (`motivo`, `estado_anterior`, ...); documentado en `api.md` |
| Estado actual vs. stub de SPEC-003 | `ports/auth.py` se conserva sin cambios de firma (punto de extension, RF-18); el stub del proveedor en `dependencies.py` se sustituye por `get_auth_provider` + `LocalJwtAuthProvider`; `AUTH_PROVIDER=oidc` produce un error de configuracion claro (fase posterior de ADR-003) |
| ADRs relacionados | ADR-002 (hexagonal), ADR-003 (AuthProvider, JWT local, OIDC futuro), ADR-005 (transiciones con rol autorizado), ADR-007 (momento de firmas, sin cambios) |
