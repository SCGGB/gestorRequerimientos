# Tareas - SPEC-007

> Tareas atomicas, ordenadas por dependencia. Cada una referencia el requisito funcional (RF) y el
> criterio de aceptacion (CA) que cubre. Backend (dominio + application + api + infraestructura) +
> frontend (paso 13 del wizard). No incluye anexos/imagenes (diferidos), ni roles/auth (SPEC-008), ni IA.
> Los binarios generados se persisten como BLOB en Oracle; no se usa `StoragePort` (ADR-006, reservado a
> anexos).
>
> **Modelo de datos Oracle / migraciones Alembic:** nueva tabla `REQ_DOCUMENTO` (DOCX y PDF como filas
> independientes con BLOB, trazabilidad y auditoria) y migracion `0003_documentos_generados`
> (`down_revision = "0002_modelo_requerimiento"`). DDL solo via Alembic.
>
> **Dependencia nueva:** `docxtpl` (y `python-docx`) en `backend/pyproject.toml`, fijada por ADR-001.
>
> Convencion de commits: un commit al cierre de cada fase con prefijo `SPEC-007:`.

## Fase 0 - Spike de plantilla (prerrequisito)

Commit de fase: `SPEC-007: spike de derivacion de la plantilla docxtpl`

- [x] **T-001 — Derivar y versionar `templates/ers_plantilla_v1.docx`** (RF-02, RF-17, ADR-004)
  - Partir de `templates/machote_requerimiento.docx` (inmutable) y aplicar el procedimiento de
    `doc/documents/mapeo-machote.md` (secciones 1..10, beneficios 4/4.1/4.2, control de versiones,
    firmas, encabezado con ticket y version, pie con `PAGE`, estilos, aplanar sdt, limpiar defectos,
    cada etiqueta en un solo run).
  - Insertar etiquetas docxtpl para el contexto de `PreviewDocument` y reservar el espacio de los
    logotipos en el encabezado (deuda tecnica, decision 5).
  - Smoke test manual: render con datos de ejemplo y verificacion de secciones, "No aplica" y saltos de
    linea. Documentar la version de plantilla (`v1`) y la brecha de logotipos.
  - Resultado: derivacion reproducible con `tools/derive_ers_template.py` (aplana sdt, elimina ejemplos y
    viñetas/párrafos vacíos, etiqueta las 12 secciones con `{%p %}` y las tablas con `{%tr %}`); plantilla
    `templates/ers_plantilla_v1.docx` (v1). Contexto por sección fija (decision del usuario). Encabezados
    `header1`/`header2` etiquetados para `{{ ticket }}` y `{{ document_version }}`. Smoke test DOCX OK
    (colecciones, "No aplica", saltos de linea). LibreOffice no esta en el host: la conversion PDF se
    valida en T-025 (Docker). Brecha de logotipos registrada (espacio reservado en el encabezado).

## Fase A - Modelo de datos y migracion

Commit de fase: `SPEC-007: tabla REQ_DOCUMENTO y migracion 0003`

- [x] **T-002 — Tabla `REQ_DOCUMENTO` en `tables.py`** (RF-10)
  - `backend/app/infrastructure/db/tables.py`: `Table("REQ_DOCUMENTO", ...)` con `ID`, `REQUERIMIENTO_ID`
    (FK), `VERSION_ID` (FK), `FORMATO` (CHECK `DOCX`/`PDF`), `PLANTILLA_VERSION`, `NOMBRE_ARCHIVO`,
    `MIME_TYPE`, `TAMANO_BYTES`, `CONTENIDO` (`BLOB`), `GENERADO_AT`, `GENERADO_BY` y auditoria
    (`_audit_columns()`); indices `REQ_DOCUMENTO_REQUERIMIENTO_IX` y `REQ_DOCUMENTO_VERSION_IX`, y
    unique `REQ_DOCUMENTO_UQ` (req, version, formato, generado_at).

- [x] **T-003 — Migracion Alembic `0003_documentos_generados`** (RF-10)
  - `backend/alembic/versions/0003_documentos_generados.py`, `down_revision = "0002_modelo_requerimiento"`;
    `upgrade` crea la tabla con BLOB, checks, FKs, indices y auditoria; `downgrade` la elimina. Patron de
    `0002_modelo_requerimiento.py`.

## Fase B - Dominio puro (sin FastAPI/SQLAlchemy/docxtpl)

Commit de fase: `SPEC-007: entidad GeneratedDocument y nombre de archivo`

- [x] **T-004 — `GeneratedDocument` y tipos de formato** (RF-10, RF-13)
  - Nuevo `backend/app/domain/requirement/document.py`: `DocumentFormat = Literal["DOCX","PDF"]`,
    `MIME_TYPES`, dataclass frozen `GeneratedDocument` (`id`, `requirement_id`, `version_id`, `format`,
    `template_version`, `file_name`, `mime_type`, `size_bytes`, `generated_at`, `generated_by`,
    `content: bytes | None`), sin imports de infraestructura ni IA.

- [x] **T-005 — `build_file_name` y prueba de dominio** (RF-19, CA-16)
  - Helper puro `build_file_name(folio, document_version, file_format) -> "T#<folio>-v<version>.<ext>"`.
  - Nuevo `backend/tests/domain/test_document.py`: DOCX y PDF, folio/version variados.

## Fase C - Puertos y adaptadores

Commit de fase: `SPEC-007: renderer docxtpl, conversor LibreOffice y repositorio BLOB`

- [x] **T-006 — Puerto `DocumentRendererPort` y adaptador docxtpl** (RF-01, RF-02, RF-17)
  - `backend/app/application/ports/document_renderer.py`: ABC `render_docx(document: PreviewDocument,
    template_version: str) -> bytes`.
  - `backend/app/infrastructure/adapters/document_renderer.py`: `DocxtplDocumentRenderer` carga
    `templates/<archivo>` desde `Settings.templates_dir`, `Environment(autoescape=True)`, mapea el
    `PreviewDocument` al contexto de la plantilla y usa `RichText`/`Listing` para saltos de linea
    (RF-08). `docxtpl` en `backend/pyproject.toml` (ADR-001).

- [x] **T-007 — Puerto `DocumentConverterPort` y adaptador LibreOffice** (RF-09)
  - `backend/app/application/ports/document_converter.py`: ABC `to_pdf(docx: bytes) -> bytes`.
  - `backend/app/infrastructure/adapters/document_converter.py`: `LibreofficeDocumentConverter` con
    `TemporaryDirectory` y `soffice --headless --convert-to pdf` (`Settings.libreoffice_binary`,
    `Settings.document_generation_timeout_seconds`), validacion de salida y errores claros (RF-15).

- [x] **T-008 — Puerto `RequirementDocumentRepository` y adaptador Oracle BLOB** (RF-10, RF-13)
  - `backend/app/application/ports/requirement_document_repository.py`: ABC `add`, `get` (con `content`),
    `list_by_requirement` (sin `content`).
  - `backend/app/infrastructure/adapters/requirement_document_repository.py`:
    `SqlAlchemyRequirementDocumentRepository` (SQLAlchemy Core + `oracledb`), insercion/lectura de BLOB;
    mappers de fila ↔ `GeneratedDocument` en `db/mappers.py`.

- [x] **T-009 — Configuracion de generacion** (RF-16)
  - `backend/app/infrastructure/config.py`: `templates_dir`, `document_template_version`,
    `libreoffice_binary`, `document_generation_timeout_seconds`, `document_max_bytes`; actualizar
    `.env.example`.

- [x] **T-010 — Pruebas de adaptadores y mappers** (RF-08, RF-10)
  - `backend/tests/infrastructure/test_document_renderer.py`: con plantilla fixture, encabezado,
    secciones, colecciones activas/orden, "No aplica", requisitos futuros, fechas `dd-mm-aaaa`, saltos de
    linea y escapado; comparacion de estructura con el `PreviewDocument` (CA-01, CA-03..CA-08).
  - `backend/tests/infrastructure/test_document_mappers.py`: fila ↔ DTO, BLOB ↔ bytes, mime/formato.

## Fase D - Casos de uso (application)

Commit de fase: `SPEC-007: casos de uso de generacion y consulta de documentos`

- [x] **T-011 — `GenerateRequirementDocuments`** (RF-01, RF-10, RF-11, RF-12, RF-13, CA-09, CA-10, CA-11)
  - Nuevo `backend/app/application/use_cases/requirement/generate_documents.py`: carga el agregado y la
    version (`RequirementNotFoundError`/`VersionNotFoundError`), valida precondiciones reutilizando
    `validate_requirement(..., target_state=GENERADO)`, compone `build_preview_document`, renderiza DOCX,
    convierte PDF, persiste DOS filas y transiciona a `GENERADO` via `change_status` + `save`. Sincrono;
    ante fallo no registra ni transiciona. Export en `use_cases/requirement/__init__.py`.

- [x] **T-012 — `GetRequirementDocument` y `ListRequirementDocuments`** (RF-13, CA-12)
  - `backend/app/application/use_cases/requirement/get_document.py` y `list_documents.py`: recuperar un
    documento validando pertenencia al requerimiento (con `content` para descarga) y listar el historico
    completo por `GENERADO_AT` desc sin `content`. Export en `__init__.py`.

- [x] **T-013 — Pruebas de casos de uso** (CA-09, CA-10, CA-11, CA-12)
  - `backend/tests/application/test_generate_documents.py` (fakes renderer/converter + repositorio): dos
    documentos con metadatos, transicion automatica (CA-09, CA-11); estado/firmas no permiten → error sin
    registros ni transicion (CA-10); regenerar agrega sin sobrescribir (CA-12).
  - `backend/tests/application/test_document_queries.py`: descarga y 404 si no pertenece; historico.

## Fase E - API y contrato

Commit de fase: `SPEC-007: endpoints de generacion, historico y descarga`

- [x] **T-014 — Esquemas `GeneratedDocumentResponse`** (RF-10)
  - Nuevo `backend/app/api/schemas/document.py` con `GeneratedDocumentResponse` y `from_domain(...)` (sin
    binario); re-export en `schemas/__init__.py`.

- [x] **T-015 — Router `documents.py` y dependencias** (RF-11, RF-13, RF-14, RF-15, RF-19, CA-16)
  - Nuevo `backend/app/api/routers/documents.py`: `POST /requerimientos/{id}/documentos` (201),
    `GET /requerimientos/{id}/documentos` (200) y
    `GET /requerimientos/{id}/documentos/{documento_id}/descarga` (`Content-Disposition: attachment;
    filename="T#<folio>-v<version>.<ext>"`). Registrar en `main.py`.
  - `backend/app/api/dependencies.py`: factorias de renderer, converter, repositorio y casos de uso.

- [x] **T-016 — Mapeo de errores de generacion** (RF-11, RF-15, CA-10)
  - `backend/app/api/errors.py`: mapear estado/firmas no permitidas a 409/422 y fallo de render/conversion
    a `document_generation_failed` (500) con mensaje en espanol, dentro del envelope existente.

- [x] **T-017 — Pruebas de API** (CA-09, CA-10, CA-12, CA-16)
  - `backend/tests/api/test_documents.py` (patron `dependency_overrides`): `POST` 201 con dos documentos;
    `POST` 409/422 no permitido; `GET` historico; `GET` descarga 200 con `Content-Disposition` y nombre
    correcto; `GET` 404 si no pertenece.

## Fase F - Documentacion del contrato

Commit de fase: `SPEC-007: documentar endpoints de documentos en api.md`

- [x] **T-018 — Actualizar `doc/technical/api.md`** (RF-10, RF-13, RF-19)
  - Nueva seccion `### Documentos generados (SPEC-007)` con las tres rutas y errores; resumen de
    `GeneratedDocumentResponse` en "Esquemas principales"; nota de BLOB en Oracle, de que el contenido es
    el `PreviewDocument` de SPEC-006 y de que el nombre sigue `T#<folio>-v<version>.<ext>`.

## Fase G - Frontend: cliente, hook y paso 13

Commit de fase: `SPEC-007: generacion y descarga en el paso 13`

- [ ] **T-019 — Tipos y cliente `api/documents.ts`** (RF-13, RF-19)
  - `frontend/src/api/types.ts`: `GeneratedDocument`.
  - `frontend/src/api/documents.ts`: `generateDocuments`, `listDocuments`, `downloadDocument` (blob +
    `Content-Disposition`); `frontend/src/api/client.ts`: `requestBlob` reutilizando `ApiError`; export en
    `api/index.ts`.

- [ ] **T-020 — Hook `useRequirementDocuments`** (RF-13, RF-14, RF-15, CA-14)
  - `frontend/src/hooks/useRequirementDocuments.ts`: `{ data, loading, error, generate, download, reload }`
    (patron de `usePreview.ts`), con descarga via `URL.createObjectURL` + `<a download>` y manejo de
    errores sin romper el wizard.

- [ ] **T-021 — Componentes y estado deshabilitado** (RF-14, CA-13)
  - `DocumentActions.tsx`: boton "Generar DOCX/PDF" y "Descargar" por documento, deshabilitados con el
    motivo visible cuando el estado no permite generar; mensajes de exito/error.
  - `DocumentHistory.tsx`: historico (formato, fecha, tamano, descarga).

- [ ] **T-022 — Integracion en `Step13Review.tsx`** (RF-12, RF-13, RF-14, CA-13)
  - Montar `DocumentActions`/`DocumentHistory` bajo la vista previa; derivar el motivo de deshabilitado del
    `RequirementStatus`; despachar la recarga de la version/estado tras una generacion exitosa.

- [ ] **T-023 — e2e (Playwright)** (CA-13, CA-14, CA-16)
  - `frontend/e2e/support/backend.ts`: mocks de `POST/GET .../documentos` y de `.../descarga` antes del
    fallback 404.
  - `frontend/e2e/wizard.spec.ts`: generar habilitado/deshabilitado por estado (CA-13); descarga con nombre
    `T#<folio>-v<version>.<ext>` (CA-16); fallo → mensaje y reintento con el wizard intacto (CA-14).

## Fase H - Calidad e integracion

Commit de fase: `SPEC-007: calidad e integracion (BLOB y conversion PDF)`

- [ ] **T-024 — Lint, tipos y unitarias backend** (RF-16, CA-15)
  - Desde `backend/`: `ruff check .`, `mypy --strict app`, `python -m pytest` en verde; app sin IA
    (`AI_PROVIDER=none`).

- [ ] **T-025 — Integracion: BLOB Oracle y conversion DOCX→PDF** (RF-09, RF-10, CA-02, CA-15)
  - `tests/integration/test_requirement_document_repository.py`: round-trip de BLOB y migracion `0003` con
    Testcontainers.
  - `tests/integration/test_document_conversion.py`: DOCX real → PDF con LibreOffice; PDF no vacio y
    secciones/textos clave equivalentes (CA-02). Marcadas `integration`.

- [ ] **T-026 — Build frontend, e2e y verificacion de alcance** (RF-16, CA-15)
  - Desde `frontend/`: `npm run build` y `npm run test:e2e` en verde.
  - Confirmar dependencia unica nueva (`docxtpl`/`python-docx`), sin cambios en `StoragePort`, y deuda de
    logotipos registrada.

## Trazabilidad CA → Tareas

| CA | Tareas |
|---|---|
| CA-01 | T-006, T-010, T-017 |
| CA-02 | T-007, T-025 |
| CA-03 | T-006, T-010 |
| CA-04 | T-006, T-010 |
| CA-05 | T-006, T-010 |
| CA-06 | T-006, T-010 |
| CA-07 | T-006, T-010 |
| CA-08 | T-006, T-010 |
| CA-09 | T-011, T-013, T-017 |
| CA-10 | T-011, T-013, T-016, T-017 |
| CA-11 | T-011, T-013 |
| CA-12 | T-012, T-013, T-017 |
| CA-13 | T-021, T-022, T-023 |
| CA-14 | T-020, T-023 |
| CA-15 | T-024, T-025, T-026 |
| CA-16 | T-005, T-015, T-017, T-019, T-023 |
