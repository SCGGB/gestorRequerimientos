# Tareas - SPEC-003

> Ordenadas por dependencia. Cada tarea es atomica y verificable. No hay esquema nuevo ni migracion Alembic:
> se reutiliza `0002_modelo_requerimiento`. No se implementan wizard/UI (SPEC-004), validacion de negocio
> integral (SPEC-005), IA (SPEC-006), DOCX/PDF (SPEC-007), auth/JWT con enforcement ni roles (SPEC-008) ni
> subida de binarios/`StoragePort` (ADR-006). Las rutas de negocio van bajo `/api/v1`; `/health` y `/version`
> no se tocan.

## Dominio adicional (Python puro, sin BD)

- [x] T-01 (RF-05, RF-06, RF-07, CA-05, CA-08) `domain/requirement/errors.py` (nuevas `RequirementNotEditableError` y `SignatureNotAllowedError`) y guardas de dominio: `Requirement.version_by_id(version_id)`, `Requirement.ensure_editable()` (exige `BORRADOR`), `RequirementVersion.ensure_working()` (exige no congelada) y `Requirement.ensure_signable(version_id)` (exige `APROBADO`/`GENERADO` y version vigente, ADR-007).
- [x] T-02 (RF-06, CA-06, CA-07) `domain/requirement/collections.py`: `CollectionKind` y helpers puros `make_item`, `items_of`, `with_added` (order incremental), `with_content_updated`, `with_deactivated` (baja logica), `with_reordered` (renumera por lista de ids, deja los no listados despues); `Benefit` exige `BenefitKind`.
- [x] T-03 (RF-05, RF-06, CA-05, CA-06, CA-07) `tests/domain/test_requirement_editing.py`: guardas (editable solo en `BORRADOR` y version no congelada), alta/edicion/baja logica/reorden por coleccion y `Benefit` con discriminador. Sin base de datos.

## Errores de aplicacion y puertos

- [x] T-04 (RF-12, CA-04) `application/errors.py`: `RequirementNotFoundError`, `VersionNotFoundError`, `CollectionItemNotFoundError`, `AttachmentNotFoundError`, `DuplicateFolioError`, `DataConflictError`.
- [x] T-05 (RF-14, CA-03) `application/ports/requirement_repository.py`: agregar `RequirementSearchFilters(status, folio)` y `search(filters, *, offset, limit) -> tuple[Sequence[Requirement], int]`; mantener `save`/`get`/`get_by_folio`/`list` sin cambios de firma.
- [x] T-06 (RF-11, CA-11) `application/ports/catalog_repository.py`: agregar `PositionCatalog.list_active() -> Sequence[Position]` (para `GET /catalogos/cargos` sin `rol`).
- [x] T-07 (RF-16) `application/ports/auth.py`: marcador `Principal` y `AuthProvider(ABC).current_principal()`; sin enforcement ni adaptador de produccion en esta spec (punto de extension de SPEC-008).

## Adaptadores de persistencia

- [x] T-08 (RF-14, CA-02, CA-03, CA-04) `infrastructure/adapters/requirement_repository.py`: implementar `search` con filtros opcionales (`ESTADO`, `FOLIO`), `COUNT(*)` y `ORDER BY ID OFFSET :offset ROWS FETCH FIRST :limit ROWS ONLY` reutilizando `_load`; traducir `NoResultFound`→`RequirementNotFoundError` y `IntegrityError`→`DuplicateFolioError` (unicidad `FOLIO`) o `DataConflictError` (resto). La firma no expone tipos de SQLAlchemy.
- [x] T-08b (CA-06, RF-06, RF-08) `infrastructure/adapters/requirement_repository.py`: sustituir el delete+insert de hijos por **upsert por fila** en `_replace_collection`/`_replace_signatures`/`_replace_attachments` (borrar solo `ID` ausentes, `UPDATE` con `id` y `INSERT` sin `id`) y aplicar el reorden en **dos fases** por el UQ `(VERSION_ID, ORDEN)`. Ids de sub-recursos estables y auditoría de fila preservada; sin cambios de firma de puerto ni migracion.
- [x] T-09 (RF-11, CA-11) `infrastructure/adapters/catalogs.py`: `SqlAlchemyPositionCatalog.list_active()` filtrando `ACTIVO='S'` y ordenando por `NOMBRE`.
- [x] T-10 (CA-02, CA-03, CA-06) `tests/integration/test_requirement_repository_search.py` (marcado `integration`): `search` con y sin filtros, total y paginacion (`offset/limit`), folio duplicado traducido a `DuplicateFolioError`, **estabilidad de ids** de colecciones/firmas/anexos entre escrituras y reorden sin violar el UQ. Reutiliza `oracle_url`/`migrated_engine`.

## Casos de uso (`application/use_cases/requirement/`)

- [x] T-11 (RF-01, RF-03, CA-01, CA-04) `create_requirement.py` (`CreateRequirement`) y `get_requirement.py` (`GetRequirement`): crear folio + version 1 de trabajo en `BORRADOR`; consultar el agregado completo (404 via `RequirementNotFoundError`).
- [x] T-12 (RF-02, CA-03) `list_requirements.py` (`ListRequirements`): calcula `offset=(page-1)*size`, llama `repo.search` y devuelve `(items, total, page, size)`.
- [x] T-13 (RF-04) `list_versions.py` (`ListVersions`, `GetVersion`): historico ordenado y detalle por `vid` (`VersionNotFoundError`).
- [x] T-14 (RF-05, CA-05) `update_version.py` (`UpdateVersion`): carga el requerimiento, exige `ensure_editable` + `ensure_working` sobre la version de trabajo, aplica `replace` de cabecera/narrativa y persiste.
- [x] T-15 (RF-06, CA-06, CA-07) `manage_collection.py` (`AddCollectionItem`, `UpdateCollectionItem`, `DeleteCollectionItem`, `ReorderCollectionItems`): usa `collections.py`; exige editable + working; `itemId` inexistente → `CollectionItemNotFoundError`.
- [x] T-16 (RF-07, CA-08) `register_signature.py` (`RegisterSignature`): valida que la version exista (`VersionNotFoundError`) y llama `Requirement.ensure_signable(vid)` (estado `APROBADO`/`GENERADO` y version vigente; si no, `SignatureNotAllowedError`); registra `ELABORO`/`REVISO`/`AUTORIZO` sobre la version vigente, esta ultima via `Requirement.authorize`.
- [x] T-17 (RF-08) `manage_attachment.py` (`AddAttachment`, `UpdateAttachment`, `DeleteAttachment`, `ReorderAttachments`): CRUD de metadato por version editable; `aid` inexistente → `AttachmentNotFoundError`; solo metadato (sin binario).
- [x] T-18 (RF-09, CA-09) `freeze_version.py` (`FreezeAndAdvance`): `titulo` opcional con default de la version vigente; llama `Requirement.freeze_and_advance` (sin version de trabajo → error de dominio → 409).
- [x] T-19 (RF-10, CA-10) `change_status.py` (`ChangeStatus`): resuelve el enum destino y llama `Requirement.change_status`.
- [x] T-20 (RF-11, CA-11) `list_catalogs.py` (`ListChangeTypes`, `ListPositions`): tipos de cambio activos y cargos por `rol` (o todos si no se informa).
- [x] T-21 (CA-01, CA-02, CA-05, CA-06, CA-07, CA-08, CA-09, CA-10, CA-11) `tests/application/test_requirement_use_cases.py`: casos de uso con `InMemoryRequirementRepository`/catalogos falsos (sin BD), cubriendo altas, copy-on-write, cambio de estado, edicion fuera de `BORRADOR`, colecciones, firmas solo en `APROBADO`/`GENERADO` y sobre la version vigente (fuera de ahi `SignatureNotAllowedError`) y catalogos.

## API (`app/api/`)

- [x] T-22 (RF-12, CA-02, CA-12) `api/schemas/errors.py` (`ErrorDetail`, `ErrorResponse`) y `api/errors.py`: registro del `exception_handler` global que mapea dominio/aplicacion/Pydantic/HTTP al envelope `{"error": {"code", "message", "details"}}` con los `code` estables del plan.
- [x] T-23 (RF-01, RF-05, RF-09, RF-10) `api/schemas/requirement.py`: entrada (`RequirementCreate`, `VersionUpdate`, `NewVersionRequest`, `StatusChangeRequest`, `SignatureCreate`) y salida (`CollectionItemResponse`, `BenefitResponse`, `SignatureResponse`, `AttachmentResponse`, `VersionResponse`, `RequirementResponse`, `RequirementSummary`, `RequirementPage`), traduciendo dominio (ingles) ↔ API (espanol).
- [x] T-24 (RF-11) `api/schemas/catalog.py` (`ChangeTypeResponse`, `PositionResponse`), `api/schemas/collection.py` (`CollectionItemCreate`, `BenefitCreate`, `CollectionItemUpdate`, `ReorderRequest`) y `api/schemas/attachment.py` (`AttachmentCreate`, `AttachmentUpdate`).
- [x] T-25 (RF-01, RF-02, RF-03, RF-04, RF-05, RF-09, RF-10) `api/routers/requirements.py` (`prefix="/api/v1"`): POST/GET listado/GET detalle, GET versiones y version, PATCH version, POST versiones y POST estado; solo orquestan validacion → caso de uso → serializacion (sin logica de negocio).
- [x] T-26 (RF-06, RF-07, RF-08) `api/routers/collections.py`, `api/routers/signatures.py` y `api/routers/attachments.py`: CRUD de colecciones (mapa explicito recurso→`CollectionKind`), registro de firmas y CRUD de anexos.
- [x] T-27 (RF-11) `api/routers/catalogs.py`: `GET /catalogos/tipos-cambio` y `GET /catalogos/cargos?rol=`.
- [x] T-28 (RF-13, RF-16) `api/dependencies.py` (fabricas de repositorio/catalogos/`AuthProvider` y de casos de uso con puertos por `Depends`) y `main.py` (incluir routers con `prefix="/api/v1"`, registrar handlers y actualizar `api/routers/__init__.py`/`api/schemas/__init__.py`). `health`/`version` sin cambios.
- [x] T-29 (CA-01, CA-02, CA-03, CA-04, CA-05, CA-08, CA-10) `tests/api/test_requirements.py`: `TestClient` con `dependency_overrides` de los puertos (patron de `tests/api/test_health.py`); cubre 201 de creacion, envelope `{items,total,page,size}`, 404, 409 (folio duplicado/estado/firma en estado no final) y 422.
- [x] T-30 (RF-12, CA-02, CA-12) `tests/api/test_error_envelope.py`: contrato del envelope `{"error": {"code","message","details"}}` y `GET /openapi.json` expone todos los endpoints de la spec.

## Documentacion

- [x] T-31 (RF-15, RF-07) `doc/technical/api.md`: prefijo `/api/v1`, envelope de error con `code` por tipo, catalogo de endpoints con codigos HTTP, politica de firmas (solo en `APROBADO`/`GENERADO` y version vigente), mapa de nombres de recursos de colecciones y referencia a `/openapi.json`.
- [x] T-31b (RF-07, CA-08) `doc/architecture/adr/007-firmas-segun-estado.md`: ADR que fija que las firmas se registran solo en estado final y sobre la version vigente, ajustando ese aspecto de ADR-005; referenciado desde `spec.md` y `plan.md`.

## Calidad

- [x] T-32 (CA-12) Verificar `ruff check .`, `mypy --strict app` y `pytest` sin errores (integracion con `pytest -m integration` con Docker/Oracle); confirmar que la app arranca sin IA (`AI_PROVIDER=none`) y sin auth activa.
