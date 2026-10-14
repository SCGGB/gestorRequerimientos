# Tareas - SPEC-002

> Ordenadas por dependencia. Cada tarea es atomica y verificable. Las migraciones se aplican solo con
> Alembic; no se escribe DDL a mano. No se implementan casos de uso/endpoints (SPEC-003), wizard (SPEC-004),
> validaciones ejecutables ni DOCX/PDF (SPEC-005/007), IA real (SPEC-006) ni auth/JWT (SPEC-008).

## Dominio (Python puro, sin BD)

- [x] T-01 (CA-06, RF-01, RF-02, RF-03) `domain/requirement/enums.py` (`RequirementStatus`, `BenefitKind`, `SignatureRole`, `ActiveFlag`) y `domain/requirement/errors.py` (`DomainError`, `InvalidStateTransitionError`, `AuthorizationNotOnCurrentVersionError`, `MultipleWorkingVersionsError`, `InvalidFolioError`).
- [x] T-02 (RF-05, RF-06) `domain/requirement/items.py`: base `CollectionItem(id, order, content, active)` y subclases `Objective`, `Consideration`, `Restriction`, `Volumetry`, `Risk`, `FutureRequirementItem`, `Benefit(+ kind: BenefitKind)`.
- [x] T-03 (RF-03, RF-07, RF-08, RF-09, RF-10) `domain/requirement/{catalog,signature,attachment,version}.py`: `ChangeType`, `Position`, `Signature`, `Attachment` y `RequirementVersion` (escalares, colecciones, firmas, anexos, `CAMPOS_DINAMICOS` como `Mapping`, `frozen`, `freeze()`, `is_working()`, accesores de colecciones activas).
- [x] T-04 (CA-05, CA-06, CA-07, RF-01, RF-02, RF-03, RF-04, RF-08) `domain/requirement/requirement.py`: agregado `Requirement` con `ticket`, `working_version`, `current_version`, `change_status` (mapa de transiciones, `InvalidStateTransitionError`), `freeze_and_advance` (copy-on-write: solo `active=True`, preserva `order`, nueva version de trabajo unica) y `authorize` (solo version vigente).
- [x] T-05 (CA-05, CA-06, CA-07) `tests/domain/test_requirement.py`: transiciones validas/invalidas, `ticket` `T#folio`, version unica no congelada, copy-on-write preserva activos y orden, `authorize` rechaza version no vigente, `Benefit` con discriminador. Sin base de datos.

## Esquema Oracle y migracion

- [x] T-06 (CA-01, CA-02, RF-11) `alembic/versions/0002_modelo_requerimiento.py` (`down_revision = "0001_base"`): crea `REQ_TIPO_CAMBIO`, `REQ_CARGO`, `REQ_REQUERIMIENTO`, `REQ_VERSION`, las 7 tablas de coleccion, `REQ_ANEXO` y `REQ_FIRMA` con auditoria, checks (`ESTADO`, `ACTIVO`, `CONGELADA`, `TIPO`, `ROL`, `CAMPOS_DINAMICOS IS JSON`), FKs (incluida `VERSION_ACTUAL_ID` diferida), UQ (`FOLIO`, `(REQUERIMIENTO_ID, NUMERO_VERSION)`, `(VERSION_ID, ORDEN)`) e indices; siembra los 6 tipos de cambio y los cargos predeterminados por rol; `downgrade()` revierte en orden inverso sin residuos.
- [x] T-07 (CA-01, CA-02, CA-08) `tests/integration/test_migration_requerimiento.py` (marcados `integration`): `alembic upgrade head` crea las 13 tablas con sus columnas de auditoria (CA-01), los catalogos quedan sembrados (CA-02) y `downgrade` las elimina; verificacion de que `CAMPOS_DINAMICOS` acepta JSON valido (CA-08).

## Puertos y adaptadores de persistencia

- [x] T-08 (RF-12) `application/ports/{requirement_repository,catalog_repository,storage}.py`: `RequirementRepository` (`save`, `get`, `get_by_folio`, `list`), `ChangeTypeCatalog`, `PositionCatalog` y el marcador `StoragePort` (sin adaptador real). Firmas sin tipos de SQLAlchemy.
- [x] T-09 (CA-03, RF-12) `infrastructure/db/tables.py`: `MetaData` propio y `Table(...)` de las 13 tablas como espejo del DDL de la migracion (tipos, checks, PK/FK/indices).
- [x] T-10 (CA-03, RF-12) `infrastructure/db/mappers.py`: mappers explicitos dominio<->fila para contenedor, version, colecciones, beneficios, firmas, anexos y catalogos (serializacion/deserializacion de `CAMPOS_DINAMICOS`).
- [x] T-11 (CA-03, RF-12) `infrastructure/adapters/{requirement_repository,catalogs}.py`: `SqlAlchemyRequirementRepository` (upsert y carga del agregado completo en transaccion, usando `create_session_factory`) y adaptadores de catalogos; fijan `CREATED_BY`/`UPDATED_BY = "SYSTEM"` y timestamps del sistema.
- [x] T-12 (CA-03, CA-04, CA-08) `tests/infrastructure/test_mappers.py` (ida y vuelta sin BD) y `tests/integration/test_requirement_repository.py` (marcados `integration`): guardar/recuperar agregado completo (CA-03), folio duplicado rechazado (CA-04), JSON invalido rechazado por `IS JSON` (CA-08).

## Calidad

- [x] T-13 (CA-09) Verificar tooling: `ruff check .`, `mypy --strict backend/app` y `pytest` sin errores (integracion via `pytest -m integration` con Docker/Oracle).
