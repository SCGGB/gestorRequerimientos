# Verify - SPEC-005: Validacion integral y maquina de estados

- Fecha de verificacion: 2026-10-19
- Spec: `specs/SPEC-005-validacion-integral-y-maquina-de-estados/spec.md` (Estado: Aprobado)
- Revisor: agente `reviewer` (revision por criterios de aceptacion)
- Alcance verificado: backend (dominio + application + api) + documentacion `doc/technical/api.md`

## Comandos ejecutados

Todos desde `backend/`, con la imagen de desarrollo cacheada (el host es Python 3.15 y no
tiene `ruff`/`mypy`, por lo que se uso el flujo de AGENTS.md):

```
docker run --rm -v "<repo>/backend:/app" -w /app gestor-req-dev sh -c "ruff check . && mypy --strict app && python -m pytest -q -p no:cacheprovider"
```

Resultado:

- `ruff check .` -> All checks passed!
- `mypy --strict app` -> Success: no issues found in 71 source files
- `python -m pytest -q` -> 124 passed (2 warnings de deprecacion de Starlette, no bloqueantes)
- `GET /openapi.json` expone `/api/v1/requerimientos/{requirement_id}/versiones/{version_id}/validar`
  y `/api/v1/requerimientos/{requirement_id}/transicionar`.

## Resultado por criterio de aceptacion

| CA | Estado | Evidencia |
|---|---|---|
| CA-01 | Cumple | `app/domain/requirement/validation.py::validate_requirement` (datos generales, necesidad actual, contexto, usuarios, colecciones). Pruebas: `tests/domain/test_validation.py::test_missing_header_reports_errors_per_field`; `tests/api/test_validation.py::test_validation_reports_errors_by_section` (`valido=false`, paths `datos_generales.titulo`, `necesidad_actual`, `objetivos`). |
| CA-02 | Cumple | `test_validation.py::test_complete_requirement_is_valid` (`is_valid is True`, `errors == ()`); `tests/api/test_validation.py::test_validation_returns_valid_for_complete_version` (`valido=true`, `errores=[]`). |
| CA-03 | Cumple | `validation.py::_validate_future_requirements` (`applies=False` -> sin error); `test_validation.py::test_future_requirements_not_applying_is_valid`; `tests/api/test_validation.py::test_validation_future_requirements_not_applying_has_no_errors`. |
| CA-04 | Cumple | `validation.py::_validate_future_requirements` emite `future_requirements_missing`, `path="requisitos_futuros_texto"`, `section="Requisitos futuros"`; `test_validation.py::test_future_requirements_applying_without_content_is_rejected`; `tests/api/test_validation.py::test_validation_future_requirements_applying_requires_content`. |
| CA-05 | Cumple | `TransitionRequirementState.execute` valida contra `allowed_transitions`; `app/api/routers/validation.py::transition_state` fija `400` cuando `not outcome.is_valid`. Pruebas: `tests/application/test_transition_requirement_state.py::test_skipped_transition_is_invalid_and_does_not_persist`; `tests/api/test_transition.py::test_forbidden_transition_returns_400_with_body` (400 + `transicion_valida=false` + `invalid_transition` + estado sin cambios). |
| CA-06 | Cumple | `TransitionRequirementState` aplica `change_status` + `repo.save` y devuelve `previous_status`/`current_status`; `StateTransitionResponse.from_outcome`. Pruebas: `test_transition_requirement_state.py::test_valid_advance_persists_new_status`; `tests/api/test_transition.py::test_valid_transition_returns_200_and_persists` (200, `estado_anterior=BORRADOR`, `estado_actual=EN_REVISION`, verificado por `GET`). |
| CA-07 | Cumple | `_parse_target` devuelve `None` -> `unknown_target_state` sin excepcion; router responde `400`. Pruebas: `test_transition_requirement_state.py::test_unknown_target_state_is_rejected`; `tests/api/test_transition.py::test_unknown_target_state_returns_400`. |
| CA-08 | Cumple | Sin cambios en firmas (`ensure_signable`/`SignatureNotAllowedError`). Regresion: `tests/api/test_routing.py` (`signature_not_allowed`) y `tests/api/test_transition.py::test_legacy_status_endpoint_keeps_409` (endpoint legacy `/estado` conserva `409 invalid_state_transition`). `git diff` confirma sin cambios en `app/infrastructure/`. |
| CA-09 | Cumple | `ValidateRequirementVersion.execute` no llama a `repo.save`. Pruebas: `tests/application/test_validate_requirement_version.py::test_validate_returns_result_without_persisting`; `tests/api/test_validation.py::test_validation_does_not_change_state` (estado sigue `BORRADOR` tras `/validar`). |
| CA-10 | Cumple | `ValidationErrorSchema { path, codigo, mensaje, seccion }` + `from_domain`. Pruebas: `test_validation.py::test_issue_exposes_path_code_message_and_section`; `tests/api/test_validation.py::test_validation_reports_errors_by_section` (assert `set(error) == {path, codigo, mensaje, seccion}`). |

Resumen: **10/10 criterios Cumple.**

## Requisitos funcionales

| RF | Estado | Evidencia |
|---|---|---|
| RF-01 | Cumple | `app/domain/requirement/enums.py::RequirementStatus` con los 6 estados; `allowed_transitions()` en `requirement.py`. |
| RF-02 | Cumple | `validate_requirement` cubre header, necesidad, contexto, usuarios/permisos, colecciones activas, requisitos futuros y control documental segun transicion. |
| RF-03 / RF-04 | Cumple | `_validate_future_requirements` (rama `applies` / `else`). |
| RF-05 | Cumple | `POST /api/v1/requerimientos/{id}/versiones/{vid}/validar` -> `ValidationResultResponse { valido, errores[], advertencias[] }`. |
| RF-06 | Cumple | `POST /api/v1/requerimientos/{id}/transicionar` -> `StateTransitionResponse`; body `StateTransitionRequest { a_estado, motivo?, actor_id? }`. |
| RF-07 | Cumple | Mapa `_ALLOWED_TRANSITIONS` + `allowed_transitions`; transicion no permitida -> `400` con `errores[].codigo = invalid_transition`. |
| RF-08 | Cumple | Firmas solo validadas (no creadas); `ensure_signable` intacto (ADR-007). |
| RF-09 | Cumple | Validacion dry-run ejecutable en `BORRADOR` sin persistir. |
| RF-10 | Cumple | `ValidationIssue` con `path` + `section` accionables por error. |

## Arquitectura hexagonal (ADR-002)

- `app/domain/requirement/validation.py` es Python puro: importa solo `dataclasses` y modulos de
  `app.domain.requirement.*`; sin FastAPI, SQLAlchemy ni IA/DOCX.
- Casos de uso en `app/application/use_cases/requirement/` dependen solo del puerto
  `RequirementRepository` (`get`/`save`); no se anadieron puertos/adaptadores.
- La API solo valida entrada, invoca el caso de uso y serializa; sin logica de negocio en routers.
- Sin migraciones Alembic nuevas ni cambios en `app/infrastructure/` (confirmado por `git diff`).
- Sin dependencias nuevas en `pyproject.toml`.

## Hallazgos / deuda tecnica

1. **Plan vs implementacion - `ValidationRequest.a_estado` — Corregido.** `ValidationRequest.a_estado`
   ahora es `str | None` (contrato del plan) y `ValidateRequirementVersion` parsea el valor con
   `parse_status`; un estado desconocido devuelve `ValidationResult` con `unknown_target_state`
   (`path="a_estado"`, `section="Maquina de estados"`) en lugar del `422` de Pydantic.
   Evidencia: `tests/application/test_validate_requirement_version.py::test_validate_unknown_target_state_returns_structured_error`;
   `tests/api/test_validation.py::test_validation_unknown_target_state_returns_structured_error` (200,
   `valido=false`).
2. **`version_date` no validado explicitamente — Corregido.** `_validate_general_data` valida
   `version_date` con `_require_date` (`required_field`, `path="datos_generales.fecha_version"`,
   `section="Datos generales"`), protegiendo el limite de persistencia aunque el dominio lo tipe como
   `date`. Evidencia: `tests/domain/test_validation.py::test_missing_version_date_is_reported`.
3. **`motivo`/`actor_id` no persistidos** (decision Q-5): se aceptan y se registran en log
   (`logger.info`), sin tabla de historial. Deuda documentada en `doc/technical/api.md` para una
   futura spec de auditoria de transiciones. No se corrige en SPEC-005 (requiere modelo/migracion).
4. **Doble endpoint de estado**: `/transicionar` (`400`) coexiste con el alias legacy `/estado`
   (`409`). Inconsistencia percibida entre ambos codigos HTTP; documentada (Q-2/Q-4) y sin ruptura
   de compatibilidad. No se corrige en SPEC-005 (cambio de contrato legacy).
5. **Cobertura de tests duplicada — Corregido.** Los helpers `_complete_version`/`_seed` se
   centralizaron en `tests/factories.py` (`complete_version`, `requirement_with`) y los cuatro
   archivos de prueba los reutilizan, eliminando la duplicacion.

## Gaps de pruebas detectados

- **Resuelto.** Se agrego cobertura de API del dry-run con `a_estado="GENERADO"`:
  `tests/api/test_validation.py::test_validation_with_target_generado_requires_document_control`
  (exige `signatures_missing` en "Control documental") y
  `test_validation_with_target_generado_and_signatures_is_valid`.
- Sin prueba de integracion que confirme la persistencia de `ESTADO` para `/transicionar` (el plan
  lo declara fuera de alcance: la persistencia ya esta cubierta por las pruebas de repositorio
  existentes). Se acepta como justificado.

## Conclusion

SPEC-005 **Cumple** sus 10 criterios de aceptacion con evidencia reproducible. Lint (`ruff`), tipos
(`mypy --strict`) y las 124 pruebas (`pytest`) pasan en la imagen de desarrollo. La implementacion
respeta la arquitectura hexagonal, no introduce migraciones ni dependencias, y las firmas (ADR-007)
permanecen sin cambios. Los hallazgos 1, 2 y 5 y el gap de pruebas del dry-run con `a_estado` fueron
corregidos; los puntos 3 y 4 quedan como deuda aceptada por decision de alcance (requieren modelo de
auditoria y cambio de contrato legacy respectivamente).
