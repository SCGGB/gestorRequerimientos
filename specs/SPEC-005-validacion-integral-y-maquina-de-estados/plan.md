# Plan tecnico - SPEC-005

> Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`,
> `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`,
> `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/007-firmas-segun-estado.md`,
> `doc/development/convenciones.md`, `doc/technical/api.md`.
> Esta spec es de **backend** (dominio + application + api). No incluye DOCX/PDF (SPEC-007),
> vista previa (SPEC-006), autorizacion por roles (SPEC-008) ni firma electronica.

## Enfoque

SPEC-005 añade validación integral (dry-run) y una máquina de estados explícita con sus
endpoints, encima de lo ya construido por SPEC-002/003/004. El trabajo se divide en cuatro
frentes, en este orden:

1. **Dominio puro**: modulo `validation.py` con el validador integral de una versión
   (`ValidationIssue`, `ValidationResult`, reglas por sección del machote, regla condicional
   de requisitos futuros y control documental según transición) y la máquina de estados
   explícita (mapa de transiciones accesible, alineado a las reglas de negocio de la spec).
   Sin imports de FastAPI/SQLAlchemy.
2. **Casos de uso**: `ValidateRequirementVersion` (dry-run, no persiste) y
   `TransitionRequirementState` (valida precondiciones, aplica la transición de dominio y
   devuelve un resultado estructurado; no lanza excepción por transición inválida).
3. **API**: esquemas `ValidationResultResponse`/`ValidationErrorSchema` y
   `StateTransitionRequest`/`StateTransitionResponse`, endpoints
   `POST /requerimientos/{id}/versiones/{vid}/validar` y `POST /requerimientos/{id}/transicionar`,
   cableado en `dependencies.py` y actualización de `doc/technical/api.md`.
4. **Pruebas y calidad**: pytest de dominio, casos de uso y API; `ruff`, `mypy --strict`.

Principios rectores: la BD es la fuente de verdad (la validación lee el agregado persistido,
no estado de cliente); la validación es pura e idempotente (dry-run); las transiciones no
crean firmas (ADR-007); sin dependencias nuevas.

### Inventario: que existe ya y que falta

| Elemento de la SPEC | Estado actual | Trabajo en esta spec |
|---|---|---|
| RF-01 estados | `RequirementStatus` con los 6 estados (`domain/requirement/enums.py`) | Sin cambios |
| Maquina de estados | `_ALLOWED_TRANSITIONS` + `Requirement.change_status` (`domain/requirement/requirement.py`); endpoint legacy `POST /requerimientos/{id}/estado` (SPEC-003) | El mapa se mantiene (spec corregida: incluye retrocesos); añadir `allowed_transitions()` como acceso publico y endpoint `/transicionar` con contrato de la spec |
| RF-02/RF-03/RF-04 validador integral | No existe en backend. Espejo **solo de forma** en `frontend/src/features/wizard/wizardSteps.ts` (`isComplete`, incluida la condicional de requisitos futuros) | Nuevo modulo de dominio `validation.py` + caso de uso + endpoint dry-run |
| RF-05 `/validar` | No existe | Nuevo |
| RF-06/RF-07 `/transicionar` | No existe (hay `/estado` con `StatusChangeRequest.nuevo_estado` → `RequirementResponse`) | Nuevo endpoint con `a_estado`/`motivo`/`actor_id` y respuesta `estado_anterior`/`estado_actual`/`transicion_valida` |
| RF-08 firmas APROBADO/GENERADO | `ensure_signable` + `SignatureNotAllowedError` → 409 `signature_not_allowed`; pruebas de API existentes | Sin cambios (CA-08 se cubre con regresión) |
| RF-09 dry-run en BORRADOR | No existe | El caso de uso no persiste nada |
| RF-10 errores accionables | Envelope de error global (`api/errors.py`) | Errores de validación con `path`+`seccion` por item |
| Frontend | Paso 12 captura `signers` en estado local (no persiste, coherente con ADR-007); `useAutosave` no interviene | Sin cambios exigidos por los CA (ver sección Frontend) |

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic

**No aplica.** No se introduce ninguna tabla, columna, indice ni migración:

- El estado ya persiste en `REQ_REQUERIMIENTO.ESTADO` (migración `0002_modelo_requerimiento`).
- La validación integral es computo puro sobre el agregado ya cargado; no requiere nuevas
  estructuras ni indices.
- Las firmas exigidas por el control documental usan `REQ_FIRMA` existente (roles
  `ELABORO`/`AUTORIZO` sobre la versión vigente, ADR-007).

`motivo` y `actor_id` de `StateTransitionRequest` se aceptan en el contrato pero **no se
persisten** (no existe tabla de historial de transiciones y esta spec no crea una — sus
"no incluye" reutiliza el esquema existente). Quedan registrados en log de la aplicación y
documentados como deuda para una futura spec de auditoría de transiciones (decisión Q-5,
confirmada).

`alembic upgrade head` sigue siendo el único mecanismo de DDL (sin cambios).

## Dominio y casos de uso

### Dominio (`app/domain/requirement/`)

**Nuevo `validation.py`** (Python puro, sin infraestructura):

- `ValidationIssue` (frozen dataclass): `path: str` (campo/sección afectado, p.ej.
  `necesidad_actual`, `objetivos`, `requisitos_futuros_texto`, `signers.ELABORO.nombre`),
  `code: str` (identificador en inglés), `message: str` (español, accionable), `section: str`
  (nombre visible de la sección del machote en español).
- `ValidationResult` (frozen dataclass): `errors: tuple[ValidationIssue, ...]`,
  `warnings: tuple[ValidationIssue, ...]`; propiedad `is_valid` (`not errors`).
- `validate_requirement(requirement: Requirement, *, target_state: RequirementStatus | None = None) -> ValidationResult`
  — valida la **versión vigente** (`current_version()`; si no hay versión, error estructurado
  `no_current_version`). Reglas (RF-02, RF-10):

  | Sección (español) | Regla | `codigo` |
  |---|---|---|
  | Datos generales | `title`, `change_type_id`, `system`, `document_version`, `version_date` no vacíos/nulos | `required_field` |
  | Necesidad actual | `current_need` no vacío | `required_field` |
  | Objetivos generales | `>= 1` elemento **activo** | `min_active_items` |
  | Consideraciones | `>= 1` activo | `min_active_items` |
  | Beneficios esperados | `>= 1` activo | `min_active_items` |
  | Diagramas contextuales | `context_description` no vacío | `required_field` |
  | Usuarios y permisos | `users_permissions` no vacío | `required_field` |
  | Restricciones | `>= 1` activo | `min_active_items` |
  | Requisitos futuros | Regla condicional RF-03/RF-04 | `future_requirements_missing` |
  | Volumetria y rendimiento | `>= 1` activo | `min_active_items` |
  | Riesgos iniciales | `>= 1` activo | `min_active_items` |
  | Control documental | Solo cuando `target_state = GENERADO`: firmas `ELABORO` y `AUTORIZO` con nombre no vacío en la versión vigente | `signatures_missing` |
  | Consistencia | `requisitos_futuros_aplica=false` con texto o elementos activos → **advertencia** (no bloquea) | `future_requirements_orphan` |

  - RF-03: `future_requirements_applies=false` → no se emiten errores por texto vacío ni por
    lista vacía (CA-03).
  - RF-04: `future_requirements_applies=true` → se exige texto no vacío **o** `>= 1` elemento
    activo; si falta, un error con `path="requisitos_futuros_texto"`,
    `section="Requisitos futuros"` (CA-04).
  - El conteo de colecciones usa solo elementos `active=True` (los inactivos no cumplen).
  - "Control documental mínimo **según transición**": decisión confirmada (Q-3) — la regla de
    `signers` solo aplica como precondición de la transición a `GENERADO` (es el único punto
    del ciclo donde las firmas pueden existir: ADR-007 permite registrarlas en
    `APROBADO`/`GENERADO`); en el dry-run base (`target_state=None`, p.ej. BORRADOR) no se
    exigen firmas. `REVISO` no se exige (coherente con el wizard, que solo obliga
    `ELABORO`/`AUTORIZO`). Reflejado en la spec (reglas de negocio).

**Maquina de estados** (en `requirement.py`, ajuste mínimo):

- Decisión Q-1 (confirmada): el mapa `_ALLOWED_TRANSITIONS` **se mantiene tal cual**, con las
  retransiciones `EN_REVISION→BORRADOR` y `VALIDADO→EN_REVISION`; la SPEC-005 se corrigió para
  declarar esos retrocesos permitidos (coherencia con SPEC-002 y con
  `tests/domain/test_requirement.py`, que hoy los asierta y no se modifica). Trabajo nuevo:
  añadir `allowed_transitions(status) -> frozenset[RequirementStatus]` como acceso publico
  para la API y las pruebas.
- `change_status(target)` y `InvalidStateTransitionError` permanecen como mecanismo de
  rechazo del dominio; el caso de uso de transición los traduce al resultado estructurado.

### Casos de uso (`app/application/use_cases/requirement/`)

| Modulo | Caso de uso | Responsabilidad (RF/CA) |
|---|---|---|
| `validate_requirement_version.py` (nuevo) | `ValidateRequirementVersion` | `repo.get(id)`, verifica `version_by_id(vid)` (sino `VersionNotFoundError`), ejecuta `validate_requirement(..., target_state=...)` y devuelve `ValidationResult`. **No persiste** (RF-05, RF-09, CA-01/CA-02/CA-09) |
| `transition_requirement_state.py` (nuevo) | `TransitionRequirementState` | `repo.get(id)`; parsea `a_estado` (string desconocido → resultado invalido, `unknown_target_state`, sin excepción); si la transición es de avance (`BORRADOR→EN_REVISION`, `EN_REVISION→VALIDADO`, `VALIDADO→APROBADO`, `APROBADO→GENERADO`) ejecuta primero `validate_requirement(target_state=...)` y, si hay errores, devuelve `transicion_valida=false` con ellos (sin persistir); si el mapa la permite, aplica `requirement.change_status` y `repo.save`; devuelve `estado_anterior`/`estado_actual` (RF-06, CA-05/CA-06/CA-07). Cancelaciones: sin validación integral previa. `motivo`/`actor_id`: aceptados, logueados, no persistidos (deuda) |

- Resultado de aplicación `TransitionOutcome` (frozen dataclass): `previous_status`,
  `current_status`, `is_valid: bool`, `errors: tuple[ValidationIssue, ...]`.
- El caso de uso **no lanza** `InvalidStateTransitionError` al cliente de este endpoint: el
  rechazo se expresa en el resultado (CA-05 exige `400` **y** `transicion_valida=false` en el
  cuerpo). Decisiones Q-2/Q-4 (confirmadas): `400` **solo** en `/transicionar`; el manejo
  global 409 de `InvalidStateTransitionError` se conserva para el endpoint legacy
  `POST /estado`, que se mantiene como alias.
- `ChangeStatus` (SPEC-003) queda intacto; se marca como legacy en `doc/technical/api.md`.

## Puertos y adaptadores afectados

- **Puertos**: ninguno nuevo ni modificado. `ValidateRequirementVersion` y
  `TransitionRequirementState` dependen solo de `RequirementRepository.get/save` ya
  existentes; la validación es computo puro sobre el agregado, no requiere consultas
  adicionales ni proyecciones.
- **Adaptadores**: ningun cambio en `infrastructure/` (sin SQL nueva, sin mapper nuevo: el
  estado ya se persiste).
- **Cableado** (`app/api/dependencies.py`): añadir
  `get_validate_requirement_version_use_case` y `get_transition_requirement_state_use_case`
  siguiendo el patron de las fabricas existentes (puertos por `Depends` para que los tests
  puedan sustituirlos).

## API (endpoints, contratos, errores)

### Esquemas (`app/api/schemas/validation.py`, nuevo)

- `ValidationErrorSchema { path: str, codigo: str, mensaje: str, seccion: str }` con
  `from_domain(issue: ValidationIssue)` (traduce dominio inglés → API español, patron de los
  demas esquemas).
- `ValidationResultResponse { valido: bool, errores: list[ValidationErrorSchema], advertencias: list[ValidationErrorSchema] }`
  con `from_domain(result: ValidationResult)`.
- `ValidationRequest { a_estado: str | None = None }` — body opcional del dry-run: permite
  evaluar tambien el "control documental según transición" para una transición planeada
  (RF-02); sin body → solo reglas base (RF-05/RF-09).
- `StateTransitionRequest { a_estado: str, motivo: str | None = None, actor_id: int | None = None }`
  — `a_estado` tipado como `str` (no enum) para poder devolver `400` con
  `unknown_target_state` segun CA-07 en vez del `422` de Pydantic.
- `StateTransitionResponse { estado_anterior: str, estado_actual: str, transicion_valida: bool, errores: list[ValidationErrorSchema] = [] }`
  con `from_outcome(outcome: TransitionOutcome)`.

### Routers

`app/api/routers/validation.py` (nuevo; prefijo `/api/v1`, tag `validacion`), sin logica de
negocio (valida entrada, invoca caso de uso, serializa):

| Metodo | Ruta | Caso de uso | Exito | Fallo |
|---|---|---|---|---|
| POST | `/requerimientos/{id}/versiones/{vid}/validar` | `ValidateRequirementVersion` | 200 `ValidationResultResponse` (incluso con `valido=false`: no es error) | 404 envelope `requirement_not_found` / `version_not_found` |
| POST | `/requerimientos/{id}/transicionar` | `TransitionRequirementState` | 200 `StateTransitionResponse` (`transicion_valida=true`) | 400 con cuerpo `StateTransitionResponse` (`transicion_valida=false`, `errores=[...]`); 404 envelope si el requerimiento no existe |

- El `400` de transición **no** usa el envelope global sino el cuerpo
  `StateTransitionResponse`: CA-05 exige `400` y `transicion_valida=false` simultaneamente,
  y la lista de errores por sección/campo (RF-10) es mas accionable en ese formato. Decision
  documentada en `doc/technical/api.md` y en la sección de riesgos.
- Codigos dentro de `errores[]`: `unknown_target_state`, `invalid_transition`
  (mapa de máquina de estados), `required_field`, `min_active_items`,
  `future_requirements_missing`, `signatures_missing`.
- Se mantiene `POST /requerimientos/{id}/estado` (SPEC-003) sin cambios de contrato, como
  alias legacy documentado hacia `/transicionar` (decisión Q-4).

### Cambios de contrato a documentar

- `doc/technical/api.md`: nuevos endpoints, esquemas `ValidationResultResponse`/
  `StateTransitionResponse`, nota de deprecation de `/estado` y matiz del `400` de
  `/transicionar` frente al envelope general.

## Frontend (pantallas, componentes, estado)

**Sin cambios requeridos.** Los criterios de aceptación de esta spec son de API y el alcance
explicito (sección "Incluye") es backend. Ademas, el espejo cliente de las reglas ya existe
y no se modifica:

- `frontend/src/features/wizard/wizardSteps.ts` reproduce la validación de forma por paso,
  incluida la condicional de requisitos futuros (RF-03/RF-04 a nivel cliente) y los
  obligatorios de control documental (ELABORO/AUTORIZO).
- `frontend/src/features/wizard/steps/Step12DocumentControl.tsx` captura `signers` en estado
  local sin persistir (coherente con ADR-007 y con la interpretación de control documental).
- `frontend/src/hooks/useAutosave.ts` y el reducer no intervienen en validación ni
  transiciones.

Trabajo diferido recomendado (fuera de esta spec; requerirá spec propia o ampliación):
cliente HTTP `frontend/src/api/validation.ts` (`validateVersion`, `transitionRequirement`),
tipos espejo `ValidationResult`/`StateTransitionResponse`, boton "Validar" en
`Step13Review` y mostrado de `errores[]` con salto a la sección afectada; acciones de
transición en el listado/detalle. Sin dependencias nuevas.

## Docker / configuracion

Sin cambios de imagenes, `docker-compose.yml` ni variables de entorno. La validación y la
transición usan la misma conexion Oracle y el mismo `create_app()`. `AI_PROVIDER=none`
sigue vigente (SPEC-005 no incorpora IA).

## Estrategia de pruebas

- **Dominio** (`tests/domain/`):
  - `test_validation.py` (nuevo): cabecera obligatoria (CA-01), completo → `is_valid`
    (CA-02), RF-03 sin errores con `aplica=false` (CA-03), RF-04 error en "Requisitos
    futuros" (CA-04), conteo solo de activos, advertencia de consistencia, control
    documental solo con `target_state=GENERADO`, campos de cada error (`path`, `codigo`,
    `seccion`) (CA-10).
  - `test_requirement.py` (sin cambios: Q-1 resuelto a favor del codigo actual); se añade
    cobertura de `allowed_transitions()` incluyendo los retrocesos `EN_REVISION→BORRADOR` y
    `VALIDADO→EN_REVISION`.
- **Casos de uso** (`tests/application/`, con `InMemoryRequirementRepository` de
  `tests/application/fakes.py`):
  - `test_validate_requirement_version.py` (nuevo): dry-run no persiste ni cambia estado
    (CA-09); version inexistente → `VersionNotFoundError`.
  - `test_transition_requirement_state.py` (nuevo): avance valido persiste
    `estado_anterior/estado_actual` (CA-06); `BORRADOR→APROBADO` → `transicion_valida=false`
    con `invalid_transition` (CA-05); `a_estado` desconocido → `unknown_target_state`
    (CA-07); avance bloqueado por validación integral fallida (precondición RF-02);
    cancelación sin validación; `motivo`/`actor_id` aceptados sin efecto en persistencia.
  - Regresión: pruebas existentes de firmas (`signature_not_allowed`, CA-08) sin tocar.
- **API** (`tests/api/`, con `dependency_overrides` + fakes, patron de
  `tests/api/test_requirements.py`):
  - `test_validation.py` (nuevo): CA-01 (`valido=false` + errores por sección/campo con
    `path`/`codigo`/`mensaje`/`seccion`, CA-10), CA-02 (`valido=true`), 404 de
    requerimiento/version, dry-run sin cambio de estado (CA-09).
  - `test_transition.py` (nuevo): CA-05 (`400` + `transicion_valida=false`), CA-06 (200 y
    `RequirementResponse.refleja` el nuevo estado via `GET`), CA-07 (`400` con
    `unknown_target_state`), 404.
- **Integracion** (`tests/integration/`): sin pruebas nuevas (no hay DDL ni SQL nueva); la
  persistencia de `ESTADO` ya esta cubierta por `test_requirement_repository.py` /
  `test_mappers.py` existentes.
- **E2E Playwright**: no aplica (sin cambios de frontend en esta spec).
- **Calidad**: `ruff check .`, `mypy --strict app`, `python -m pytest` sin errores;
  `GET /openapi.json` expone los endpoints nuevos.

## Trazabilidad RF -> diseño

| RF | Elemento de diseño | Pruebas |
|---|---|---|
| RF-01 | `RequirementStatus` (existente) + mapa `_ALLOWED_TRANSITIONS` (sin cambios) + `allowed_transitions()` | `tests/domain/test_requirement.py` (retrocesos y `allowed_transitions`) |
| RF-02 | `domain/requirement/validation.py::validate_requirement` (tabla de reglas) | `tests/domain/test_validation.py`, `tests/api/test_validation.py` (CA-01, CA-02) |
| RF-03 | Regla `future_requirements_applies=false` en `validate_requirement` | `tests/domain/test_validation.py` (CA-03) |
| RF-04 | Regla `future_requirements_applies=true` en `validate_requirement` | `tests/domain/test_validation.py` (CA-04) |
| RF-05 | `POST /requerimientos/{id}/versiones/{vid}/validar` + `ValidationResultResponse` | `tests/api/test_validation.py` |
| RF-06 | `POST /requerimientos/{id}/transicionar` + `StateTransitionRequest/Response` + `TransitionRequirementState` | `tests/application/test_transition_requirement_state.py`, `tests/api/test_transition.py` (CA-06) |
| RF-07 | Mapa de transiciones + resultado `invalid_transition`/`unknown_target_state` con `400` | CA-05, CA-07 |
| RF-08 | Sin cambios: `ensure_signable` (ADR-007) | Regresión `tests/api/test_requirements.py` (CA-08) |
| RF-09 | `ValidateRequirementVersion` sin `repo.save` | CA-09 (`tests/application` y `tests/api`) |
| RF-10 | `ValidationIssue{path, code, message, section}` → `ValidationErrorSchema` | CA-10 |

## Riesgos y decisiones (ADRs relacionados)

- **ADR-002 (hexagonal)**: validador y transición en dominio puro; application orquesta puertos;
  la `api` solo serializa; sin SQL nueva.
- **ADR-005/ADR-007 (firmas/estados)**: el validador no exige firmas en BORRADOR (imposibles
  de persistir hasta APROBADO); el control documental se exige solo como precondición de
  `APROBADO→GENERADO`; las transiciones no crean firmas (CA-08 se cubre por regresión).
- **400 vs 409 en transicion invalida** (Q-2, decidido): SPEC-005 (CA-05/CA-07) exige `400`;
  SPEC-003 y `doc/technical/api.md` usan `409 invalid_state_transition` para el endpoint
  legacy `POST /estado`. Decision: `400` **solo** en `/transicionar` (contrato nuevo de la
  spec) y se conserva `409` en el handler global para `/estado` (compatibilidad). Riesgo de
  inconsistencia percibida entre ambos endpoints — documentado en `doc/technical/api.md`.
- **Retrocesos en el mapa de transiciones** (Q-1, decidido): la SPEC-005 se corrigio para
  declarar `EN_REVISION→BORRADOR` y `VALIDADO→EN_REVISION` permitidos (coherente con
  SPEC-002 y con el codigo/pruebas existentes). El mapa de dominio no cambia.
- **Control documental "según transición"** (Q-3, decidido): firmas `ELABORO`/`AUTORIZO`
  exigidas solo como precondición de `APROBADO→GENERADO`; no se exigen en BORRADOR ni en el
  dry-run base (el wizard no persiste esos nombres hasta estados avanzados).
- **Endpoint legacy `POST /estado`** (Q-4, decidido): se mantiene como alias con su contrato
  y `409` originales; se documenta hacia `/transicionar`.
- **`motivo`/`actor_id` no persistidos** (Q-5, decidido): sin tabla de historial de
  transiciones; se aceptan en el contrato, se registran en log y se ignoran en persistencia.
  Deuda documentada para una futura spec de auditoría.
- **Dry-run permite validar versiones congeladas**: util para revision historica; el caso de
  uso solo exige que la version exista en el agregado (404 en otro caso).
- **Sin dependencias nuevas**: solo stdlib + stack existente (FastAPI/Pydantic v2).

## Decisiones resueltas (Q-1..Q-5)

1. **Q-1 — Retrocesos**: se mantienen `EN_REVISION→BORRADOR` y `VALIDADO→EN_REVISION`; se
   corrigio la spec (reglas de negocio) y el codigo de dominio/pruebas no cambia.
2. **Q-2 — Codigo HTTP**: `400` en el nuevo `/transicionar` (exigido por CA-05/CA-07);
   `409` se conserva en el legacy `POST /estado`.
3. **Q-3 — Control documental**: firmas `ELABORO`/`AUTORIZO` exigidas solo como precondición
   de `APROBADO→GENERADO`; en el dry-run base no se exigen.
4. **Q-4 — Endpoint legacy**: `POST /requerimientos/{id}/estado` se mantiene como alias con
   contrato y `409` originales, documentado hacia `/transicionar`.
5. **Q-5 — `motivo`/`actor_id`**: se aceptan y se loguean sin persistir; deuda documentada
   para una futura spec de auditoría de transiciones.

No quedan preguntas abiertas en esta spec.
