# Plan tecnico - SPEC-003

> Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`,
> `doc/documents/mapeo-machote.md`, `doc/ui/wizard-flow.md`, `doc/development/convenciones.md`,
> `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`,
> `doc/architecture/adr/003-autenticacion.md`,
> `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/006-almacenamiento-objetos-dev.md`,
> `doc/architecture/adr/007-firmas-segun-estado.md`.
> Esta spec construye la capa `application` (casos de uso) y `api` encima del dominio y la persistencia de
> SPEC-002. **No** incluye wizard/UI (SPEC-004), validacion de negocio integral (SPEC-005), IA (SPEC-006),
> generacion DOCX/PDF (SPEC-007), auth/JWT y roles (SPEC-008) ni subida de binarios de anexos ni `StoragePort`
> (ADR-006). `POST /estado` a `GENERADO` solo ejecuta la transicion, no genera archivos.

## Enfoque

Exponer el agregado `Requirement` (ya persistido en Oracle por SPEC-002) mediante casos de uso en
`application` y endpoints HTTP bajo `/api/v1`. El trabajo se separa en cinco frentes en este orden:

1. **Dominio adicional**: pequenas invariantes de edicion que SPEC-002 no necesitaba (`RequirementNotEditableError`,
   acceso a una version por `id`, guardas `ensure_editable`/`ensure_working`) y los helpers puros de colecciones
   (alta/edicion/baja logica/reorden + discriminador `BenefitKind`). Sin imports de FastAPI/SQLAlchemy.
2. **Puertos ampliados**: `RequirementRepository.search(...)` (listado filtrado/paginado, RF-14),
   `PositionCatalog.list_active()` (catalogos sin filtro), un marcador `AuthProvider` (punto de extension, sin
   enforcement) y errores de aplicacion (`RequirementNotFoundError`, `VersionNotFoundError`,
   `CollectionItemNotFoundError`, `AttachmentNotFoundError`, `DuplicateFolioError`, `DataConflictError`).
3. **Casos de uso** (`application/use_cases/requirement/`): crear, listar, consultar, versionar, editar cabecera/
   narrativa, CRUD de colecciones, firmas, CRUD de anexos, cambio de estado y catalogos. Orquestan el dominio y
   los puertos; **cero** logica de negocio en routers (RF-13).
4. **Adaptadores**: implementar `search` (COUNT + OFFSET/FETCH) y traducir `NoResultFound`/`IntegrityError` del
   driver a errores de aplicacion, de modo que la `api` no importe `sqlalchemy` ni conozca el driver.
5. **API** (`api/`): esquemas Pydantic v2 (entrada/salida), un `exception_handler` global con envelope propio
   unico, routers `/api/v1` por recurso, cableado de dependencias y `doc/technical/api.md`.

La fuente de verdad sigue siendo la base de datos; los casos de uso cargan el agregado completo, aplican la
mutacion pura del dominio y persisten con `RequirementRepository.save`. El adaptador conserva el upsert del
contenedor/versiones y pasa a un **upsert por fila** de los hijos (ids estables; ver Adaptadores).

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic

**No aplica.** Esta spec no introduce tablas, columnas, indices ni migraciones nuevas: reutiliza el esquema
`0002_modelo_requerimiento` y los catalogs sembrados por SPEC-002. `alembic upgrade head` sigue siendo el unico
mecanismo de DDL (sin cambios). No se agrega una revision nueva.

## Dominio y casos de uso

### Dominio adicional (`app/domain/requirement/`)

Sin imports de infraestructura ni HTTP. Se anade lo minimo que SPEC-002 no requeria:

- `errors.py`: nuevas `RequirementNotEditableError(DomainError)` — el requerimiento no esta en `BORRADOR`, o
  la version objetivo esta congelada — y `SignatureNotAllowedError(DomainError)` — se intenta firmar fuera de
  `APROBADO`/`GENERADO` o sobre una version no vigente; ambas se mapean a `409`.
- `requirement.py`:
  - `version_by_id(version_id) -> RequirementVersion | None` — busca en `self.versions`.
  - `ensure_editable() -> None` — exige `status is BORRADOR`; si no, lanza `RequirementNotEditableError`.
  - `ensure_signable(version_id) -> None` — exige `status in {APROBADO, GENERADO}` y
    `version_id == current_version().id`; si no, lanza `SignatureNotAllowedError` (ADR-007).
- `version.py`:
  - `ensure_working() -> None` — exige `not frozen`; si no, lanza `RequirementNotEditableError`.
- `collections.py` (nuevo, Python puro):
  - `CollectionKind(StrEnum)` con los nombres de atributo del dominio: `OBJETIVOS`→`objectives`,
    `CONSIDERACIONES`→`considerations`, `BENEFICIOS`→`benefits`, `RESTRICCIONES`→`restrictions`,
    `VOLUMETRIA`→`volumetry`, `RIESGOS`→`risks`, `REQUISITOS_FUTUROS`→`future_requirements_items`.
  - `make_item(kind, *, content, order, benefit_kind=None) -> CollectionItem` — fabrica el tipo correcto
    (`Benefit` exige `kind`).
  - `items_of(version, kind) -> tuple[CollectionItem, ...]` — accesor uniforme (incluye inactivos).
  - `with_added(version, kind, item) -> RequirementVersion` — asigna `order = max(orden existente)+1`.
  - `with_content_updated(version, kind, item_id, content) -> RequirementVersion` — devuelve `(version, item)`
    actualizado o `None` si no existe el `item_id` (la capa de casos decide el 404).
  - `with_deactivated(version, kind, item_id) -> RequirementVersion` — soft-delete (`active=False`); el item
    permanece en la tupla para que el persistidor lo escriba.
  - `with_reordered(version, kind, ordered_ids) -> RequirementVersion` — renumera `order` 1..n segun la lista;
    los elementos activos no listados conservan su orden relativo y se colocan despues; ids desconocidos se
    ignoran en dominio y el caso de uso valida existencia antes.

### Errores de aplicacion (`app/application/errors.py`, nuevo)

Errores que solo tienen sentido una vez existe el repositorio/HTTP; no viven en el dominio:

| Error | Uso | HTTP |
|---|---|---|
| `RequirementNotFoundError` | `repo.get` no encuentra el requerimiento | 404 |
| `VersionNotFoundError` | la version no pertenece/`existe` en el agregado | 404 |
| `CollectionItemNotFoundError` | `itemId` inexistente en la coleccion | 404 |
| `AttachmentNotFoundError` | `aid` inexistente en la version | 404 |
| `DuplicateFolioError` | folio unico violado | 409 |
| `DataConflictError` | otra violacion de integridad (FK/check) | 409 |

### Casos de uso (`app/application/use_cases/requirement/`)

Un modulo por operacion; clases pequenas con `execute(...)`. Dependen **solo** de puertos (`RequirementRepository`,
`ChangeTypeCatalog`, `PositionCatalog`).

| Modulo | Caso de uso | Responsabilidad (RF/CA) |
|---|---|---|
| `create_requirement.py` | `CreateRequirement` | Arma `Requirement(folio, BORRADOR)` + `RequirementVersion(number=1, …)` de trabajo y persiste (RF-01, CA-01/CA-02) |
| `list_requirements.py` | `ListRequirements` | Llama `repo.search(filters, offset, limit)` y compone `{items, total, page, size}` (RF-02, CA-03) |
| `get_requirement.py` | `GetRequirement` | `repo.get(id)` o `RequirementNotFoundError` (RF-03, CA-04) |
| `list_versions.py` | `ListVersions`, `GetVersion` | Historico y detalle por `vid` (RF-04) |
| `update_version.py` | `UpdateVersion` | `ensure_editable` + `ensure_working`; `replace` de cabecera/narrativa y guarda (RF-05, CA-05) |
| `manage_collection.py` | `AddCollectionItem`, `UpdateCollectionItem`, `DeleteCollectionItem`, `ReorderCollectionItems` | Usa `collections.py`; exige editable + working (RF-06, CA-06/CA-07) |
| `register_signature.py` | `RegisterSignature` | `ensure_signable` (estado final + version vigente) y anyade la `Signature` a la version vigente (RF-07, CA-08) |
| `manage_attachment.py` | `AddAttachment`, `UpdateAttachment`, `DeleteAttachment`, `ReorderAttachments` | CRUD de metadato por version editable (RF-08) |
| `freeze_version.py` | `FreezeAndAdvance` | `Requirement.freeze_and_advance(...)` con default de `titulo` (RF-09, CA-09) |
| `change_status.py` | `ChangeStatus` | `Requirement.change_status(target)` (RF-10, CA-10) |
| `list_catalogs.py` | `ListChangeTypes`, `ListPositions` | Catalogos de lectura (RF-11, CA-11) |

Regla comun: los casos usan un helper `_load_requirement(repo, id)` que delega el 404 en el adaptador (que traduce
`NoResultFound`) y verifica existencia de sub-recursos con los errores de aplicacion. No consultan ni escriben
SQL directamente.

### Firmas: estado final y version vigente (ADR-007)

Las firmas `ELABORO`, `REVISO` y `AUTORIZO` solo se registran cuando el estado es `APROBADO` o `GENERADO` y
sobre la **version vigente** (`ensure_signable`); en cualquier otro estado o version → `409`
(`signature_not_allowed`). `AUTORIZO` se sigue enrutando por `Requirement.authorize`. Este ADR-007 reemplaza,
para el *cuando* de la captura, la politica de ADR-005. Si la version no existe → `VersionNotFoundError` (404);
si existe pero no es la vigente o el estado no es final → `SignatureNotAllowedError` (409).

## Puertos y adaptadores afectados

### Puertos (`app/application/ports/`)

- `requirement_repository.py` (extender, sin romper firmas existentes):
  - `RequirementSearchFilters(status: RequirementStatus | None = None, folio: int | None = None)`.
  - `search(self, filters, *, offset: int, limit: int) -> tuple[Sequence[Requirement], int]` — `(items, total)`.
  - Se mantienen `save`, `get`, `get_by_folio`, `list` intactos.
- `catalog_repository.py` (extender): `PositionCatalog.list_active() -> Sequence[Position]` para
  `GET /catalogos/cargos` sin `rol`.
- `auth.py` (nuevo, marcador): `AuthProvider(ABC)` con `current_principal() -> Principal | None` y un dataclass
  `Principal`. **Sin enforcement** en esta spec (RF-16, ADR-003); documenta el punto de extension de SPEC-008.

### Adaptadores (`app/infrastructure/adapters/`)

- `requirement_repository.py`:
  - `search`: construye la clausula con filtros opcionales, ejecuta `COUNT(*)` y una consulta con
    `ORDER BY ID OFFSET :offset ROWS FETCH FIRST :limit ROWS ONLY` (Oracle 12c+), y carga cada id con el `_load`
    existente. Sin tipos de SQLAlchemy en la firma.
  - Traduccion de errores: envolver `save`/`get` en `try/except`
    - `NoResultFound` → `RequirementNotFoundError`.
    - `IntegrityError`: si el nombre del constraint/mensaje refiere a la unicidad de `FOLIO`
      (`UQ_REQ_REQUERIMIENTO_FOLIO`) → `DuplicateFolioError`; en otro caso → `DataConflictError`.
  - **Upsert por fila de los hijos** (reemplaza el delete+insert de SPEC-002, manteniendo el upsert total del
    agregado): para colecciones, firmas y anexos de cada version, borrar solo las filas cuyo `ID` no este en la
    tupla del dominio, `UPDATE` las que traen `id` (contenido, `ORDEN`, `ACTIVO`, `UPDATED_*`) e `INSERT` las de
    `id` nulo (`CREATED_*`/`UPDATED_*`). Asi los identificadores de sub-recursos quedan **estables** y no se
    reinicia la auditoría de fila. El reorden se aplica en **dos fases** por el UQ `(VERSION_ID, ORDEN)`: primero
    desplazar todos los `ORDEN` de la version a un rango temporal y luego fijar los valores finales.
  - `save` sigue devolviendo `self.get(requirement_id)` (agregado recargado). La firma del metodo y la interfaz
    del puerto no cambian.
- `catalogs.py`: `SqlAlchemyPositionCatalog.list_active()` (filtra `ACTIVO='S'`, ordena por `NOMBRE`).

## API (endpoints, contratos, errores)

### Convenciones

- Prefijo `/api/v1`; `/health` y `/version` permanecen en la raiz (sin tocar).
- Nombres de campos en espanol snake_case; los esquemas traducen dominio (ingles) ↔ API.
- Envelope de error unico: `{"error": {"code": str, "message": str, "details": object | null}}` (RF-12).

### Esquemas (`app/api/schemas/`)

- `errors.py`: `ErrorDetail(code, message, details)`, `ErrorResponse(error=ErrorDetail)`.
- `requirement.py`:
  - Entrada: `RequirementCreate(folio, titulo, tipo_cambio_id, sistema, version_documento, fecha_version)`,
    `VersionUpdate` (todos opcionales: `titulo`, `tipo_cambio_id`, `sistema`, `version_documento`,
    `fecha_version`, `necesidad_actual`, `contexto_descripcion`, `contexto_manejo_errores`, `usuarios_permisos`,
    `requisitos_futuros_aplica`, `requisitos_futuros_texto`, `campos_dinamicos`),
    `NewVersionRequest(version_documento, fecha_version, titulo: str | None = None)`,
    `StatusChangeRequest(nuevo_estado: RequirementStatus)`, `SignatureCreate(rol, nombre, cargo, cargo_id=None)`.
  - Salida: `CollectionItemResponse`, `BenefitResponse(+tipo)`, `SignatureResponse`, `AttachmentResponse`,
    `VersionResponse` (escalares + colecciones + firmas + anexos + `numero`, `congelada`),
    `RequirementResponse` (id, folio, ticket, estado, version_actual_id, versiones),
    `RequirementSummary`, `RequirementPage(items, total, page, size)`.
- `catalog.py`: `ChangeTypeResponse(id, codigo, nombre, activo)`, `PositionResponse(id, rol, nombre,
  predeterminado, activo)`.
- `collection.py`: `CollectionItemCreate(contenido, orden: int | None = None)`,
  `BenefitCreate(contenido, tipo, orden: int | None = None)`, `CollectionItemUpdate(contenido)`,
  `ReorderRequest(ids: list[int])`.
- `attachment.py`: `AttachmentCreate(nombre, tipo_mime, orden: int | None = None, leyenda: str | None = None,
  storage_key)`, `AttachmentUpdate(...)` (opcionales), `ReorderRequest` reutilizado.

`fecha_version` es `datetime.date`; `campos_dinamicos` es `dict[str, Any] | None`. La validacion de forma
(tipos/longitudes) produce `422`; las reglas condicionales quedan para SPEC-005.

### Routers (`app/api/routers/`)

Todos con `prefix="/api/v1"` y `tags` por recurso. Sin logica de negocio: validan entrada, invocan el caso de uso
y serializan.

`requirements.py`
| Metodo | Ruta | Caso de uso | Exito |
|---|---|---|---|
| POST | `/requerimientos` | `CreateRequirement` | 201 `RequirementResponse` |
| GET | `/requerimientos?estado=&folio=&page=&size=` | `ListRequirements` | 200 `RequirementPage` |
| GET | `/requerimientos/{id}` | `GetRequirement` | 200 `RequirementResponse` |
| GET | `/requerimientos/{id}/versiones` | `ListVersions` | 200 `list[VersionResponse]` |
| GET | `/requerimientos/{id}/versiones/{vid}` | `GetVersion` | 200 `VersionResponse` |
| PATCH | `/requerimientos/{id}/versiones/{vid}` | `UpdateVersion` | 200 `VersionResponse` |
| POST | `/requerimientos/{id}/versiones` | `FreezeAndAdvance` | 201 `RequirementResponse` |
| POST | `/requerimientos/{id}/estado` | `ChangeStatus` | 200 `RequirementResponse` |

`collections.py` — `{c}` ∈ `objetivos`, `consideraciones`, `beneficios`, `restricciones`, `volumetria`,
`riesgos`, `requisitos-futuros` (mapa explicito nombre-recurso → `CollectionKind`).
| Metodo | Ruta | Caso de uso | Exito |
|---|---|---|---|
| POST | `/requerimientos/{id}/versiones/{vid}/{c}` | `AddCollectionItem` | 201 `VersionResponse` |
| PATCH | `/requerimientos/{id}/versiones/{vid}/{c}/{itemId}` | `UpdateCollectionItem` | 200 `VersionResponse` |
| DELETE | `/requerimientos/{id}/versiones/{vid}/{c}/{itemId}` | `DeleteCollectionItem` | 204 |
| PUT | `/requerimientos/{id}/versiones/{vid}/{c}/orden` | `ReorderCollectionItems` | 200 `VersionResponse` |

`signatures.py`
| POST | `/requerimientos/{id}/versiones/{vid}/firmas` | `RegisterSignature` | 201 `SignatureResponse` |

`attachments.py`
| POST | `/requerimientos/{id}/versiones/{vid}/anexos` | `AddAttachment` | 201 `AttachmentResponse` |
| PATCH | `/requerimientos/{id}/versiones/{vid}/anexos/{aid}` | `UpdateAttachment` | 200 `AttachmentResponse` |
| DELETE | `/requerimientos/{id}/versiones/{vid}/anexos/{aid}` | `DeleteAttachment` | 204 |
| PUT | `/requerimientos/{id}/versiones/{vid}/anexos/orden` | `ReorderAttachments` | 200 `list[AttachmentResponse]` |

`catalogs.py`
| GET | `/catalogos/tipos-cambio` | `ListChangeTypes` | 200 `list[ChangeTypeResponse]` |
| GET | `/catalogos/cargos?rol=` | `ListPositions` | 200 `list[PositionResponse]` |

### Errores y `exception_handler` global (`app/api/errors.py`)

Handlers registrados en `create_app()`:

| Excepcion | HTTP | `code` |
|---|---|---|
| `InvalidStateTransitionError` | 409 | `invalid_state_transition` |
| `AuthorizationNotOnCurrentVersionError` | 409 | `authorization_not_on_current_version` |
| `MultipleWorkingVersionsError` | 409 | `multiple_working_versions` |
| `RequirementNotEditableError` | 409 | `not_editable` |
| `SignatureNotAllowedError` | 409 | `signature_not_allowed` |
| `DuplicateFolioError` | 409 | `duplicate_folio` |
| `DataConflictError` | 409 | `data_conflict` |
| `DomainError` (resto) | 409 | `domain_error` |
| `RequirementNotFoundError` | 404 | `requirement_not_found` |
| `VersionNotFoundError` | 404 | `version_not_found` |
| `CollectionItemNotFoundError` | 404 | `collection_item_not_found` |
| `AttachmentNotFoundError` | 404 | `attachment_not_found` |
| `InvalidFolioError` | 422 | `invalid_folio` |
| `RequestValidationError` (Pydantic) | 422 | `validation_error` (`details` = errores) |
| `StarletteHTTPException` | propio | `http_error` |

`details` siempre `object | null`; `message` en espanol; `code` estable por tipo. Con esto la API no filtra
`detail` crudo de FastAPI (CA-02 exige el envelope en folio duplicado).

### Cableado (`app/api/dependencies.py` y `app/main.py`)

- `dependencies.py`: `get_requirement_repository()`, `get_change_type_catalog()`, `get_position_catalog()` y
  `get_auth_provider()` (reusan `get_engine()`), mas fabricas de caso de uso que reciben puertos por `Depends`
  (patron de `get_check_health_use_case`), de forma que los tests puedan sustituir los puertos.
- `main.py`: registrar los routers nuevos con `prefix="/api/v1"` y los `exception_handler`. `health`/`version`
  sin cambios.

## Frontend (pantallas, componentes, estado)

No aplica (SPEC-004). No se toca `frontend/`.

## Docker / configuracion

Sin cambios de imagenes ni `docker-compose.yml`. Se reutiliza la conexion Oracle y `AI_PROVIDER=none`
(RF-16). No se agregan dependencias: FastAPI + Pydantic v2 + SQLAlchemy 2.x ya estan en `pyproject.toml`.

## Documentacion

- `doc/technical/api.md` (nuevo): prefijo, envelope de error, catalogo de endpoints, codigos HTTP, convencion de
  nombres de recursos de colecciones y referencia a `/openapi.json` (RF-15). No existia (`doc/technical/` tenia
  solo `.gitkeep`).

## Estrategia de pruebas

- **Dominio** (`tests/domain/`): `ensure_editable`/`ensure_working` y helpers de `collections.py` (alta con
  `order` incremental, baja logica, reorden segun ids, `Benefit` con `tipo`), sin BD.
- **Casos de uso** (`tests/application/`): con un `InMemoryRequirementRepository`/catalogos falsos. Cubren
  crear (CA-01/CA-02), versionar copy-on-write (CA-09), cambio de estado (CA-10), edicion solo en BORRADOR
  (CA-05), colecciones (CA-06/CA-07), firmas y `AUTORIZO` en vigente (CA-08), catalogos (CA-11).
- **API** (`tests/api/`): `TestClient` con `dependency_overrides` de los puertos (patron de
  `tests/api/test_health.py`). Cubren status codes, envelope `{items,total,page,size}` (CA-03), 404 (CA-04),
  409 de folio/estado/firma/version (CA-02/CA-05/CA-08/CA-10) y contrato del envelope de error.
- **Integracion** (`tests/integration/`, marcados `integration`): `search` paginado/filtrado, traduccion de
  `IntegrityError`→`DuplicateFolioError` y **estabilidad de ids** de colecciones/firmas/anexos entre escrituras,
  ademas del reorden sin violar el UQ, contra Oracle (RF-14). Se reutiliza `oracle_url`/`migrated_engine`.
- **Calidad** (CA-12): `ruff check .`, `mypy --strict app` y `pytest` sin errores; `GET /openapi.json` expone
  todos los endpoints.

## Riesgos y decisiones (ADRs relacionados)

- **IDs de sub-recursos (resuelto por diseño)**: en SPEC-002 `save` reemplazaba los hijos (ids efimeros,
  auditoría reiniciada). Aqui el adaptador hace **upsert por fila** (ver arriba), de modo que los `id` de
  colecciones/firmas/anexos son estables entre escrituras; se cubre con prueba de integracion. El reorden en
  dos fases evita violar el UQ `(VERSION_ID, ORDEN)`.
- **`search` carga agregados completos por pagina**: simple y correcto; costo acotado por `size`. Deuda:
  proyeccion ligera si el listado crece.
- **`authorize` acepta `version_id=None`** (H-07/DT-06): el caso de uso valida que la version exista en el
  agregado antes de firmar; prueba de API dedicada (CA-08).
- **Mapeo de errores inconsistente**: un unico modulo de handlers y `code` estable por error; prueba de contrato
  del envelope.
- **Convencion de recursos vs nombres de dominio**: mapa explicito en `collections.py` + `api.md`.
- **Edicion concurrente del borrador** (DT-03): documentada; sin bloqueo optimista en esta spec.
- **FK/check invalidos** (p. ej. `tipo_cambio_id` inexistente) llegan como `IntegrityError`: el adaptador los
  traduce a `DataConflictError` (409) en lugar de un 500.
- ADR-002 (hexagonal), ADR-003 (auth como punto de extension), ADR-005 (firmas/estados),
  ADR-006 (anexos solo metadato), ADR-007 (firmas solo en estado final y version vigente).
