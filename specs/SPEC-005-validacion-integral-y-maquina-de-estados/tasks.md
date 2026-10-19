# Tareas - SPEC-005

> Tareas atomicas, ordenadas por dependencia. Cada una referencia el requisito funcional (RF) y el
> criterio de aceptacion (CA) que cubre. Spec **solo backend** (dominio + application + api): no toca
> DOCX/PDF (SPEC-007), vista previa (SPEC-006), autorizacion por roles (SPEC-008), firma electronica ni
> frontend.
>
> **Modelo de datos Oracle / migraciones Alembic: no aplica.** El estado ya persiste en
> `REQ_REQUERIMIENTO.ESTADO` (migracion `0002_modelo_requerimiento`) y las firmas en `REQ_FIRMA`; la
> validacion es computo puro sobre el agregado. No se crea tabla/columna/indice/migracion (ver plan,
> seccion "Modelo de datos Oracle"). `motivo`/`actor_id` se aceptan pero no se persisten (deuda Q-5).
>
> Convencion de commits: un commit al cierre de cada fase con prefijo `SPEC-005:`.

## Fase A - Dominio puro (sin FastAPI/SQLAlchemy)

Commit de fase: `SPEC-005: dominio validador integral y acceso a transiciones`

- [ ] **T-01 — Tipos de resultado de validacion** (RF-02, RF-10, CA-10)
  - Nuevo `backend/app/domain/requirement/validation.py` (Python puro): `ValidationIssue` (frozen
    dataclass: `path`, `code`, `message`, `section`) y `ValidationResult` (frozen dataclass:
    `errors: tuple[ValidationIssue, ...]`, `warnings: tuple[ValidationIssue, ...]`, propiedad
    `is_valid = not errors`).
  - Sin imports de FastAPI, SQLAlchemy ni librerias de IA/DOCX; codigos en ingles, mensajes/secciones en espanol.

- [ ] **T-02 — Validador integral de la version vigente** (RF-02, RF-03, RF-04, CA-01, CA-02, CA-03, CA-04)
  - `validate_requirement(requirement: Requirement, *, target_state: RequirementStatus | None = None) -> ValidationResult`.
  - Lee la version vigente (`current_version()`); si no existe, error estructurado `no_current_version`.
  - Reglas base (tabla del plan): Datos generales (`title`, `change_type_id`, `system`,
    `document_version`, `version_date` → `required_field`), Necesidad actual (`current_need`),
    Contexto (`context_description`), Usuarios y permisos (`users_permissions`), colecciones con
    `>= 1` elemento **activo** (`objetivos`, `consideraciones`, `beneficios`, `restricciones`,
    `volumetria`, `riesgos` → `min_active_items`).
  - RF-03: `future_requirements_applies=false` → no se emite error por texto vacio ni lista vacia (CA-03).
  - RF-04: `future_requirements_applies=true` → exige texto no vacio **o** `>= 1` activo; si falta,
    error `future_requirements_missing` en `path="requisitos_futuros_texto"`,
    `section="Requisitos futuros"` (CA-04).
  - Consistencia: `aplica=false` con texto o elementos activos → **advertencia** `future_requirements_orphan`
    (no bloquea).
  - Cada error incluye `path`, `code`, `message`, `section` (CA-01, CA-02, CA-10).

- [ ] **T-03 — Control documental condicionado a la transicion** (RF-02, RF-08, CA-08)
  - En `validation.py`: si `target_state = GENERADO`, exigir firmas `ELABORO` y `AUTORIZO` con
    `nombre` no vacio sobre la version vigente → error `signatures_missing`
     (`path="signers.ELABORO.nombre"`/`signers.AUTORIZO.nombre`, seccion "Control documental").
  - Con `target_state=None` (dry-run base, p.ej. BORRADOR) **no** se exigen firmas (decision Q-3);
    `REVISO` no se exige (coherente con el wizard).
  - No se crean firmas: solo se valida su existencia (ADR-007).

- [ ] **T-04 — Acceso publico al mapa de transiciones** (RF-01, RF-07, CA-05, CA-07)
  - Ajuste minimo en `backend/app/domain/requirement/requirement.py`: agregar
    `allowed_transitions(status: RequirementStatus) -> frozenset[RequirementStatus]` sobre
    `_ALLOWED_TRANSITIONS`.
  - Mantener **sin cambios** el mapa (incluye retrocesos `EN_REVISION→BORRADOR` y
    `VALIDADO→EN_REVISION`; decision Q-1) y conservar `change_status(target)` /
    `InvalidStateTransitionError` como mecanismo de rechazo del dominio.

- [ ] **T-05 — Pruebas unitarias del validador** (CA-01, CA-02, CA-03, CA-04, CA-10)
  - Nuevo `backend/tests/domain/test_validation.py`: cabecera incompleta → `is_valid=false` con
    errores por seccion/campo (CA-01); completo → `is_valid=true` (CA-02); `aplica=false` sin errores
    (CA-03); `aplica=true` sin texto/activos → error en "Requisitos futuros" (CA-04); conteo solo de
    activos; advertencia de consistencia; control documental solo con `target_state=GENERADO`;
    estructura de cada error (`path`, `codigo`, `seccion`) (CA-10). Sin base de datos.

- [ ] **T-06 — Cobertura de `allowed_transitions()`** (RF-01, CA-06)
  - Ampliar `backend/tests/domain/test_requirement.py` (sin alterar los tests existentes de
    retrocesos) con aserciones de `allowed_transitions()` incluyendo
    `EN_REVISION→BORRADOR` y `VALIDADO→EN_REVISION`.

## Fase B - Casos de uso (application)

Commit de fase: `SPEC-005: casos de uso validar version y transicionar estado`

- [ ] **T-07 — `ValidateRequirementVersion`** (RF-05, RF-09, CA-09)
  - Nuevo `backend/app/application/use_cases/requirement/validate_requirement_version.py`: `repo.get(id)`
    (`RequirementNotFoundError`), verifica `version_by_id(vid)` (`VersionNotFoundError`), ejecuta
    `validate_requirement(..., target_state=...)` y devuelve `ValidationResult`. **No persiste** (dry-run).
  - Depende solo del puerto `RequirementRepository.get/save` existente; sin puertos ni adaptadores nuevos.

- [ ] **T-08 — `TransitionRequirementState`** (RF-06, RF-07, CA-05, CA-06, CA-07)
  - Nuevo `backend/app/application/use_cases/requirement/transition_requirement_state.py`:
    `repo.get(id)`; parsea `a_estado` (`str` desconocido → `unknown_target_state`, sin excepcion);
    transicion no permitida por el mapa → `invalid_transition`; en avance
    (`BORRADOR→EN_REVISION`, `EN_REVISION→VALIDADO`, `VALIDADO→APROBADO`, `APROBADO→GENERADO`) ejecuta
    antes `validate_requirement(target_state=...)` y, con errores, devuelve `transicion_valida=false`
    sin persistir; si el mapa la permite, aplica `change_status` + `repo.save`.
  - Resultado `TransitionOutcome` (frozen dataclass): `previous_status`, `current_status`, `is_valid`,
    `errors`. El caso de uso **no lanza** `InvalidStateTransitionError` en este flujo.
  - `motivo`/`actor_id`: aceptados y logueados, **no persistidos** (deuda Q-5). Cancelaciones sin
    validacion integral previa.
  - No modifica `ChangeStatus` (SPEC-003), que queda como legacy (Q-4).

- [ ] **T-09 — Pruebas de `ValidateRequirementVersion`** (CA-09)
  - Nuevo `backend/tests/application/test_validate_requirement_version.py` (con
    `InMemoryRequirementRepository` de `tests/application/fakes.py`): dry-run no persiste ni cambia
    estado (CA-09); version inexistente → `VersionNotFoundError`.

- [ ] **T-10 — Pruebas de `TransitionRequirementState`** (CA-05, CA-06, CA-07)
  - Nuevo `backend/tests/application/test_transition_requirement_state.py`: avance valido persiste
    `estado_anterior/estado_actual` (CA-06); `BORRADOR→APROBADO` → `transicion_valida=false` con
    `invalid_transition` (CA-05); `a_estado` desconocido → `unknown_target_state` (CA-07); avance
    bloqueado por validacion integral fallida; cancelacion sin validacion; `motivo`/`actor_id` sin
    efecto en persistencia.

## Fase C - API y contrato

Commit de fase: `SPEC-005: endpoints /validar y /transicionar con esquemas`

- [ ] **T-11 — Esquemas de validacion y transicion** (RF-05, RF-06, RF-10, CA-10)
  - Nuevo `backend/app/api/schemas/validation.py`:
    `ValidationErrorSchema { path, codigo, mensaje, seccion }` con `from_domain(issue)`;
    `ValidationResultResponse { valido, errores[], advertencias[] }` con `from_domain(result)`;
    `ValidationRequest { a_estado: str | None = None }` (body opcional del dry-run);
    `StateTransitionRequest { a_estado: str, motivo: str | None, actor_id: int | None }` (`a_estado`
    como `str` para devolver `400`, no `422` de Pydantic);
    `StateTransitionResponse { estado_anterior, estado_actual, transicion_valida, errores[] }` con
    `from_outcome(outcome)`.
  - Traduccion dominio (ingles) ↔ API (espanol) siguiendo el patron de los esquemas existentes.

- [ ] **T-12 — Endpoint `POST /requerimientos/{id}/versiones/{vid}/validar`** (RF-05, RF-09, CA-01, CA-02, CA-09, CA-10)
  - Nuevo `backend/app/api/routers/validation.py` (prefijo `/api/v1`, tag `validacion`), sin logica de
    negocio: valida entrada, invoca `ValidateRequirementVersion`, serializa.
  - Exito `200 ValidationResultResponse` incluso con `valido=false` (no es error de HTTP); fallo
    `404` envelope `requirement_not_found` / `version_not_found`.

- [ ] **T-13 — Endpoint `POST /requerimientos/{id}/transicionar`** (RF-06, RF-07, CA-05, CA-06, CA-07)
  - En `validation.py`: `200 StateTransitionResponse` con `transicion_valida=true`; `400` con cuerpo
    `StateTransitionResponse` (`transicion_valida=false`, `errores=[...]`; codigos
    `unknown_target_state`, `invalid_transition`, `required_field`, `min_active_items`,
    `future_requirements_missing`, `signatures_missing`); `404` envelope si el requerimiento no existe.
  - El `400` usa el cuerpo de la respuesta (no el envelope global) por exigencia de CA-05 + RF-10
    (decision Q-2, documentada).

- [ ] **T-14 — Cableado y conservacion del endpoint legacy** (RF-07, CA-05, CA-08)
  - `backend/app/api/dependencies.py`: fabricas `get_validate_requirement_version_use_case` y
    `get_transition_requirement_state_use_case` con puertos por `Depends` (patron existente).
  - Registrar el router nuevo en `main.py`/`api/routers/__init__.py` y los esquemas en
    `api/schemas/__init__.py`. Mantener `POST /requerimientos/{id}/estado` (SPEC-003) y el handler
    global `409 invalid_state_transition` **sin cambios** (alias legacy, Q-4).

## Fase D - Documentacion

Commit de fase: `SPEC-005: documentar endpoints validar/transicionar en api.md`

- [ ] **T-15 — Actualizar `doc/technical/api.md`** (RF-05, RF-06, RF-07, RF-08, RF-09, RF-10)
  - Documentar `POST /requerimientos/{id}/versiones/{vid}/validar` (dry-run, 200 aunque `valido=false`)
    y `POST /requerimientos/{id}/transicionar`; esquemas `ValidationResultResponse`,
    `ValidationErrorSchema`, `StateTransitionRequest`/`StateTransitionResponse`.
  - Nota de deprecation/alias de `POST /requerimientos/{id}/estado` hacia `/transicionar` y matiz del
    `400` de `/transicionar` frente al `409` del envelope general (Q-2/Q-4).
  - Registro de la deuda Q-5 (`motivo`/`actor_id` aceptados y logueados, no persistidos) y nota de que
    no hay cambios de modelo/migracion.

## Fase E - Pruebas de API

Commit de fase: `SPEC-005: pruebas de API de validacion y transicion`

- [ ] **T-16 — Pruebas de `POST /validar`** (CA-01, CA-02, CA-09, CA-10)
  - Nuevo `backend/tests/api/test_validation.py` (`TestClient` + `dependency_overrides` con fakes,
    patron de `tests/api/test_requirements.py`): `valido=false` con `path`/`codigo`/`mensaje`/`seccion`
    por error (CA-01, CA-10), `valido=true` (CA-02), `404` de requerimiento/version, dry-run sin cambio
    de estado (CA-09).

- [ ] **T-17 — Pruebas de `POST /transicionar`** (CA-05, CA-06, CA-07)
  - Nuevo `backend/tests/api/test_transition.py`: `400` con `transicion_valida=false` (CA-05); `200` y
    estado reflejado via `GET` (CA-06); `400` con `unknown_target_state` (CA-07); `404`.

- [ ] **T-18 — Regresion de compatibilidad** (CA-08)
  - Confirmar (sin modificar) que las pruebas existentes de firmas (`signature_not_allowed`) y del
    endpoint legacy `POST /estado` (`409`) siguen en verde; agregar el caso minimo necesario solo si
    falta cobertura del alias.

## Fase F - Calidad

Commit de fase: `SPEC-005: calidad (ruff, mypy, pytest)`

- [ ] **T-19 — Lint, tipos y pruebas** (RF-02..RF-09)
  - Desde `backend/`: `ruff check .`, `mypy --strict app`, `python -m pytest` en verde. Confirmar que
    `GET /openapi.json` expone los endpoints nuevos y que la app arranca sin IA (`AI_PROVIDER=none`).

- [ ] **T-20 — Verificacion de alcance** (RF-01, RF-08)
  - Confirmar que no hay cambios de modelo Oracle ni migraciones Alembic nuevas
    (`alembic upgrade head` sin revisiones pendientes), que `infrastructure/` no se modifica y que no se
    incorporaron dependencias nuevas.

## Trazabilidad CA → Tareas

| CA | Tareas |
|---|---|
| CA-01 | T-02, T-05, T-12, T-16 |
| CA-02 | T-02, T-05, T-12, T-16 |
| CA-03 | T-02, T-05, T-16 |
| CA-04 | T-02, T-05, T-16 |
| CA-05 | T-04, T-08, T-10, T-13, T-14, T-17 |
| CA-06 | T-06, T-08, T-10, T-13, T-17 |
| CA-07 | T-04, T-08, T-10, T-13, T-17 |
| CA-08 | T-03, T-14, T-18 |
| CA-09 | T-07, T-09, T-12, T-16 |
| CA-10 | T-01, T-02, T-05, T-11, T-12, T-16 |
