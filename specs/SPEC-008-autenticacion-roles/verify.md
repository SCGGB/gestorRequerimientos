# Verificacion - SPEC-008-autenticacion-roles

Base de comparacion: `f2587cb` (commit previo al inicio de SPEC-008, `f0c8d31`).

## Resultado por criterio de aceptacion

| CA | Resultado | Evidencia |
|---|---|---|
| CA-01 | **Cumple** | Token de 8 h con los roles actuales: `tests/domain/test_session.py` (2), `tests/infrastructure/test_jwt_token_service.py` (6, round-trip y expiracion = `SESSION_TTL`), `tests/application/test_authenticate_user.py` (7), `tests/api/test_auth.py` (7, login 200). `Settings.jwt_ttl_hours = 8` (`config.py:26`). |
| CA-02 | **Cumple** | Mensaje unico que no revela existencia: `tests/application/test_authenticate_user.py` (credenciales malas/inexistentes), `tests/api/test_auth.py` (401 `invalid_credentials`). `InvalidCredentialsError` en `application/errors.py`. |
| CA-03 | **Cumple** | 401 con envelope sin token / token invalido / token expirado: `tests/api/test_auth_enforcement.py` (10); rechazo de firma falsa, `alg` distinto de `HS256` y `exp` vencido en `tests/infrastructure/test_jwt_token_service.py` (6). `401` declarado en OpenAPI (`api/openapi.py`, `tests/api/test_openapi.py` 5). |
| CA-04 | **Cumple** | 403 con envelope y sin cambios persistidos: `tests/api/test_auth_enforcement.py` (10), `tests/domain/test_authorization.py` (11, matriz por accion), `AccessDeniedError` mapeado a 403 en `api/errors.py`. |
| CA-05 | **Cumple** | Transicion por rol del estado destino, 403 antes de persistir: `tests/domain/test_authorization.py`, `tests/api/test_transition.py` (9). |
| CA-06 | **Cumple** | Firma solo por el rol correspondiente; `ADMIN` nunca: `tests/domain/test_authorization.py` (`ensure_signature_allowed`), `tests/application/test_requirement_use_cases.py` (rol ajeno y `ADMIN` -> 403 sin persistir). |
| CA-07 | **Cumple** | Generacion de documentos restringida a `AUTORIZO`/`ADMIN`: `tests/api/test_auth_enforcement.py`; `403` declarado en `POST .../documentos` (`api/openapi.py`). |
| CA-08 | **Cumple** | Gestion de usuarios solo `ADMIN`; autodesactivacion rechazada: `tests/api/test_users.py` (9), `tests/application/test_manage_users.py` (8), `tests/domain/test_user.py` (6), `tests/integration/test_user_repository.py` (5), `frontend/e2e/auth.spec.ts` (pantalla de usuarios visible solo para `ADMIN`). Ademas verificado contra el stack Docker real: item `Gestion de usuarios` ausente para `ELABORO` y `GET /usuarios` -> 403 `forbidden` (6/6 e2e reales). |
| CA-09 | **Cumple** | Bloqueo al 5to intento y reinicio por edicion: `tests/domain/test_user.py` (6), `tests/application/test_authenticate_user.py`, `tests/application/test_manage_users.py`, `tests/api/test_users.py` (reinicio por `PATCH`), `tests/integration/test_user_repository.py`. |
| CA-10 | **Cumple** | Migracion `0004` crea `SYS_USUARIO`/`SYS_USUARIO_ROL` y siembra un `ADMIN` autenticable: `tests/integration/test_migration_autenticacion.py` (4) en la corrida de integracion con Oracle real (37 passed). |
| CA-11 | **Cumple** | Actor real y auditoria con `motivo` en `DETALLE`: `tests/integration/test_audit_repository.py` (2), `tests/application/test_auth_audit.py` (7), `tests/api/test_transition.py` (9). `SYS_AUDITORIA.ACTOR` = identidad autenticada (actor real sustituye a `SYSTEM`). Verificado tambien en la base real del stack Docker (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGIN_BLOCKED`, `USER_CREATE`, `USER_UPDATE`, `LOGOUT` con actor real y sin contrasenas en el detalle). |
| CA-12 | **Cumple** | Overlay de login sin desmontar la vista y borrador persistido conservado: `frontend/e2e/auth.spec.ts` ("401 simulado abre el overlay y tras re-autenticar conserva el borrador"), `frontend/src/auth/AuthContext.tsx`, `frontend/src/auth/LoginOverlay.tsx`. Verificado tambien contra el stack real: un token corrupto provoca un 401 real que abre el overlay manteniendo montada la vista de gestion de usuarios. |
| CA-13 | **Cumple** | `/health` y `/version` publicas (200 sin token) y `POST /auth/login` publica: `tests/api/test_auth_enforcement.py`; `401` a nivel de router en todo `/api/v1` y ausente en `/health`/`/version` (`api/openapi.py`, `tests/api/test_openapi.py`). |
| CA-14 | **Cumple** | Union de permisos con dos roles: `tests/domain/test_authorization.py` (`ensure_authorized` con union), `tests/api/test_auth_enforcement.py`; `RequiredRoles` sin herencia implicita (`domain/auth/authorization.py`). |
| CA-15 | **Cumple** | La aplicacion opera sin IA: `AI_PROVIDER=none` -> **272 passed**, 37 deselected; `create_app()` sin proveedor de IA; 0 coincidencias de cliente de IA en `backend/app`. Detalle en "Sin IA (CA-15)". |
| CA-16 | **Cumple** | Calidad completa en verde: `ruff check .`, `mypy --strict app`, **272 passed** (unitarias), **37 passed** (integracion con Oracle real), `npm run build` y **28 passed** (e2e). Adicion: stack Docker completo (oracle + backend + frontend) con **27/27** comprobaciones de API real, **6/6** e2e de navegador real y roundtrip de migraciones `0001 -> 0004 -> base -> head`. Detalle en las secciones de T-36, T-37, T-38 y "Prueba end-to-end con Docker". |

**Conclusion:** los 16 criterios de aceptacion se cumplen. Sin pendientes de la spec (las dos
observaciones DC-04 y DC-05 son deuda menor ya registrada y no bloquean ningun CA).

## Verificacion de coherencia documental (doc/technical/api.md <-> implementacion)

Alcance: `doc/technical/api.md` (T-30, sin commit) frente a routers/esquemas/errores y frente a
`spec.md`/`plan.md`. Resultado: **coherente en lo esencial**, con 3 desalineaciones y 2 observaciones
menores.

| # | Hallazgo | Severidad | Estado | Evidencia |
|---|---|---|---|---|
| DC-01 | `api.md` afirma que el token "transporta solo identidad (`sub`, `iat`, `exp`)"; el payload tambien incluye `roles`. | Media | Corregido | `doc/technical/api.md:119-121` y `plan.md` (Enfoque) actualizados para incluir `roles` y aclarar que la BD es la fuente de verdad; `jwt_token_service.py:24-29` sin cambios. |
| DC-02 | `expira_en` de `LoginResponse` no documenta unidad y el router lo fija a `28800` en duro, sin derivarlo de `Settings.jwt_ttl_hours`. | Media | Corregido | `backend/app/api/dependencies.py` (`get_session_ttl_seconds`) y `backend/app/api/routers/auth.py` ahora derivan `expira_en` de `jwt_ttl_hours * 3600`; se elimino el comentario de desarrollo. |
| DC-03 | `spec.md` (Alcance y RF-03) decia que "solo `/health` y `/version` permanecen publicos", pero `POST /auth/login` esta bajo `/api/v1` y es publico. | Media | Corregido | `spec.md:22` (Alcance) y `spec.md:51` (RF-03) actualizados para exceptuar `POST /auth/login`. |
| DC-04 | `Settings.password_min_length` no se usa: el minimo 8 esta fijo en los esquemas y en la doc. | Baja | Pendiente (deuda) | `backend/app/infrastructure/config.py:27`; `backend/app/api/schemas/user.py:7,14`; `doc/technical/api.md:104-105`. |
| DC-05 | `Action.READ` y `Action.DOWNLOAD_DOCUMENTS` no se aplican como dependencia (lecturas y descarga usan `get_current_principal`); coherente con la doc ("todos"). | Baja | Aceptado | `backend/app/domain/auth/authorization.py:11,31`; `doc/technical/api.md:69-82`. |

Coherente verificado: envelope de errores 401/403/404/409 (`api/errors.py` vs `api.md:23-31`), matriz de
transiciones y firmas (`authorization.py:35-47` vs `api.md:74-76`), endpoints `/auth` y `/usuarios`
(`routers/auth.py`, `routers/users.py` vs `api.md:92-100`), contrato de `/transicionar` sin `actor_id`
(`schemas/validation.py:47-49` vs `api.md:146-153`), actor real sustituyendo a `SYSTEM`, y esquemas
listados (`api.md:265-266`).

## Integracion con Docker + Testcontainers (T-36)

Comando (desde `backend/`, imagen cacheada `gestor-req-integration` con Testcontainers + Oracle
Free 23ai y LibreOffice):

```
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v "<ruta-absoluta>/backend:/app" -w /app \
  -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal \
  gestor-req-integration:latest \
  sh -c "python -m pytest -m integration tests/integration -p no:cacheprovider -q"
```

Resultado: **37 passed** (Oracle real via `gvenzl/oracle-free`, migracion Alembic `0001` -> `0004`).

| Evidencia | Resultado | Detalle |
|---|---|---|
| Migracion `0004` + semilla `ADMIN` (T-11, CA-10) | PASSED | `test_migration_autenticacion.py::test_upgrade_creates_auth_schema`, `::test_upgrade_seeds_admin_and_hash_verifies`, `::test_downgrade_drops_auth_tables` |
| `ADMIN` sembrado autenticable de punta a punta (T-11, CA-10) | PASSED | `test_migration_autenticacion.py::test_seeded_admin_authenticates_end_to_end` (login real con `AuthenticateUser` + repositorios reales: token con rol `ADMIN` y auditoria `LOGIN_SUCCESS`) |
| Repositorio de usuarios (T-12, CA-08, CA-09) | PASSED | `test_user_repository.py` (5): round-trip multi-rol, roles por diferencia de conjuntos, baja logica, `UsernameTakenError`, listado ordenado |
| Repositorio de auditoria con `motivo` en `DETALLE` (T-13, CA-11) | PASSED | `test_audit_repository.py` (2): `DETALLE` JSON con `motivo`/`estado_actual`, `ENTIDAD_ID` nulo permitido |
| Pruebas de migracion existentes con el fixture autouse | PASSED | `test_migration.py` (2), `test_migration_requerimiento.py` (5), `test_requirement_document_repository.py` (5); el fixture autouse de sesion `tests/integration/conftest.py::_seed_admin_env` fija `SEED_ADMIN_*` antes de cualquier `upgrade` |
| Resto de la suite de integracion (sin regresiones) | PASSED | `test_database_engine.py` (2), `test_document_conversion.py` (2), `test_requirement_repository.py` (5), `test_requirement_repository_search.py` (5) |
| Lint y tipos (sin regresiones por el cambio) | PASSED | `ruff check .` -> All checks passed; `mypy --strict app` -> Success (114 archivos) |

## Lint, tipos y unitarias backend (T-37)

Comandos (desde `backend/`, imagen cacheada `gestor-req-dev`):

| Comando | Resultado |
|---|---|
| `ruff check .` | All checks passed |
| `mypy --strict app` | Success: no issues found in 115 source files |
| `python -m pytest` | **272 passed**, 37 deselected (integracion), 5 warnings |
| `AI_PROVIDER=none python -m pytest` | **272 passed**, 37 deselected (integracion) |
| `AI_PROVIDER=none python -m pytest tests/api/test_auth.py tests/api/test_auth_enforcement.py tests/api/test_users.py` | 26 passed (pruebas de auth sin IA) |
| `AI_PROVIDER=none` + `create_app()` | `ai_provider = none`; app creada sin ningun proveedor de IA |

La aplicacion no contiene ningun cliente de IA: la busqueda de `openai|ollama|anthropic|gpt-|llm|ia_provider|ai_client|assistant`
en `backend/app` no devuelve coincidencias (CA-15). `AI_PROVIDER` solo existe como parametro de `Settings`
(`backend/app/infrastructure/config.py:33`) y no habilita ninguna dependencia.

### `GET /openapi.json` con las columnas 401/403 (CA-16)

Al verificar el criterio de T-37, el esquema OpenAPI **no** documentaba `401`/`403` en ningun endpoint (solo
`200`/`201`/`204`/`422`). Se corrigio para que el contrato publicado coincida con la matriz de autorizacion:

- Nuevo `backend/app/api/openapi.py`: respuestas reutilizables del envelope (`UNAUTHENTICATED_RESPONSE`,
  `INVALID_CREDENTIALS_RESPONSE`, `FORBIDDEN_RESPONSE`, `not_found_response`, `conflict_response`) que referencian
  el esquema `ErrorResponse` e incluyen un ejemplo por codigo.
- `401` a nivel de router en todos los routers de `/api/v1` (`auth`, `users`, `requirements`, `validation`,
  `collections`, `attachments`, `documents`, `signatures`, `catalogs`); `POST /auth/login` lo sobreescribe con
  `invalid_credentials`/`account_locked`.
- `403` en los endpoints con restriccion de rol de la matriz del plan: `/usuarios*`, `POST /requerimientos`,
  `PATCH .../versiones/{vid}`, `POST .../versiones`, `POST .../estado`, `POST .../transicionar`,
  `POST .../firmas`, `POST .../documentos`, colecciones y anexos.
- `404`/`409` en `/usuarios` (`user_not_found`, `username_taken`, `self_deactivation_not_allowed`), como documenta
  `doc/technical/api.md`.
- `/health` y `/version` siguen publicos y sin `401`/`403` (CA-13).

Nuevo `backend/tests/api/test_openapi.py` (5 pruebas) como regresion: endpoints nuevos presentes, `401` en todo
`/api/v1`, `403` en los endpoints con restriccion de rol, `401` del login con `invalid_credentials`/`account_locked`
y `ErrorResponse` registrado en `components.schemas`.

## Build frontend y e2e (T-38)

Comandos (desde `frontend/`):

| Comando | Resultado |
|---|---|
| `npm run build` (`tsc -b && vite build`) | PASSED - sin errores de tipos; `vite v7.3.7`, 94 modulos transformados, `dist/assets/index-DGCsU81Y.js` 292.10 kB (gzip 87.45 kB) y `dist/assets/index-CiBqznrS.css` 23.10 kB (gzip 5.23 kB) |
| `npm run test:e2e` (Playwright, chromium) | **28 passed** (23.1 s), 0 skipped, 0 failed |
| `npm run test:e2e` (segunda corrida, detector de instabilidad) | **28 passed** (10.9 s) |

Detalle de la suite e2e (T-35, `frontend/e2e/`):

| Archivo | Pruebas | Alcance |
|---|---|---|
| `auth.spec.ts` | 6 | sin sesion -> overlay de login (CA-12); credenciales invalidas con mensaje legible; 401 simulado -> overlay -> re-autenticacion conservando el borrador persistido (CA-12); 403 -> acceso denegado sin perder el wizard (RF-14); gestion de usuarios visible y operable solo para ADMIN (CA-08) |
| `layout.spec.ts` | 4 | layout base, navegacion en la barra lateral, vista de overview, humo de proxy con rutas relativas `/api/v1` (suite adaptada con semilla de sesion) |
| `wizard.spec.ts` | 18 | pasos 1-13 del asistente (validaciones, colecciones, beneficios, contexto, requisitos futuros, control documental, revision, vista previa, autosave, impresion, generacion y descarga de DOCX/PDF) con sesion sembrada al inicio |

Notas:

- La suite e2e corre contra el servidor de desarrollo de Vite (`webServer` en `playwright.config.ts`,
  `npm run dev -- --port 5173`) con el backend simulado por `e2e/support/backend.ts` (mocks de
  `/auth/login`, `/auth/sesion`, `/auth/logout` y `/usuarios`, y envelope `unauthenticated` cuando el
  test lo simula).
- `playwright.config.ts` no define `retries` fuera de CI (`retries: process.env.CI ? 2 : 0`), por lo
  que las dos corridas anteriores son sin reintentos: no hay cobertura de reintentos ocultando fallos.
- `dist/`, `playwright-report/` y `test-results/` estan en `frontend/.gitignore`: la corrida no deja
  artefactos versionables.

## Verificacion de alcance (T-39)

Comparacion contra `f2587cb` (commit previo al inicio de SPEC-008).

### RF-15 - Sin dependencias nuevas

| Archivo | Resultado | Evidencia |
|---|---|---|
| `backend/pyproject.toml` | **Sin cambios** | `git diff f2587cb -- backend/pyproject.toml` vacio. Dependencias: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `oracledb`, `docxtpl` (dev: `ruff`, `mypy`, `pytest`, `pytest-cov`, `httpx`, `testcontainers`). Sin `pyjwt`, `python-jose`, `passlib`, `bcrypt`, `argon2` ni `cryptography`. |
| `frontend/package.json` | **Sin cambios** | `git diff f2587cb -- frontend/package.json` vacio. Dependencias: `react`, `react-dom` (dev: vite, tailwind, typescript, playwright). |
| `frontend/package-lock.json` | **Sin cambios** | `git diff --stat f2587cb -- frontend/package-lock.json` vacio: no se instalo nada nuevo en el frontend. |

JWT y hashing se implementan **solo con stdlib**, tal como decisiono el plan:

- `infrastructure/adapters/jwt_token_service.py`: `base64`, `hashlib`, `hmac`, `json`, `datetime`.
- `infrastructure/adapters/password_hasher.py`: `base64`, `hashlib`, `hmac`, `secrets` (PBKDF2-HMAC-SHA256).
- Busqueda de `import|from` de `jwt|passlib|bcrypt|jose|authlib|oauthlib|itsdangerous|argon2|cryptography|pyjwt` en
  todo `backend/app`: **0 coincidencias**.

### RF-16 - Docker, secretos y configuracion

| Chequeo | Resultado | Evidencia |
|---|---|---|
| `docker-compose.yml` sin cambios de servicios | PASSED | `git diff f2587cb -- docker-compose.yml` vacio. Sigue con 4 servicios (`oracle`, `rustfs`, `backend`, `frontend`) y 2 volumenes; `backend` conserva `env_file: .env` (`required: false`), por lo que `SEED_ADMIN_*`, `JWT_SECRET`, `JWT_TTL_HOURS`, `PASSWORD_MIN_LENGTH` y `LOGIN_MAX_FAILED_ATTEMPTS` fluyen automaticamente sin tocar el compose. |
| `docker/` (Dockerfiles) sin cambios | PASSED | `git diff --stat f2587cb -- docker/` vacio. `backend.Dockerfile`, `backend-dev.Dockerfile`, `backend-integration.Dockerfile`, `frontend.Dockerfile` y `frontend.nginx.conf` intactos. |
| Sin secretos en imagenes | PASSED | Busqueda de `SEED_ADMIN|JWT_SECRET|PASSWORD=|SECRET=|TOKEN=|wallet` en todos los archivos de `docker/`: **0 coincidencias**. El wallet de Oracle se monta como volumen (`ORACLE_WALLET_DIR` en `.env.example`), nunca en la imagen. |
| Secretos fuera de git | PASSED | `.env` esta en `.gitignore` (raiz) y no esta trackeado; el unico archivo de entorno versionado es `.env.example`. `git ls-files` solo devuelve `.env.example`. |
| `.env.example` con aviso de secretos | PASSED | Seccion nueva (T-06) con `JWT_SECRET`, `SEED_ADMIN_USERNAME`, `SEED_ADMIN_PASSWORD`, `SEED_ADMIN_NOMBRE`, `JWT_TTL_HOURS`, `PASSWORD_MIN_LENGTH`, `LOGIN_MAX_FAILED_ATTEMPTS` y el aviso explicito "SECRETO: solo en `.env`, nunca en imagenes ni en git". Unica modificacion fuera de `backend/` y `frontend/` (`.env.example`: +9 lineas). |
| Sin default implicito de credenciales | PASSED | `alembic/versions/0004_usuarios_autenticacion.py:41-45`: si faltan `SEED_ADMIN_USERNAME` o `SEED_ADMIN_PASSWORD` la migracion falla con error en espanol; no hay default silencioso. La insercion usa parametros bound (`:username`, `:password_hash`), el secreto nunca via f-string. |
| Una sola implementacion de hashing | PASSED | La migracion `0004` reusa `Pbkdf2PasswordHasher` (`0004_usuarios_autenticacion.py:35,47-48`): no hay un segundo algoritmo de derivacion de claves. |

### RF-18 - `AuthProvider` como punto de extension (sustituible por OIDC sin tocar el dominio)

| Chequeo | Resultado | Evidencia |
|---|---|---|
| `ports/auth.py` sin cambios de firma | PASSED | `git diff f2587cb -- backend/app/application/ports/auth.py` **vacio** (byte a byte identico). `Principal(user_id: str, roles: frozenset[str])` y `AuthProvider.current_principal() -> Principal | None` intactos (SPEC-003). |
| Dominio sin imports de JWT/OIDC | PASSED | Todos los imports de `backend/app/domain/`: solo stdlib (`collections.abc`, `dataclasses`, `datetime`, `enum`, `typing`) e imports intra-dominio (`app.domain.auth.*`, `app.domain.requirement.*`). Busqueda de `jwt|oidc|oauth|hashlib|hmac|base64|pbkdf2|token` en `domain/`: **0 coincidencias**. |
| Dominio sin dependencias hacia application/infrastructure/api | PASSED | Busqueda de `app.(application|infrastructure|api)` en `domain/`: **0 coincidencias** (regla 12 de `AGENTS.md`, dominio puro). |
| Sustitucion por OIDC acotada al adaptador | PASSED | El unico punto que conoce el proveedor es `infrastructure/adapters/local_auth_provider.py:54-70` (`build_auth_provider`: `local_jwt` -> `LocalJwtAuthProvider`; `oidc` -> `AuthProviderConfigurationError` con mensaje "ver ADR-003: OIDC es una fase posterior"). La API consume solo el puerto: `api/dependencies.py:341-356` (`get_auth_provider` -> `get_current_principal`). Implementar OIDC es **anadir un adaptador** que cumpla `AuthProvider`; no obliga a tocar dominio, casos de uso ni puertos. |
| Puerto intacto en el arbol de cambios | PASSED | `backend/app/application/ports/auth.py` no aparece en `git diff --name-status f2587cb` (archivo no modificado). |

### Sin IA (CA-15)

| Chequeo | Resultado | Evidencia |
|---|---|---|
| App creada con `AI_PROVIDER=none` | PASSED | `create_app()` en la imagen `gestor-req-dev`: `ai_provider = none`, `auth_provider = local_jwt`, `jwt_ttl_hours = 8`, 15 rutas registradas, app creada sin proveedor de IA. |
| Suite completa con `AI_PROVIDER=none` | PASSED | `AI_PROVIDER=none python -m pytest` -> **272 passed**, 37 deselected (integracion), 5 warnings. |
| Sin cliente de IA en el codigo | PASSED | `grep -rEil 'openai|ollama|anthropic|gpt-|llm|ai_client|assistant' backend/app` -> **0 archivos**. `AI_PROVIDER` solo existe como parametro de `Settings` (`config.py:33`) y no habilita ninguna dependencia. |

## Prueba end-to-end con Docker (stack completo)

Nivel 1 (API real + navegador real) y Nivel 2 (integracion) ejecutados sobre el stack de
`docker-compose.yml`: Oracle real, FastAPI real y frontend Vite real, **sin mocks**.

### Entorno

| Componente | Detalle |
|---|---|
| `oracle` | Oracle Database Free 23ai, puerto `1521`, healthy |
| `backend` | FastAPI + uvicorn en `8000`, healthy, imagen `docker/backend.Dockerfile` |
| `frontend` | Vite dev server en `5173`, proxy `/api`, `/health`, `/version` -> `http://backend:8000` |
| Volumen | recreado desde cero (`docker compose down -v`) para partir de un esquema limpio |
| Configuracion | `.env` local (ignorado por git) con `ORACLE_PASSWORD`, `JWT_SECRET`, `SEED_ADMIN_USERNAME=admin`, `SEED_ADMIN_PASSWORD`, `AI_PROVIDER=none` |

### Correccion de infraestructura requerida

`docker/backend.Dockerfile` no copiaba `alembic/` ni `alembic.ini` a la imagen final, por lo que el
contenedor `backend` no podia ejecutar las migraciones (`alembic: not found`). Correccion aplicada:

```dockerfile
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
```

### Migraciones sobre el volumen limpio (roundtrip)

| Paso | Resultado |
|---|---|
| `alembic upgrade head` | PASSED - `0001` -> `0004_usuarios_autenticacion` |
| `alembic downgrade base` | PASSED - elimina `SYS_USUARIO_ROL` y `SYS_USUARIO` |
| `alembic upgrade head` | PASSED - vuelve a `head` |

### Nivel 1a - Smoke de API contra Oracle real

Script `smoke.ps1` (temporal, fuera del repo) ejecutando `http://localhost:8000/api/v1`:
**27/27 comprobaciones PASSED**.

| Area | Comprobaciones |
|---|---|
| Login (CA-01, CA-02) | `POST /auth/login` 200 con `expira_en = 28800` (8 h); `GET /auth/sesion` 200 con roles; usuario inexistente y clave incorrecta devuelven el mismo envelope `invalid_credentials` (mensaje unico, sin revelar existencia) |
| Enforcement (CA-03, CA-04) | Sin token -> 401 `unauthenticated`; token invalido -> 401; recurso ajeno -> 403 `forbidden` |
| Gestion de usuarios (CA-08, CA-09) | Alta 201; usuario duplicado -> 409 `username_taken`; contrasena corta -> 422; 5 intentos fallidos -> 409 `account_locked`; `PATCH` reinicia `intentos_fallidos`; autodesactivacion -> 409 `self_deactivation_not_allowed`; `POST /auth/logout` 204 |
| Endpoints publicos (CA-13) | `GET /version` responde 200 sin token |

### Nivel 1b - Navegador real (Playwright sin mocks)

Suite temporal ejecutada con `npx playwright test --config .tmp-real-e2e/playwright.config.ts`
(`baseURL: http://localhost:5173`, sin `webServer`, sin mocks de `/auth/*` ni `/usuarios`):
**6 passed**.

| Prueba | Criterio | Evidencia en el stack real |
|---|---|---|
| Sin sesion el overlay bloquea la aplicacion pero no desmonta la vista | CA-12 | `login-overlay` visible y `Requerimientos` sigue montado por debajo |
| Login real: el token se guarda y la sesion se valida contra el backend | CA-01, CA-13 | JWT HS256 de 3 segmentos en `localStorage`; tras recargar la sesion persiste (`GET /auth/sesion` real) y el menu `Gestion de usuarios` aparece |
| Credenciales invalidas muestran el mensaje del envelope real | CA-02 | El overlay muestra `Usuario o contrasena incorrectos.` (mensaje unico del backend real) |
| ADMIN: la gestion de usuarios lista, crea y edita usuarios reales | CA-08, CA-09 | Tabla con `admin`; alta con rol `Elaboro` y estado `Activo`; edicion con aviso de reinicio de intentos y cambio de nombre |
| Un ELABORO no ve la gestion de usuarios y la API responde 403 | CA-08 | El item `Gestion de usuarios` no existe para el rol `ELABORO` y `GET /api/v1/usuarios` responde 403 `forbidden` |
| Un token corrupto abre el overlay sin perder la vista montada | CA-12, RF-14 | `POST /usuarios` con token invalido -> 401 real -> el overlay aparece y `Gestion de usuarios` sigue montado debajo |

### Nivel 2 - Integracion con Oracle real (Testcontainers)

Mismo comando de la seccion T-36 (imagen `gestor-req-integration`):

```
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v "<ruta-absoluta>/backend:/app" -w /app \
  -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal \
  gestor-req-integration:latest \
  sh -c "python -m pytest -m integration tests/integration -p no:cacheprovider -q"
```

Resultado: **37 passed**, 0 failed, 0 skipped, 0 errores (exit code 0).

### Auditoria verificada en la base real

Consultas directas a `SYS_USUARIO`, `SYS_USUARIO_ROL` y `SYS_AUDITORIA` del contenedor `oracle`:

| Evidencia | Resultado | Detalle |
|---|---|---|
| Semilla de `ADMIN` (CA-10) | PASSED | `SYS_USUARIO`: `admin` / `Administrador`, `ACTIVO = 'S'`, hash `pbkdf2_sha256$200000$...` |
| Roles (CA-08) | PASSED | `SYS_USUARIO_ROL`: `admin -> ADMIN`, usuario `ELABORO` -> `ELABORO` |
| Auditoria de acceso (CA-11) | PASSED | `LOGIN_SUCCESS`, `LOGIN_FAILED` (con `motivo` e `intentos`), `LOGIN_BLOCKED`, `USER_CREATE`, `USER_UPDATE`, `LOGOUT`, siempre con `ACTOR` real |
| Sin contrasena en la auditoria | PASSED | `USER_UPDATE` registra `{"contrasena": "cambiada"}`, nunca el valor de la clave |
| Actor real (CA-11) | PASSED | `LOGIN_SUCCESS` con `ACTOR = e2e30904` (el propio usuario, no `SYSTEM`) |

## Hallazgos

- DC-01, DC-02 y DC-03 (**media**) fueron **corregidos** el 2026-10-21.
- DC-04 y DC-05 quedan como observaciones menores (deuda).
- DC-06, DC-07 y DC-08 se registraron con la prueba end-to-end con Docker (ver abajo). DC-07 (no hay
  cierre de sesion en la UI) es el unico hallazgo **funcional**; no incumple ningun CA ni RF de SPEC-008
  (RF-14 no exige un boton de cierre de sesion), por lo que queda como tarea de una spec posterior.
- Tras las correcciones, la coherencia documental se considera **Cumple**: `doc/technical/api.md`
  describe correctamente la matriz, los endpoints, los errores y el payload del token, y `spec.md`
  ya no contradice el login publico.
- Calidad: `ruff check .`, `mypy --strict app` y `python -m pytest` en verde (imagen `gestor-req-dev`).
- Alcance (T-39): **sin hallazgos**. No se introdujeron dependencias nuevas (RF-15), `docker-compose.yml`
  y los Dockerfiles no cambiaron y no contienen secretos (RF-16), `ports/auth.py` conserva su firma y el
  dominio sigue sin imports de JWT/OIDC, por lo que el proveedor OIDC es sustituible sin tocarlo
  (RF-18), y la aplicacion opera con `AI_PROVIDER=none` (CA-15).
- Infraestructura: `docker/backend.Dockerfile` se corrigio para incluir `alembic/` y `alembic.ini` en la
  imagen final (sin esto el contenedor `backend` no podia migrar). No afecta al alcance de la spec.
- Estado final de SPEC-008: los 39 tasks estan completados, los 16 criterios de aceptacion se cumplen y
  la prueba end-to-end con Docker (Nivel 1 y Nivel 2) esta en verde. La implementacion queda lista para
  commit de cierre de fase.

## Correcciones aplicadas (2026-10-21)

- DC-01: `doc/technical/api.md` y `plan.md` documentan `roles` en el payload del token y que la BD es la
  fuente de verdad.
- DC-02: `get_session_ttl_seconds` en `dependencies.py`; `routers/auth.py` deriva `expira_en` de
  `jwt_ttl_hours * 3600`.
- DC-03: `spec.md` RF-03 y Alcance exceptuan `POST /auth/login`.

## Deuda tecnica registrada

- DC-04: usar `PASSWORD_MIN_LENGTH` o retirarlo de `Settings`.
- DC-05: valorar `require_action(Action.READ)`/`Action.DOWNLOAD_DOCUMENTS` para enforcement explicito.
- DC-06: `backend/app/infrastructure/adapters/user_repository.py` fija `CREATED_BY`/`UPDATED_BY` en `"SYSTEM"`
  para las filas de `SYS_USUARIO`. No incumple RF-11 (que aplica a las tablas de negocio `REQ_*`) ni RF-12
  (la trazabilidad real queda en `SYS_AUDITORIA`, con `ACTOR` real verificado). Deuda menor: propagar el
  actor autenticado hasta `SYS_USUARIO` si se requiere auditoria por fila de usuario.
- DC-07: **no existe control de cierre de sesion en la interfaz**. `AuthContext.logout()` y
  `POST /auth/logout` existen y funcionan (verificado en el smoke y en `SYS_AUDITORIA`), pero ningun
  componente del frontend los invoca: la busqueda de `logout` en `frontend/src` solo devuelve
  `api/auth.ts` y `auth/AuthContext.tsx`. Consecuencia: el usuario no puede terminar su sesion desde la
  aplicacion; el token permanece en `localStorage` hasta que expiran las 8 h. RF-14 no exige explicitamente
  un boton de cierre de sesion, por lo que **no es incumplimiento de la spec**, pero es un hueco funcional
  que conviene cerrar en una spec siguiente.
- DC-08: sin sesion, la vista de requerimientos (montada por debajo del overlay) pide `GET /requerimientos`
  sin token y muestra el banner `Se requiere autenticacion.` detrás del overlay. El overlay cumple su
  funcion (CA-12, RF-14) y el mensaje es legible, pero la peticion 401 es evitable y el banner queda
  visible tras el overlay. Deuda menor de UX.

### Detalle de DC-07 (evidencia)

| Chequeo | Resultado |
|---|---|
| `logout()` en `AuthContext` | Implementado (`frontend/src/auth/AuthContext.tsx:116`), invoca `logoutRequest()` y limpia token, usuario y estado |
| `POST /auth/logout` | 204 verificado en el smoke real y `LOGOUT` registrado en `SYS_AUDITORIA` |
| Invocacion desde la UI | **Ninguna**: `grep -r "logout" frontend/src` solo devuelve `api/auth.ts` (cliente HTTP) y `auth/AuthContext.tsx` (contexto); ningun componente lo invoca |
| Boton/menu de cierre de sesion | No existe en `AppLayout`, `Sidebar` ni `UsersPage` |
