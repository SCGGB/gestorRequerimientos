# Plan tecnico - SPEC-007-generacion-docx-pdf

## Enfoque

El backend genera el DOCX del requerimiento con `docxtpl` a partir de la plantilla derivada y versionada
`templates/ers_plantilla_v1.docx` (ADR-004), usando como unica entrada el contenido normalizado ya
existente (`PreviewDocument`, `build_preview_document`, SPEC-006). El PDF se obtiene convirtiendo el DOCX
generado con LibreOffice headless (ADR-001, ADR-002); no hay segundo motor. Ambos binarios se persisten
como BLOB en Oracle y cada uno se registra como fila independiente con su trazabilidad (RF-10). La
generacion es sincrona en la peticion (decision 3) y, tras el exito, el requerimiento transiciona
automaticamente a `GENERADO` (decision 4).

Decisiones de diseno:

- **Reutilizacion estricta del DTO**: el renderizador consume `PreviewDocument` y no recalcula reglas de
  negocio. La generacion invoca la misma composicion que la vista previa (`build_preview_document`),
  garantizando consistencia vista previa ↔ DOCX ↔ PDF (RF-01, RF-09, NFR).
- **Binarios en Oracle (BLOB)**: nueva tabla `REQ_DOCUMENTO` y adaptador de persistencia propio. No se usa
  `StoragePort`/ADR-006, reservado para anexos (`REQ_ANEXO.STORAGE_KEY`); se declara explicitamente en el
  plan y en `doc/technical/api.md`.
- **Hexagonal**: el dominio define la entidad `GeneratedDocument` y los puertos de render/conversion/
  persistencia viven en `application`; `docxtpl`, LibreOffice, Oracle y el manejo de ficheros temporales
  viven en `infrastructure`; el router solo valida, invoca y serializa.
- **Transicion de estado**: se reutiliza `Requirement.change_status(GENERADO)` y las precondiciones de
  `validate_requirement(..., target_state=GENERADO)` (firmas `ELABORO` y `AUTORIZO`, `APROBADO ->
  GENERADO`), sin duplicar la maquina de estados.
- **Plantilla**: se deriva una sola vez en un spike previo (Fase 0) y se versiona (`v1`, `v2`, ...). Cada
  documento registra `PLANTILLA_VERSION`. Los logotipos se reservan como espacio en el encabezado (deuda
  tecnica); no se incorporan imagenes.
- **Dependencia nueva justificada**: `docxtpl` (y su dependencia `python-docx`) es la libreria que fija
  ADR-001 para DOCX; es la unica dependencia nueva y no hay alternativa sin escribir el DOCX a mano.

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic

Nueva tabla `REQ_DOCUMENTO` en `backend/app/infrastructure/db/tables.py` (SQLAlchemy Core, mismo
`MetaData`):

| Columna | Tipo | Notas |
|---|---|---|
| `ID` | `Numeric(19,0)` PK | `NUMBER GENERATED ALWAYS AS IDENTITY` (mismo helper `_ID`) |
| `REQUERIMIENTO_ID` | `Numeric(19,0)` NOT NULL FK | → `REQ_REQUERIMIENTO.ID` |
| `VERSION_ID` | `Numeric(19,0)` NOT NULL FK | → `REQ_VERSION.ID`; version congelada usada |
| `FORMATO` | `String(10)` NOT NULL | `DOCX` o `PDF` (CHECK in lista) |
| `PLANTILLA_VERSION` | `String(20)` NOT NULL | p. ej. `v1` |
| `NOMBRE_ARCHIVO` | `String(300)` NOT NULL | `T#<folio>-v<version>.<ext>` |
| `MIME_TYPE` | `String(150)` NOT NULL | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` / `application/pdf` |
| `TAMANO_BYTES` | `Numeric(19,0)` NOT NULL | |
| `CONTENIDO` | `BLOB` NOT NULL | binario generado |
| `GENERADO_AT` | `TIMESTAMP` NOT NULL | fecha/hora de generacion |
| `GENERADO_BY` | `String(200)` NOT NULL | actor (valor por defecto mientras auth vive en SPEC-008) |
| `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY` | audit | helper `_audit_columns()` |

- Indices: `REQ_DOCUMENTO_REQUERIMIENTO_IX` (`REQUERIMIENTO_ID`), `REQ_DOCUMENTO_VERSION_IX`
  (`VERSION_ID`) y unique `REQ_DOCUMENTO_UQ` (`REQUERIMIENTO_ID`, `VERSION_ID`, `FORMATO`,
  `GENERADO_AT`) para permitir multiples generaciones sin sobrescribir (RF-13). Nombres segun el
  patron de `0002_modelo_requerimiento.py` (decision durante T-003).
- No se modifican tablas existentes; `REQ_REQUERIMIENTO.ESTADO` ya admite `GENERADO`.
- Migracion Alembic `backend/alembic/versions/0003_documentos_generados.py` con `revision =
  "0003_documentos_generados"`, `down_revision = "0002_modelo_requerimiento"`; `upgrade` crea tabla,
  FKs, checks, indices y auditoria; `downgrade` la elimina. DDL solo via Alembic.
- `target_metadata` sigue en `None`; se sigue el patron de `0002_modelo_requerimiento.py`.

## Dominio y casos de uso

### Dominio (puro)

Nuevo `backend/app/domain/requirement/document.py`:

- `DocumentFormat = Literal["DOCX", "PDF"]`; `MIME_TYPES: dict[DocumentFormat, str]`.
- `@dataclass(frozen=True, slots=True)` `GeneratedDocument`: `id: int | None`, `requirement_id: int`,
  `version_id: int`, `format: DocumentFormat`, `template_version: str`, `file_name: str`,
  `mime_type: str`, `size_bytes: int`, `generated_at: datetime`, `generated_by: str`, `content:
  bytes | None` (solo presente al descargar). Sin imports de FastAPI, SQLAlchemy, docxtpl ni LibreOffice.
- Helper puro `build_file_name(folio: int, document_version: str, file_format: DocumentFormat) -> str`
  → `T#<folio>-v<document_version>.<ext>` (RF-19). `folio` es `int` porque `Requirement.folio` es entero
  (el prefijo `T#` lo agrega el helper).

Sin cambios en `enums.py`, `requirement.py`, `version.py`, `preview.py` (se reutilizan tal cual). Los
codigos de error de dominio/aplicacion existentes (`InvalidStateTransitionError`,
`RequirementNotEditableError`, errores de validacion) ya cubren las precondiciones.

### Aplicacion

Puertos nuevos (`backend/app/application/ports/`):

- `document_renderer.py` — `DocumentRendererPort` ABC: `render_docx(document: PreviewDocument,
  template_version: str) -> bytes` (RF-01, RF-02).
- `document_converter.py` — `DocumentConverterPort` ABC: `to_pdf(docx: bytes) -> bytes` (RF-09).
- `requirement_document_repository.py` — `RequirementDocumentRepository` ABC: `add(document) -> int`,
  `get(document_id) -> GeneratedDocument` (con `content`), `list_by_requirement(requirement_id) ->
  list[GeneratedDocument]` (sin `content`).

Export en `ports/__init__.py` (`__all__`; hoy solo exporta `DatabaseHealthPort`).

Casos de uso (`backend/app/application/use_cases/requirement/`):

- `generate_documents.py` — `GenerateRequirementDocuments`:
  1. `repository.get(requirement_id)` → `RequirementNotFoundError`.
  2. `requirement.version_by_id(version_id)` o `requirement.current_version()` → `VersionNotFoundError`.
  3. Precondiciones: `requirement.ensure_editable()`/estado `APROBADO` y firmas requeridas via
     `validate_requirement(requirement, version, target_state=GENERADO)` (no duplica reglas).
  4. `preview = build_preview_document(requirement, version)`.
  5. `docx = renderer.render_docx(preview, template_version)`.
  6. `pdf = converter.to_pdf(docx)`.
  7. Persiste dos filas (DOCX y PDF) con `document_repository.add(...)` (RF-10, RF-13).
  8. `requirement.change_status(RequirementStatus.GENERADO)` y `repository.save(requirement)` (RF-12,
     decision 4). Todo sincrono; si falla render/conversion/persistencia no se registra nada y no hay
     transicion (RF-11, CA-10).
  Devuelve los `GeneratedDocument` (sin `content`).
- `get_document.py` — `GetRequirementDocument`: recupera un documento por id y valida pertenencia al
  requerimiento; devuelve `GeneratedDocument` con `content` para la descarga (RF-13).
- `list_documents.py` — `ListRequirementDocuments`: historico ordenado por `GENERADO_AT` descendente,
  sin `content` (RF-13, retencion "conservar todo").

Export en `use_cases/requirement/__init__.py` (`__all__`). Patron identico a `build_preview_document.py`.

## Puertos y adaptadores afectados

- **Adaptadores nuevos** (`backend/app/infrastructure/adapters/`):
  - `document_renderer.py` — `DocxtplDocumentRenderer`: carga `templates/<archivo>` desde
    `Settings.templates_dir`, `Environment(autoescape=True)`, contexto = `PreviewDocument` mapeado a
    variables de plantilla (secciones, colecciones, control de versiones, firmas, encabezado),
    `RichText`/`Listing` para saltos de linea (RF-08). Devuelve `bytes` del DOCX en memoria.
  - `document_converter.py` — `LibreofficeDocumentConverter`: escribe el DOCX en un `TemporaryDirectory`,
    invoca `soffice --headless --convert-to pdf --outdir <dir> <docx>` (`Settings.libreoffice_binary`,
    `Settings.document_generation_timeout_seconds`), valida la salida y devuelve los `bytes` del PDF.
    Si no hay binario o falla el proceso → error de infraestructura mapeado a 500 (RF-15).
  - `requirement_document_repository.py` — `SqlAlchemyRequirementDocumentRepository` (SQLAlchemy Core,
    mismo `Engine`/`sessionmaker` que `SqlAlchemyRequirementRepository`): inserta/lee BLOB con
    `oracledb`; mappers en `db/mappers.py` para fila ↔ `GeneratedDocument`.
- **Tablas**: `REQ_DOCUMENTO` nueva en `db/tables.py` (ver arriba).
- **`requirement_repository.py`**: sin cambios; el caso de uso reutiliza `get`/`save`.
- **Configuracion**: `backend/app/infrastructure/config.py` — nuevas `Settings`: `templates_dir: str =
  "/app/templates"`, `document_template_version: str = "v1"`, `libreoffice_binary: str = "soffice"`,
  `document_generation_timeout_seconds: int = 60`, `document_max_bytes: int` (limite defensivo).
  Actualizar `.env.example`.

## API (endpoints, contratos, errores)

Router nuevo `backend/app/api/routers/documents.py` (`APIRouter(prefix="/api/v1", tags=["documentos"])`),
registrado en `backend/app/main.py`:

- `POST /api/v1/requerimientos/{requerimiento_id}/documentos` — genera DOCX y PDF de la version vigente
  (o `version_id` opcional en el body). Sincrono. `response_model=list[GeneratedDocumentResponse]`
  (metadatos sin binario). `201`. Errores: `404 requirement_not_found`/`version_not_found`; `409`
  estado o firmas no permiten generar; `422` validacion; `500` fallo de generacion/conversion.
- `GET /api/v1/requerimientos/{requerimiento_id}/documentos` — historico completo (sin binario),
  `response_model=list[GeneratedDocumentResponse]`, `200` (RF-13).
- `GET /api/v1/requerimientos/{requerimiento_id}/documentos/{documento_id}/descarga` — devuelve el
  binario con `FileResponse` (o `Response`) y `Content-Disposition: attachment;
  filename="T#<folio>-v<version>.<ext>"`, `media_type` segun formato (RF-19, CA-16). `404` si no existe
  o no pertenece al requerimiento.

Esquemas nuevos `backend/app/api/schemas/document.py` (re-export en `schemas/__init__.py`):
`GeneratedDocumentResponse` (`id`, `formato`, `version_id`, `plantilla_version`, `nombre_archivo`,
`mime_type`, `tamano_bytes`, `generado_at`, `generado_by`) con `from_domain(...)`. Sin campos binarios.

Dependencias nuevas en `backend/app/api/dependencies.py`: `get_document_renderer`,
`get_document_converter`, `get_requirement_document_repository` y las factorias
`get_generate_documents_use_case`, `get_get_document_use_case`, `get_list_documents_use_case` (patron
`Annotated[..., Depends(...)]` existente).

Errores: se reutiliza el envelope unico de `backend/app/api/errors.py` (`{error:{code,message,details}}`).
Agregar mapeo de error de conversion/render → `document_generation_failed` (500) con mensaje en espanol.

Documentacion: `doc/technical/api.md` — nueva seccion `### Documentos generados (SPEC-007)` con las tres
rutas, y resumen de `GeneratedDocumentResponse` en "Esquemas principales"; nota de BLOB en Oracle y de que
el contrato de contenido es el `PreviewDocument` de SPEC-006.

## Frontend (pantallas, componentes, estado)

### Cliente y tipos

- `frontend/src/api/types.ts`: `GeneratedDocument` (`id`, `formato`, `version_id`, `plantilla_version`,
  `nombre_archivo`, `mime_type`, `tamano_bytes`, `generado_at`, `generado_by`).
- `frontend/src/api/documents.ts`: `generateDocuments(requerimientoId): Promise<GeneratedDocument[]>`,
  `listDocuments(requerimientoId): Promise<GeneratedDocument[]>`, `downloadDocument(requerimientoId,
  documentoId): Promise<{ blob: Blob; fileName: string }>`. Export en `api/index.ts`.
- `frontend/src/api/client.ts`: nueva funcion `requestBlob(path)` que hace `fetch`, valida `response.ok`
  (reutiliza `ApiError`/envelope en error) y devuelve `{ blob, fileName }` leyendo `Content-Disposition`.
  El `request<T>()` JSON actual no se toca.

### Hook

- `frontend/src/hooks/useRequirementDocuments.ts`, patron `{ data, loading, error, reload }` de
  `usePreview.ts`: carga el historico al activarse, expone `generate()` (llama a `generateDocuments` y
  recarga) y `download(documentoId)` (dispara la descarga con `URL.createObjectURL` + `<a download>`).
  Maneja estados de carga/error sin romper el wizard (RF-14, RF-15).

### Componentes (en `frontend/src/features/wizard/components/preview/` o nueva subcarpeta `documents/`)

- `DocumentActions.tsx`: boton "Generar DOCX/PDF" y boton "Descargar" por documento; deshabilitado con
  el motivo visible cuando el estado no lo permite (RF-14, CA-13); mensajes de exito/error.
- `DocumentHistory.tsx`: lista del historico (formato, fecha, tamano, enlace de descarga).
- Integracion en `Step13Review.tsx`: agregar `DocumentActions`/`DocumentHistory` debajo de la vista
  previa; el motivo de deshabilitado se deriva del `RequirementStatus` del requerimiento cargado.

Tokens de `src/index.css` (`@theme`); sin logica de negocio en el frontend.

### e2e (Playwright)

- `frontend/e2e/support/backend.ts`: mock de `POST/GET **/api/v1/requerimientos/*/documentos` y de
  `.../documentos/*/descarga` (binario `application/pdf`/DOCX simulado) antes del fallback 404.
- `frontend/e2e/wizard.spec.ts`: generar habilitado/deshabilitado por estado (CA-13); descarga dispara
  el blob y respeta el nombre `T#<folio>-v<version>.<ext>` (CA-16); fallo → mensaje y reintento con el
  wizard intacto (CA-14).

## Docker / configuracion

- `docker/backend.Dockerfile` ya instala `libreoffice-writer`, fuentes y copia `templates` a
  `/app/templates`. Añadir copia explicita de la plantilla derivada no es necesaria (copia el directorio)
  pero **verificar** que `templates/ers_plantilla_v1.docx` se incluya en la imagen.
- `docker-compose.yml`: el servicio `backend` solo monta `./backend/app`; añadir un volume de desarrollo
  `./templates:/app/templates:ro` para iterar la plantilla sin rebuild. Mantener `AI_PROVIDER=none`.
- `docker/backend-dev.Dockerfile` no tiene LibreOffice: las pruebas de conversion PDF se marcan
  `integration`; las de render DOCX (docxtpl) siguen en unitarias.
- `backend/pyproject.toml`: agregar `docxtpl` a dependencias (justificado por ADR-001).
- `.env.example`: `TEMPLATES_DIR`, `DOCUMENT_TEMPLATE_VERSION=v1`, `LIBREOFFICE_BINARY=soffice`,
  `DOCUMENT_GENERATION_TIMEOUT_SECONDS=60`, `DOCUMENT_MAX_BYTES`.

## Estrategia de pruebas

### Backend unitarias

- `tests/domain/test_document.py`: `build_file_name` → `T#<folio>-v<version>.<ext>` (CA-16).
- `tests/application/test_generate_documents.py` (fakes `InMemoryRequirementRepository` + renderer y
  converter falsos que devuelven bytes): registra DOS documentos (DOCX+PDF) con metadatos correctos y
  transiciona a `GENERADO` (CA-09, CA-11); estado no permitido o firmas faltantes → error sin registrar
  ni transicionar (CA-10); regenerar agrega filas sin sobrescribir (CA-12).
- `tests/application/test_document_queries.py`: `GetRequirementDocument`/`ListRequirementDocuments`
  (historico completo; 404 si no pertenece al requerimiento).
- `tests/infrastructure/test_document_mappers.py`: fila ↔ `GeneratedDocument`, BLOB ↔ bytes, mime/format.
- `tests/infrastructure/test_document_renderer.py`: con plantilla fixture `ers_plantilla_v1.docx`,
  verifica encabezado (`T#` + version documental), secciones, colecciones activas/orden, "No aplica",
  requisitos futuros, fechas `dd-mm-aaaa`, saltos de linea y escapado (CA-01, CA-03..CA-06, CA-07, CA-08);
  comparacion de estructura contra el `PreviewDocument` de la misma version (consistencia, CA-01).

### Backend API

- `tests/api/test_documents.py` (patron `dependency_overrides` de `test_preview.py`): `POST` 201 con dos
  documentos (CA-09); `POST` 409/422 en estado no permitido (CA-10); `GET` historico (CA-12); `GET`
  descarga 200 con `Content-Disposition` y nombre correcto (CA-16); `GET` 404 si no pertenece.

### Backend integracion (`-m integration`)

- `tests/integration/test_requirement_document_repository.py`: BLOB real en Oracle (Testcontainers),
  round-trip del contenido y del historico; migracion `0003` aplica en `migrated_engine`.
- `tests/integration/test_document_conversion.py`: DOCX real → PDF con LibreOffice; verifica que el PDF
  existe, no esta vacio y comparte las secciones/textos clave del DOCX (equivalencia, CA-02). Requiere
  imagen con LibreOffice (no `backend-dev`).

### Frontend

- `npm run build` (`tsc -b` + vite) sin errores; `npm run test:e2e` en verde con los tests del paso 13.

### Verificacion final (CA-15)

Desde `backend/`: `ruff check .`, `mypy --strict app`, `python -m pytest`; integracion con Docker; desde
`frontend/`: `npm run build` y `npm run test:e2e`. Evidencia en `verify.md`.

## Riesgos y decisiones (ADRs relacionados)

| Riesgo/decision | Gestion |
|---|---|
| Divergencia vista previa / DOCX / PDF | Fuente unica `PreviewDocument`; el renderizador no recalcula reglas (RF-01, RF-09) |
| BLOB en Oracle vs `StoragePort` de ADR-006 | Documentos generados por persistencia (BLOB); `StoragePort` queda para anexos; declarado en plan y `api.md` |
| LibreOffice fuera de `backend-dev` | Conversion PDF solo en pruebas `integration` con imagen que si lo tiene |
| Plantilla horneada en imagen, no montada | Volume `./templates:/app/templates:ro` en compose para desarrollo |
| Dependencia nueva `docxtpl`/`python-docx` | Fijada por ADR-001; unica dependencia nueva y justificada |
| Logotipos reales | Espacio reservado en encabezado; deuda tecnica registrada en `verify.md` |
| Descripcion del cambio inexistente | Celda vacia/"—"; deuda mantenida (RF-04) |
| Roles/auth de generar/descargar | Diferidos a SPEC-008; actor por defecto mientras tanto |
| Timeout/tamano de documento | `DOCUMENT_GENERATION_TIMEOUT_SECONDS` y `DOCUMENT_MAX_BYTES`; error claro y sin registro |
| ADRs relacionados | ADR-001 (docxtpl+LibreOffice), ADR-002 (hexagonal), ADR-004 (plantilla derivada), ADR-005/007 (firmas y estados) |
