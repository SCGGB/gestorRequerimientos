# Verificacion - SPEC-002: Modelo de dominio y persistencia del requerimiento

- Spec: `spec.md` (Estado: **Approved**, 2026-10-13)
- Plan / Tareas: `plan.md`, `tasks.md`
- Fecha de verificacion: 2026-10-14
- Rama: `spec/SPEC-002-modelo-dominio-requerimiento`
- Entorno: host sin Python 3.12; corridas en contenedor `python:3.12-slim` (segun `AGENTS.md`). Oracle via Testcontainers.

## Evidencia ejecutada

**E1 - Lint, tipos y unitarias (sin Docker):**

```
docker run --rm -v "${PWD}:/app" -w /app python:3.12-slim sh -c "pip install -q -e '.[dev]' && ruff check . && mypy --strict app && python -m pytest -p no:cacheprovider -q"
```

- `ruff check .` -> All checks passed!
- `mypy --strict app` -> Success: no issues found in 39 source files (nota: unused section(s): module = ['alembic.*', 'testcontainers.*'], no es error)
- `python -m pytest` -> 43 passed, 14 deselected, 1 warning in 1.79s

**E2 - Integracion (Docker + Testcontainers Oracle):**

```
docker run --rm -v "${PWD}:/app" -v /var/run/docker.sock:/var/run/docker.sock -w /app -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal python:3.12-slim sh -c "pip install -q -e '.[dev]' && python -m pytest -m integration tests/integration -p no:cacheprovider -q"
```

- 14 passed, 1 warning in 15.81s (incluye `test_database_engine` (2), `test_migration` (2), `test_migration_requerimiento` (5), `test_requirement_repository` (5))

## Resultado por criterio

| Criterio | Resultado | Evidencia |
|---|---|---|
| CA-01 | Cumple | `backend/alembic/versions/0002_modelo_requerimiento.py`; E2 `test_migration_requerimiento.py::test_upgrade_creates_requerimiento_schema` (13 tablas de `EXPECTED_TABLES` + columnas de auditoria `AUDIT_COLUMNS` en cada tabla) y `::test_downgrade_drops_requerimiento_schema` (sin residuos tras `downgrade` a `base`) -> PASSED |
| CA-02 | Cumple | E2 `test_migration_requerimiento.py::test_upgrade_seeds_catalogs`: `REQ_TIPO_CAMBIO.CODIGO` = {NUEVA_FUNCIONALIDAD, CORRECCION, REPORTE, INTEGRACION, BASE_DATOS, MEJORA_TECNICA} y `REQ_CARGO` con `PREDETERMINADO='S'` para {ELABORO, REVISO, AUTORIZO} -> PASSED; semilla en `_seed_change_types`/`_seed_positions` de `0002_modelo_requerimiento.py` |
| CA-03 | Cumple (brecha de cobertura, ver H-05) | E2 `test_requirement_repository.py::test_saves_and_loads_full_aggregate` (`loaded == saved`: escalares, JSON, firmas, anexos), `::test_get_by_folio_and_list`, `::test_updates_existing_requirement` -> PASSED; E1 `test_mappers.py::test_version_with_children_round_trip` cubre las 7 colecciones a nivel mapper -> PASSED |
| CA-04 | Cumple | E2 `test_requirement_repository.py::test_duplicate_folio_is_rejected` espera `IntegrityError` por `REQ_REQUERIMIENTO_FOLIO_UQ` -> PASSED |
| CA-05 | Cumple | E1 `tests/domain/test_requirement.py::test_freeze_and_advance_copies_only_active_items_preserving_order` (solo `active=True`, `order` preservado, `id=None`, version anterior `frozen`, sucesora no congelada) -> PASSED |
| CA-06 | Cumple | E1 `tests/domain/test_requirement.py::{test_forbidden_transition_is_rejected, test_terminal_states_have_no_transitions, test_forward_transitions_are_allowed, test_backward_transitions_are_allowed, test_cancel_from_non_terminal_is_allowed}` -> PASSED |
| CA-07 | Cumple | E1 `test_authorize_only_on_current_version` (rechaza `version_id` no vigente con `AuthorizationNotOnCurrentVersionError`; acepta la vigente) -> PASSED |
| CA-08 | Cumple | E2 `test_migration_requerimiento.py::{test_campos_dinamicos_rejects_invalid_json, test_campos_dinamicos_accepts_valid_json}` (`IS JSON`) y `test_requirement_repository.py::test_invalid_dynamic_fields_json_is_rejected` -> PASSED |
| CA-09 | Cumple | E1 `ruff` All checks passed; `mypy --strict app` Success (39 archivos); `pytest` 43 passed / 14 deselected; `integration` marcado y excluido por defecto en `pyproject.toml` |

**Resumen: 9/9 Cumple.**

## Hallazgos

- **H-01 (positivo) - Separacion hexagonal respetada.** `app/domain/**` no importa FastAPI/SQLAlchemy/docxtpl/Alembic/IA; `app/application/**` no importa `app.infrastructure` ni SQLAlchemy; los tipos de SQLAlchemy quedan confinados a `app/infrastructure/**`. Los puertos exponen solo entidades de dominio.
- **H-02 - Adaptadores de catalogo sin pruebas.** `SqlAlchemyChangeTypeCatalog` y `SqlAlchemyPositionCatalog` (`infrastructure/adapters/catalogs.py`) no tienen prueba unitaria ni de integracion; CA-02 se evidencia con SQL directo, no a traves de los adaptadores. La lectura de catalogos (RF-09/RF-12) queda sin cobertura.
- **H-03 - `tables.py` no es espejo exacto del DDL.** La migracion define la FK `REQ_REQUERIMIENTO.VERSION_ACTUAL_ID -> REQ_VERSION.ID` via `op.create_foreign_key`, pero `infrastructure/db/tables.py:REQ_REQUERIMIENTO` no declara esa `ForeignKey`. Ademas `CONTENIDO` de las tablas de coleccion es `nullable=True` en la migracion y `nullable=False` en `tables.py`. No rompe pruebas hoy, pero contradice el "espejo exacto" del plan (linea 127).
- **H-04 - Concurrencia / version unica no protegida en BD.** "Como maximo una version no congelada" solo se valida en dominio (`MultipleWorkingVersionsError`); no hay indice unico ni bloqueo optimista en el esquema. El riesgo "Concurrencia al crear versiones" (spec) pedia definir bloqueo optimista en el plan y no quedo implementado.
- **H-05 - Cobertura CA-03 incompleta contra Oracle.** El round-trip de integracion ejercita objetivos, beneficios, riesgos, firmas y anexos; consideraciones, restricciones, volumetria y requisitos futuros solo se prueban a nivel de mapper. El codigo es generico (`_replace_collection`/`_collection_rows`), riesgo residual bajo.
- **H-06 - Deriva plan <-> codigo.** `plan.md` (linea 95) describe `RequirementVersion.add_signature(signature)`; la implementacion expone `with_signature(...)`. Solo desalineacion documental.
- **H-07 - Caso borde en `authorize`.** La comparacion `current.id != version_id` acepta `version_id=None` cuando la version vigente aun no fue persistida (`current.id is None`). No hay CA que lo cubra, pero permite autorizar una version no persistida.
- **H-08 - Exportaciones de puertos inconsistentes.** `application/ports/__init__.py` solo reexporta `DatabaseHealthPort`, mientras `infrastructure/adapters/__init__.py` si reexporta los adaptadores nuevos. Inconsistencia menor de ergonomia.
- **H-09 - `mypy` reporta override no usado.** `[[tool.mypy.overrides]] module = ["alembic.*", "testcontainers.*"]` queda sin uso (nota, no error). No afecta CA-09.

## Deuda tecnica registrada

- **DT-01** Pruebas de `SqlAlchemyChangeTypeCatalog` / `SqlAlchemyPositionCatalog` (H-02).
- **DT-02** Unificar `tables.py` con el DDL de la migracion (FK `VERSION_ACTUAL_ID`, nulabilidad de `CONTENIDO`) o documentar la divergencia como intencional (H-03).
- **DT-03** Control de concurrencia / garantia en BD de "una sola version no congelada" (H-04).
- **DT-04** Ampliar el round-trip de integracion CA-03 a las 7 colecciones (H-05).
- **DT-05** Alinear `plan.md` (`add_signature`) con el codigo (`with_signature`) (H-06).
- **DT-06** Endurecer `authorize` para rechazar `version_id` nulo/sin persistir y anadir prueba (H-07).
- **DT-07** Reexportar los puertos nuevos en `application/ports/__init__.py` (H-08).
- **DT-08** Limpiar/justificar el override de `mypy` para mantener la salida sin notas (H-09).
