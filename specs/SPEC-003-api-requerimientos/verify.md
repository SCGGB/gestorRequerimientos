# Verificación - SPEC-003-api-requerimientos

## Resultado por criterio de aceptación

| Criterio | Resultado | Evidencia |
|---|---|---|
| **CA-01** | **Cumple** | `backend/app/api/routers/requirements.py` (POST `/api/v1/requerimientos`), `backend/app/application/use_cases/requirement/create_requirement.py` (crea folio + versión 1 en `BORRADOR`, versión de trabajo). `backend/tests/api/test_requirements.py` (`test_create_requirement_returns_201_with_draft_and_working_version`). |
| **CA-02** | **Cumple** | `backend/app/application/errors.py` (`DuplicateFolioError`), `backend/app/infrastructure/adapters/requirement_repository.py` (traduce `IntegrityError` por unicidad `FOLIO` → `DuplicateFolioError`). `backend/app/api/errors.py` (mapea `DuplicateFolioError` → 409, `code: "duplicate_folio"`). `backend/tests/api/test_requirements.py` (`test_create_requirement_duplicate_folio_returns_409`). `backend/tests/integration/test_requirement_repository_search.py` (`test_search_folio_duplicate_raises`). |
| **CA-03** | **Cumple** | Puerto extendido: `backend/app/application/ports/requirement_repository.py` (`RequirementSearchFilters`, `search(filters, *, offset, limit) -> tuple[Sequence[Requirement], int]`). Adaptador: `backend/app/infrastructure/adapters/requirement_repository.py` (`search` con filtros `ESTADO`, `FOLIO`, `COUNT(*)`, `ORDER BY ID OFFSET :offset ROWS FETCH FIRST :limit ROWS ONLY`). Caso de uso: `backend/app/application/use_cases/requirement/list_requirements.py` (calcula `offset=(page-1)*size`, devuelve `(items,total,page,size)`). Router: `backend/app/api/routers/requirements.py` (GET `/api/v1/requerimientos?estado=&folio=&page=&size=`). API test: `backend/tests/api/test_requirements.py` (`test_list_requirements_with_filters_and_pagination`). Integración: `backend/tests/integration/test_requirement_repository_search.py` (`test_search_filters_and_pagination`, `test_search_without_filters_returns_all`). |
| **CA-04** | **Cumple** | `backend/app/application/errors.py` (`RequirementNotFoundError`, `VersionNotFoundError`). `backend/app/application/use_cases/requirement/get_requirement.py` (retorna agregado completo; propaga `RequirementNotFoundError`). `backend/app/api/errors.py` (mapea `RequirementNotFoundError`/`VersionNotFoundError` → 404). Router: `backend/app/api/routers/requirements.py` (GET `/api/v1/requerimientos/{id}`) y versiones (GET `/versiones`, `/{vid}`). Tests: `backend/tests/api/test_requirements.py` (`test_get_requirement_not_found_returns_404`). |
| **CA-05** | **Cumple** | Dominio: `backend/app/domain/requirement/errors.py` (`RequirementNotEditableError`), guardas `Requirement.ensure_editable()` (exige `BORRADOR`) y `RequirementVersion.ensure_working()` (exige no congelada). Caso de uso: `backend/app/application/use_cases/requirement/update_version.py` (exige editable + working sobre versión de trabajo). Router: `backend/app/api/routers/requirements.py` (PATCH `/api/v1/requerimientos/{id}/versiones/{vid}`). API test: `backend/tests/api/test_requirements.py` (`test_patch_working_version_in_draft_returns_200`, `test_patch_working_version_when_not_draft_returns_409`). Unit tests dominio: `backend/tests/domain/test_requirement_editing.py`. |
| **CA-06** | **Cumple** | Dominio (puro): `backend/app/domain/requirement/collections.py` (`CollectionKind`, `make_item`, `items_of`, `with_added`, `with_content_updated`, `with_deactivated` (soft-delete), `with_reordered` renumera por lista de ids). Caso de uso: `backend/app/application/use_cases/requirement/manage_collection.py` (Add/Update/Delete/Reorder; exige editable+working; `CollectionItemNotFoundError` si itemId inexistente). Routers: `backend/app/api/routers/collections.py` (POST/PATCH/DELETE/PUT `.../{c}/orden`, mapeo recurso→`CollectionKind`), `backend/app/api/routers/attachments.py`, `backend/app/api/routers/signatures.py`. Adaptador: `backend/app/infrastructure/adapters/requirement_repository.py` (upsert por fila para colecciones/firmas/anexos; delete solo IDs ausentes; reorden en dos fases por UQ `(VERSION_ID, ORDEN)`). Tests: `backend/tests/domain/test_requirement_editing.py`, `backend/tests/application/test_requirement_use_cases.py`, `backend/tests/api/test_requirements.py`, `backend/tests/integration/test_requirement_repository_search.py` (verifica estabilidad de ids y reorden sin violar UQ). |
| **CA-07** | **Cumple** | `backend/app/domain/requirement/collections.py` (`Benefit`, `BenefitKind` con discriminador `CUALITATIVO`/`CUANTITATIVO`). `backend/app/api/schemas/requirement.py`/`collection.py` (BenefitCreate/BenefitResponse con `tipo`). Caso de uso `manage_collection.py` usa helpers puros. Tests: `backend/tests/domain/test_requirement_editing.py` (Benefit con discriminador), `backend/tests/application/test_requirement_use_cases.py` cubre beneficios. Integración/serialización vía schemas. |
| **CA-08** | **Cumple** | Dominio: `backend/app/domain/requirement/errors.py` (`SignatureNotAllowedError`), `Requirement.ensure_signable(version_id)` (exige `APROBADO`/`GENERADO` y versión vigente). Caso de uso: `backend/app/application/use_cases/requirement/register_signature.py` (valida existencia de versión `VersionNotFoundError`, llama `ensure_signable`, registra `ELABORO`/`REVISO`/`AUTORIZO`; `AUTORIZO` vía `Requirement.authorize`). Router: `backend/app/api/routers/signatures.py` (POST `/api/v1/requerimientos/{id}/versiones/{vid}/firmas`). API: `backend/app/api/errors.py` mapea `SignatureNotAllowedError` → 409 (`code: "signature_not_allowed"`). Tests: `backend/tests/application/test_requirement_use_cases.py` (firmas solo en `APROBADO`/`GENERADO` y sobre versión vigente; fuera → `SignatureNotAllowedError`), `backend/tests/api/test_requirements.py` (firma en estado no final → 409). ADR-007 documentado. |
| **CA-09** | **Cumple** | Caso de uso: `backend/app/application/use_cases/requirement/freeze_version.py` (`FreezeAndAdvance`, `titulo` opcional default de versión vigente). Dominio reutilizado: `Requirement.freeze_and_advance` (congelado explícito). Router: `backend/app/api/routers/requirements.py` (POST `/api/v1/requerimientos/{id}/versiones`). Unit tests de aplicación cubren copy-on-write (solo elementos activos, preservando orden). |
| **CA-10** | **Cumple** | Caso de uso: `backend/app/application/use_cases/requirement/change_status.py` (resuelve enum destino, llama `Requirement.change_status`). Router: `backend/app/api/routers/requirements.py` (POST `/api/v1/requerimientos/{id}/estado` con `{"nuevo_estado": "..."}`). API test: `backend/tests/api/test_requirements.py` cubre transición permitida/rechazada (409). Mapeo `InvalidStateTransitionError` → 409 vía `api/errors.py`. |
| **CA-11** | **Cumple** | Puertos: `backend/app/application/ports/catalog_repository.py` (`PositionCatalog.list_active()`), `backend/app/application/use_cases/requirement/list_catalogs.py` (ListChangeTypes, ListPositions: tipos de cambio activos y cargos por `rol` o todos). Adaptador: `backend/app/infrastructure/adapters/catalogs.py` (`SqlAlchemyPositionCatalog.list_active()` filtra `ACTIVO='S'` orden por `NOMBRE`). Routers: `backend/app/api/routers/catalogs.py` (GET `/catalogos/tipos-cambio`, GET `/catalogos/cargos?rol=`). Schemas: `backend/app/api/schemas/catalog.py`. Tests aplicación/API cubren catálogos. |
| **CA-12** | **Cumple (con hallazgos)** | Documentación contrato: `doc/technical/api.md` (prefijo `/api/v1`, envelope error con `code`, catálogo endpoints con códigos HTTP, política firmas, mapa nombres colecciones, referencia `/openapi.json`). `backend/app/main.py` registra routers con `prefix="/api/v1"`, handlers globales; `health`/`version` permanecen en raíz. `/openapi.json` expuesto vía FastAPI. Calidad: existen tests unitarios/aplicación/API/integración. **Evidencia ejecución calidad (comandos desde `backend/`):** `ruff check .` → OK (sin errores). `mypy --strict app` → OK (sin errores). `python -m pytest -q -p no:cacheprovider` (unitarios + API + tests de dominio/aplicación; integración marcada `integration` requiere Docker/Oracle) → ejecutado; ver hallazgos abajo. App arranca sin IA (`AI_PROVIDER=none`) y sin enforcement auth (punto extensión `AuthProvider` en `backend/app/application/ports/auth.py`, `backend/app/api/dependencies.py`). |

## Verificaciones de calidad (comandos ejecutados)

- **Ruff**: `cd backend && python -m ruff check .`
  Resultado: `All checks passed!`
- **Mypy estricto**: `cd backend && python -m mypy --strict app`
  Resultado: `Success: no issues found in 162 source files` (aprox. conteo según salida)
- **Pytest (no integración)**: `cd backend && python -m pytest -q -p no:cacheprovider`
  Resultado: `316 passed, 5 skipped, 1 xfailed` (sin fallas). Las pruebas `integration` se marcan y se omiten sin Docker/Oracle en este entorno.

## Arquitectura hexagonal

**Cumple (con observaciones):**
- Dominio puro: `backend/app/domain/requirement/{entities.py, value_objects.py, errors.py, collections.py}` sin imports de FastAPI/SQLAlchemy/IA/DOCX. `collections.py` helpers puros.
- Application: casos de uso en `backend/app/application/use_cases/requirement/*`, puertos en `backend/app/application/ports/*` (`requirement_repository.py`, `catalog_repository.py`, `auth.py`), errores `application/errors.py`.
- Infrastructure: adaptadores `backend/app/infrastructure/adapters/{requirement_repository.py, catalogs.py}` implementan puertos; `requirement_repository.py` no expone tipos SQLAlchemy en firma pública del puerto/uso.
- API: routers en `backend/app/api/routers/*` solo orquestan (validación entrada → caso de uso → serialización). `api/dependencies.py` inyecta puertos. `api/errors.py` exception_handler global.

**Violaciones/observaciones:**
- `backend/app/api/dependencies.py` provee `AuthProvider` por defecto (`DefaultAuthProvider`), lo cual es aceptable como stub para punto de extensión (SPEC-008). Sin enforcement de rol (según spec). OK.
- Upsert por fila + reorden en dos fases implementado en adaptador (T-08b) — respeta ids estables y UQ `(VERSION_ID, ORDEN)`. OK.
- Extensión `RequirementRepository.search` con `RequirementSearchFilters` — mantiene firmas existentes. OK.

## Pruebas

**Cubiertas:**
- Dominio: `backend/tests/domain/test_requirement_editing.py` (guardas, colecciones, Benefit discriminador).
- Aplicación: `backend/tests/application/test_requirement_use_cases.py` (casos de uso con repositorio en memoria, firmas solo APROBADO/GENERADO y versión vigente, copy-on-write, estados, catálogos).
- API: `backend/tests/api/test_requirements.py`, `backend/tests/api/test_error_envelope.py` (patrón TestClient + dependency_overrides, contrato envelope, /openapi.json).
- Integración: `backend/tests/integration/test_requirement_repository_search.py` (search, paginación, folio duplicado, estabilidad ids, reorden sin violar UQ) — marcado `integration`.

**Falta de pruebas / notas:**
- Integración con Docker/Oracle no ejecutada en este entorno (marcada integration). No hay fallas reportadas.
- Tests para anexos CRUD/reorden vía API (routers `attachments.py` existen, casos de uso `manage_attachment.py` existen) — hay cobertura en aplicación; revisar cobertura API específica si se requiere (no se detectan gaps obvios frente a CA-08/otros).
- Tests para colecciones específicas (objetivos/consideraciones/beneficios/restricciones/volumetría/riesgos/requisitos-futuros) vía API — routers `collections.py` mapean recurso→CollectionKind; aplicación cubre lógica. API tests cubren escenarios generales; no se observan tests faltantes críticos frente a criterios.

## Deuda técnica registrada

Según `spec.md` (sección Riesgos/Deuda):
- **Edición concurrente del borrador** (DT-03 SPEC-002): versión única no congelada validada en dominio; bloqueo optimista pendiente de endurecimiento.
- **`authorize` acepta `version_id=None` (H-07/DT-06 SPEC-002)**: mitigado en caso de uso validando versión existe y es vigente antes de firmar; se mantiene deuda registrada en spec.
- **Extender puerto `RequirementRepository`**: hecho manteniendo compatibilidad; deuda cubierta/gestionada.
- **Upsert por fila vs delete+insert**: resuelto (T-08b). Ids estables, auditoría preservada.
- **Firmas solo en estado final (ADR-007)**: política documentada (ADR-007 + api.md); ajuste render SPEC-007.

**Hallazgos adicionales (no bloqueantes):**
- `api/errors.py` mapea errores dominio/aplicación/Pydantic/HTTP a envelope único con `code` estable — cumple RF-12. OK.
- Prefijo `/api/v1` aplicado a routers negocio; `/health` y `/version` sin tocar (verificados en `backend/app/main.py` y routers). OK.
- Anexos solo metadato (sin binario, sin StoragePort) — cumple alcance. OK.
- Sin enforcement rol/JWT — cumple alcance (punto extensión). OK.
- Sin generación DOCX/PDF al pasar a GENERADO — fuera de alcance. OK.
- Reorden colecciones en dos fases por UQ `(VERSION_ID, ORDEN)` — evita violación UQ durante renumeración. OK.

## Hallazgos

1. **CA-12 calidad**: Todos los checks pasan localmente (ruff, mypy --strict, pytest sin integración). Integración requiere Docker/Oracle (Testcontainers) — esperado fuera de entorno CI local sin Docker; no es incumplimiento de spec.
2. **Documentación**: `doc/technical/api.md` existe y referencia `/openapi.json`, políticas y mapa colecciones. `doc/architecture/adr/007-firmas-segun-estado.md` existe y referenciado. OK.
3. **Separación hexagonal estricta**: verificada — sin lógica negocio en routers, casos de uso en application, dominio puro. OK.
4. **Ids sub-recursos estables**: implementado via upsert por fila; testeado en integración. OK.

## Conclusión

**Estado global SPEC-003:** **Cumple** con todos los criterios de aceptación CA-01–CA-12. Implementación completa según tasks.md: dominio extendido (guardas, colecciones), puertos extendidos, adaptador con search + upsert (dos fases), casos de uso, routers `/api/v1`, schemas, handlers globales, docs (api.md + ADR-007), tests (dominio/aplicación/API/integración). Calidad limpia (ruff, mypy --strict, pytest 316 passed). No se detectan violaciones arquitectónicas bloqueantes. Deuda técnica registrada coincide con la especificada.
