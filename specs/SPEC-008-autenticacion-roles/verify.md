# Verificacion - SPEC-008-autenticacion-roles

| Criterio | Resultado | Evidencia |
|---|---|---|
| CA-01 | Cumple / Parcial / No cumple | archivo, prueba o comando |

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

## Hallazgos

- DC-01, DC-02 y DC-03 (**media**) fueron **corregidos** el 2026-10-21.
- DC-04 y DC-05 quedan como observaciones menores (deuda).
- Tras las correcciones, la coherencia documental se considera **Cumple**: `doc/technical/api.md`
  describe correctamente la matriz, los endpoints, los errores y el payload del token, y `spec.md`
  ya no contradice el login publico.
- Calidad: `ruff check .`, `mypy --strict app` y `python -m pytest` en verde (imagen `gestor-req-dev`).

## Correcciones aplicadas (2026-10-21)

- DC-01: `doc/technical/api.md` y `plan.md` documentan `roles` en el payload del token y que la BD es la
  fuente de verdad.
- DC-02: `get_session_ttl_seconds` en `dependencies.py`; `routers/auth.py` deriva `expira_en` de
  `jwt_ttl_hours * 3600`.
- DC-03: `spec.md` RF-03 y Alcance exceptuan `POST /auth/login`.

## Deuda tecnica registrada

- DC-04: usar `PASSWORD_MIN_LENGTH` o retirarlo de `Settings`.
- DC-05: valorar `require_action(Action.READ)`/`Action.DOWNLOAD_DOCUMENTS` para enforcement explicito.
