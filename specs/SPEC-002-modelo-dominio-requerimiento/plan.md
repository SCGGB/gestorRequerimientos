# Plan tecnico - SPEC-002

> Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`,
> `doc/documents/mapeo-machote.md`, `doc/development/convenciones.md`,
> `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`,
> `doc/architecture/adr/004-plantilla-docxtpl-derivada.md`,
> `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/006-almacenamiento-objetos-dev.md`.
> Esta spec es de dominio y persistencia: **no** incluye casos de uso/endpoints (SPEC-003), wizard (SPEC-004),
> validaciones ejecutables ni generacion DOCX/PDF (SPEC-005/007), IA real (SPEC-006) ni auth/JWT (SPEC-008).

## Enfoque

Construir el modelo estructurado del requerimiento como **fuente de verdad** en Oracle y exponerlo al resto
del sistema unicamente a traves de puertos. El trabajo se separa en cuatro frentes en este orden:

1. **Esquema Oracle** (`0002_modelo_requerimiento`): contenedor + versiones + colecciones + firmas + anexos +
   catalogos, con auditoria, checks, FKs, indices y datos semilla. Reversible (`downgrade`).
2. **Dominio puro** (`app/domain/requirement/`): entidades, objetos de valor, enumeraciones e invariantes
   (transiciones de estado, version unica no congelada, copy-on-write al congelar, Autorizo solo en la version
   vigente). Sin imports de FastAPI/SQLAlchemy/docxtpl/IA.
3. **Puertos** (`app/application/ports/`): `RequirementRepository`, `ChangeTypeCatalog`, `PositionCatalog` y el
   marcador `StoragePort` (ausente desde SPEC-001; se anade aqui como puerto documentado, sin adaptador real).
4. **Adaptadores** (`app/infrastructure/`): tablas SQLAlchemy 2.x Core en un `MetaData` propio, mappers
   explicitos dominio<->fila y repositorios que no filtran tipos de SQLAlchemy al dominio.

Decisiones ya fijadas en `spec.md` (no contradecir): `FOLIO` numerico unico; `CAMPOS_DINAMICOS` CLOB con
`CHECK (... IS JSON)`; auditoria con `CREATED_AT/UPDATED_AT` del sistema y `CREATED_BY/UPDATED_BY = 'SYSTEM'`
hasta SPEC-008.

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic

Revision `0002_modelo_requerimiento` (`down_revision = "0001_base"`). Prefijo de modulo `REQ`, tablas en
singular, MAYUSCULAS. Toda tabla lleva `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY`. PK `ID`
`NUMBER GENERATED ALWAYS AS IDENTITY`. DDL **solo** por Alembic.

### Catalogos (se sembrados en la migracion)

| Tabla | Columnas | Restricciones |
|---|---|---|
| `REQ_TIPO_CAMBIO` | `ID`, `CODIGO` VARCHAR2(50), `NOMBRE` VARCHAR2(100), `ACTIVO` CHAR(1), auditoria | PK; `ACTIVO IN ('S','N')`; UQ `CODIGO` |
| `REQ_CARGO` | `ID`, `ROL` VARCHAR2(20), `NOMBRE` VARCHAR2(100), `PREDETERMINADO` CHAR(1), `ACTIVO` CHAR(1), auditoria | PK; `ROL IN ('ELABORO','REVISO','AUTORIZO')`; `PREDETERMINADO IN ('S','N')`; `ACTIVO IN ('S','N')`; IX `(ROL)` |

Semilla `REQ_TIPO_CAMBIO` (6, RF del producto): `NUEVA_FUNCIONALIDAD`, `CORRECCION`, `REPORTE`,
`INTEGRACION`, `BASE_DATOS`, `MEJORA_TECNICA` con su `NOMBRE` en espanol y `ACTIVO='S'`.
Semilla `REQ_CARGO`: un registro predeterminado por rol (`ELABORO`, `REVISO`, `AUTORIZO`) con `PREDETERMINADO='S'`.

### Contenedor y version

| Tabla | Columnas | Notas |
|---|---|---|
| `REQ_REQUERIMIENTO` | `ID`, `FOLIO` NUMBER(19), `ESTADO` VARCHAR2(20), `VERSION_ACTUAL_ID` NUMBER, auditoria | UQ `FOLIO`; `ESTADO IN ('BORRADOR','EN_REVISION','VALIDADO','APROBADO','GENERADO','CANCELADO')`; FK diferida a `REQ_VERSION(ID)` (nullable) |
| `REQ_VERSION` | `ID`, `REQUERIMIENTO_ID`, `NUMERO_VERSION` NUMBER(10), `VERSION_DOCUMENTO` VARCHAR2(20), `FECHA_VERSION` DATE, `TITULO` VARCHAR2(300), `TIPO_CAMBIO_ID`, `SISTEMA` VARCHAR2(200), `NECESIDAD_ACTUAL` CLOB, `CONTEXTO_DESCRIPCION` CLOB, `CONTEXTO_MANEJO_ERRORES` CLOB, `USUARIOS_PERMISOS` CLOB, `REQUISITOS_FUTUROS_APLICA` CHAR(1), `REQUISITOS_FUTUROS_TEXTO` CLOB, `CAMPOS_DINAMICOS` CLOB, `CONGELADA` CHAR(1), auditoria | FK `REQUERIMIENTO_ID`; FK `TIPO_CAMBIO_ID`; UQ `(REQUERIMIENTO_ID, NUMERO_VERSION)`; `CONGELADA IN ('S','N')`; `REQUISITOS_FUTUROS_APLICA IN ('S','N')`; `CHECK (CAMPOS_DINAMICOS IS JSON)`; IX `(REQUERIMIENTO_ID)` |

La FK circular `REQ_REQUERIMIENTO.VERSION_ACTUAL_ID -> REQ_VERSION.ID` se crea despues de ambas tablas con
`op.create_foreign_key`. `downgrade()` la elimina en orden inverso.

### Colecciones ordenadas

Tablas `REQ_OBJETIVO`, `REQ_CONSIDERACION`, `REQ_RESTRICCION`, `REQ_VOLUMETRIA`, `REQ_RIESGO`,
`REQ_REQUISITO_FUTURO`: `ID`, `VERSION_ID`, `ORDEN` NUMBER(10), `CONTENIDO` CLOB, `ACTIVO` CHAR(1), auditoria.
FK `VERSION_ID -> REQ_VERSION(ID)`; `ACTIVO IN ('S','N')`; UQ `(VERSION_ID, ORDEN)`; IX `(VERSION_ID)`.

`REQ_BENEFICIO`: identica mas `TIPO` VARCHAR2(15) con `TIPO IN ('CUALITATIVO','CUANTITATIVO')` (RF-06).
Los requisitos futuros narrativos usan `REQ_VERSION.REQUISITOS_FUTUROS_APLICA/TEXTO`; la coleccion
`REQ_REQUISITO_FUTURO` cubre la lista cuando aplica (mapeo del machote, seccion 8).

### Anexos, firmas y auditoria

| Tabla | Columnas | Restricciones |
|---|---|---|
| `REQ_ANEXO` | `ID`, `VERSION_ID`, `ORDEN` NUMBER(10), `NOMBRE` VARCHAR2(255), `TIPO_MIME` VARCHAR2(100), `STORAGE_KEY` VARCHAR2(500), `LEYENDA` VARCHAR2(255), `ACTIVO` CHAR(1), auditoria | FK `VERSION_ID`; `ACTIVO IN ('S','N')`; el binario **no** se guarda en Oracle (RF-10, ADR-006) |
| `REQ_FIRMA` | `ID`, `VERSION_ID`, `ROL` VARCHAR2(20), `NOMBRE` VARCHAR2(150), `CARGO` VARCHAR2(150), `CARGO_ID` NUMBER, auditoria | FK `VERSION_ID`; FK `CARGO_ID -> REQ_CARGO(ID)`; `ROL IN ('ELABORO','REVISO','AUTORIZO')`; IX `(VERSION_ID)` |

Cada tabla de coleccion/anexo/firma hereda los `CREATED_*`/`UPDATED_*`. La migracion siembra catalogos en
`upgrade()` y `downgrade()` elimina tablas en orden inverso (hijos antes que padres) sin residuos (CA-01).

## Dominio y casos de uso

Paquete `backend/app/domain/requirement/` (Python puro, `dataclass(frozen=True, slots=True)` y `StrEnum` como
en `domain/health.py`). Nombres de codigo en ingles.

- `enums.py`
  - `RequirementStatus(StrEnum)`: `BORRADOR`, `EN_REVISION`, `VALIDADO`, `APROBADO`, `GENERADO`, `CANCELADO`.
  - `BenefitKind(StrEnum)`: `CUALITATIVO`, `CUANTITATIVO`.
  - `SignatureRole(StrEnum)`: `ELABORO`, `REVISO`, `AUTORIZO`.
  - `ActiveFlag(StrEnum)`: `S`, `N` (uso interno dominio<->persistencia).
- `errors.py`: `DomainError`, `InvalidStateTransitionError`, `AuthorizationNotOnCurrentVersionError`,
  `MultipleWorkingVersionsError`, `InvalidFolioError`.
- `catalog.py`: `ChangeType(id, code, name, active)`, `Position(id, role, name, is_default, active)`.
- `items.py`: base `CollectionItem(id, order, content, active)` y subclases `Objective`, `Consideration`,
  `Restriction`, `Volumetry`, `Risk`, `FutureRequirementItem` y `Benefit(..., kind: BenefitKind)`.
- `signature.py`: `Signature(id, version_id, role, name, position, position_id)`.
- `attachment.py`: `Attachment(id, version_id, order, name, mime_type, storage_key, caption, active)`.
- `version.py`: `RequirementVersion(...)` con colecciones, firmas, anexos, escalares y `frozen`. Metodos:
  `freeze()`, `is_working()`, `active_objectives()` (y analogos por coleccion), `add_signature(signature)`
  (rechaza `AUTORIZO` via `InvalidStateTransition`/error dedicado si la version no es vigente).
- `requirement.py`: agregado `Requirement(id, folio, status, current_version_id, versions)`.
  - `ticket` -> `f"T#{folio}"` (RF-02).
  - `working_version()` -> la unica version no congelada; `current_version()` -> la referenciada por
    `current_version_id` (RF-03).
  - `change_status(target)` valida contra un mapa de transiciones permitidas
    (`BORRADOR->EN_REVISION|CANCELADO`, `EN_REVISION->VALIDADO|BORRADOR|CANCELADO`,
    `VALIDADO->APROBADO|EN_REVISION|CANCELADO`, `APROBADO->GENERADO|CANCELADO`,     terminales sin salida);
    lanza `InvalidStateTransitionError` (CA-06).
  - `freeze_and_advance()` implementa copy-on-write (RF-04/CA-05): congela la version de trabajo, crea la
    version `N+1` copiando solo los elementos con `active=True`, preservando `order`, y actualiza
    `current_version_id`. Copia tambien los escalares como borrador de partida (documentado).
  - `authorize(version_id, ...)` acepta `AUTORIZO` solo si `version_id == current_version_id`
    (CA-07/RF-08); `ELABORO`/`REVISO` se registran por cualquier version via `version.add_signature`.
  - Invariante: como maximo una version no congelada; `freeze_and_advance` y cualquier alta lo verifican
    (`MultipleWorkingVersionsError`).

No se implementan casos de uso de negocio (SPEC-003): el dominio queda listo para que esos casos lo invoquen.

## Puertos y adaptadores afectados

- `application/ports/requirement_repository.py`:
  - `RequirementRepository(ABC)`: `save(requirement) -> Requirement` (upsert de contenedor, versiones,
    colecciones, firmas y anexos), `get(requirement_id) -> Requirement`, `get_by_folio(folio) -> Requirement | None`,
    `list() -> Sequence[Requirement]`. Firma sin tipos de SQLAlchemy.
- `application/ports/catalog_repository.py`:
  - `ChangeTypeCatalog(ABC)`: `list_active() -> Sequence[ChangeType]`, `get(change_type_id) -> ChangeType | None`.
  - `PositionCatalog(ABC)`: `list_by_role(role) -> Sequence[Position]`, `get(position_id) -> Position | None`.
- `application/ports/storage.py`:
  - `StoragePort(ABC)` marcador (`put`/`get`/`delete` por `key`) que documenta la resolucion del binario de
    anexos fuera de Oracle (RF-10, ADR-006). **Sin adaptador real** en esta spec.
- `infrastructure/db/tables.py`: `metadata = MetaData()` + `Table(...)` para las 13 tablas, espejo exacto del
  DDL de la migracion (tipos `String`, `Numeric`, `Text`, `CheckConstraint`, `Identity`).
- `infrastructure/db/mappers.py`: funciones `to_domain_*`/`to_row_*` explicitas por entidad (evitan divergencia
  entre nombres de dominio y columnas).
- `infrastructure/adapters/requirement_repository.py`: `SqlAlchemyRequirementRepository` que usa
  `create_session_factory` de `infrastructure/database.py`, transacciones y los mappers; no expone filas ni
  tipos de SQLAlchemy al dominio.
- `infrastructure/adapters/catalogs.py`: `SqlAlchemyChangeTypeCatalog`, `SqlAlchemyPositionCatalog`.
- Los adaptadores fijan `CREATED_BY`/`UPDATED_BY = "SYSTEM"` y `CREATED_AT`/`UPDATED_AT = now` (decision de
  `spec.md`).

## API (endpoints, contratos, errores)

No aplica en esta spec. Los endpoints de requerimientos y catalogos llegan en SPEC-003. `main.py` no cambia.

## Frontend (pantallas, componentes, estado)

No aplica en esta spec (SPEC-004). No se toca `frontend/`.

## Docker / configuracion

Sin cambios de imagenes ni de `docker-compose.yml`. Se reutiliza la conexion Oracle (`oracle-free` en dev)
ya provista por SPEC-001 (`infrastructure/database.py`, `config.py`). La migracion debe correr contra la misma
conexion thin.

## Estrategia de pruebas

- **Dominio** (`tests/domain/`, sin BD): transiciones validas/invalidas (CA-06), `ticket` `T#folio`, version
  unica no congelada, `freeze_and_advance` copia solo activos preservando orden (CA-05), `authorize` rechaza
  version no vigente (CA-07), `Benefit` con discriminador.
- **Mappers** (`tests/infrastructure/`, sin BD): ida y vuelta dominio->fila->dominio conserva contenido, orden,
  activo y escalares; serializacion JSON de `CAMPOS_DINAMICOS`.
- **Integracion** (`pytest -m integration` + Testcontainers Oracle, `tests/integration/conftest.py`):
  - `test_migration_requerimiento.py`: `alembic upgrade head` crea las 13 tablas con sus columnas (CA-01),
    catalogos sembrados (CA-02) y `downgrade` elimina todo sin residuos.
  - `test_requirement_repository.py`: guardar/recuperar agregado completo con colecciones, firmas y anexos
    (CA-03); folio duplicado rechazado por unicidad (CA-04); JSON invalido rechazado por `IS JSON` (CA-08).
- **Calidad** (CA-09): `ruff check .`, `mypy --strict backend/app` y `pytest` sin errores. Los tests de
  integracion quedan marcados `integration` (excluidos por defecto en `pyproject.toml`).

## Riesgos y decisiones (ADRs relacionados)

- ADR-002 (hexagonal + Docker), ADR-005 (firmas/estados: Elaboro/Reviso por version, Autorizo en vigente),
  ADR-006 (anexos: metadato + `StoragePort`, binario fuera de Oracle), ADR-004 (la plantilla solo afecta
  presentacion; el modelo no se acopla a DOCX).
- FK circular `VERSION_ACTUAL_ID`: se resuelve creando la FK despues de ambas tablas; `downgrade` la elimina
  primero.
- `IS JSON` en `oracle-free`: se usa `CLOB` (SQLAlchemy `Text`) como en `SYS_AUDITORIA`; verificar en CI.
- Copy-on-write: cubierto por prueba dedicada de congelado (activos + orden).
- **Supuesto a confirmar**: los `NOMBRE` semilla de `REQ_CARGO` por rol son valores predeterminados editables
  (no hay cargos institucionales en la documentacion); se siembra un unico cargo predeterminado por rol.
- `StoragePort` no existe pese a lo previsto en SPEC-001: se crea como marcador documentado, sin adaptador.
