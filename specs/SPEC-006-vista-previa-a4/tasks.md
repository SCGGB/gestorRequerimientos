# Tareas - SPEC-006

> Tareas atomicas, ordenadas por dependencia. Cada una referencia el requisito funcional (RF) y el
> criterio de aceptacion (CA) que cubre. Backend (dominio + application + api) + frontend (paso 13 del
> wizard). No genera DOCX/PDF (SPEC-007), no crea anexos/imagenes, no captura "Descripcion del cambio"
> ni firmas, ni toca auth/roles (SPEC-008), ni IA.
>
> **Modelo de datos Oracle / migraciones Alembic: no aplica.** La vista previa se compone desde el
> agregado ya persistido (`REQ_VERSION`, colecciones, `REQ_FIRMA`); no se crea tabla/columna/indice ni
> revision Alembic (ver plan, seccion "Modelo de datos Oracle"). Sin dependencias nuevas.
>
> Convencion de commits: un commit al cierre de cada fase con prefijo `SPEC-006:`.

## Fase A - Dominio puro (sin FastAPI/SQLAlchemy/Pydantic)

Commit de fase: `SPEC-006: dominio de composicion del PreviewDocument`

- [x] **T-01 — Dataclasses del DTO de renderizado** (RF-03, RF-04)
  - Nuevo `backend/app/domain/requirement/preview.py` (Python puro): `PreviewDocument`,
    `PreviewSection`, `PreviewBlock` (`tipo: Literal["parrafo", "lista", "no_aplica"]`, `texto`,
    `items`), `PreviewVersionRow`, `PreviewFirmas`, `PreviewSigner`, todas frozen dataclass con
    slots, tipado completo.
  - Helper `_format_date(d: date) -> str` → `dd-mm-aaaa` (RF-08).
  - Sin imports de FastAPI, SQLAlchemy, Pydantic ni librerias de IA/DOCX; codigos en ingles.

- [x] **T-02 — Composicion de encabezado y secciones del machote** (RF-03, RF-05, RF-06, RF-07, CA-03, CA-04, CA-05)
  - `build_preview_document(requirement: Requirement, version: RequirementVersion) -> PreviewDocument`
    con el orden fijo de secciones del plan (1..10 incluida la contenedora `4 Beneficios Esperados`
    sin bloques y subsecciones `4.1`/`4.2`); encabezado `folio`, `requirement.ticket`, `titulo`,
    `version_documento`, `fecha_version`.
  - Colecciones via `version.active_*()`: solo activos en orden `order`, items sin contenido
    omitidos (CA-03, RF-05); coleccion vacia → titulo conservado + bloque `no_aplica` `"No aplica"`
    (CA-04, decision P-04).
  - Requisitos futuros: `aplica=false` → `no_aplica` `"No Aplica."` sin texto ni elementos;
    `aplica=true` → `parrafo` con `future_requirements_text` (si existe) y/o `lista` con activos
    (CA-05, RF-07).
  - Secciones narrativas (`necesidad_actual`, `diagramas_contextuales` con `context_description` +
    `context_error_handling` opcional, `usuarios_permisos`) → siempre bloque `parrafo`.
  - Sin secciones ajenas al machote (sin RF/no RF ni IEEE 830).

- [x] **T-03 — Control de versiones y firmas** (RF-09, RF-10, CA-06, CA-07, CA-08 backend)
  - Control de versiones: fila por cada `requirement.versions` ordenado por `number`, con
    `version`, `fecha` (`dd-mm-aaaa`), `descripcion_cambio: None`, `reviso`/`elaboro` = nombre de la
    firma del rol (`signatures_by_role`) o `None` (CA-06, CA-07).
  - Firmas de la version consultada: `elaboro`/`reviso`/`autorizo` → `PreviewSigner(nombre, cargo)`
    o `None` por rol (ADR-007); la composicion solo lee, nunca crea ni modifica firmas (CA-08).

- [x] **T-04 — Pruebas unitarias del dominio** (CA-03, CA-04, CA-05, CA-06, CA-07, CA-08)
  - Nuevo `backend/tests/domain/test_preview.py` con `tests/factories.py::complete_version`:
    activos/orden y omision de items vacios (CA-03); coleccion vacia → `no_aplica` "No aplica" con
    titulo (CA-04); requisitos futuros false/true con texto, lista y ambos (CA-05); fechas
    `dd-mm-aaaa` (CA-06); control de versiones completo con `descripcion_cambio=None` (CA-07);
    firmas null/presentes por rol (CA-08); numeracion y orden de secciones; encabezado con
    `ticket = T#<folio>`. Sin base de datos.

## Fase B - Casos de uso (application)

Commit de fase: `SPEC-006: caso de uso BuildPreviewDocument`

- [x] **T-05 — `BuildPreviewDocument`** (RF-01, RF-02, CA-01, CA-02 backend)
  - Nuevo `backend/app/application/use_cases/requirement/build_preview_document.py`:
    `repository.get(requirement_id)` (`RequirementNotFoundError`), `version_by_id(version_id)` o
    `VersionNotFoundError`, invoca `build_preview_document(...)` y devuelve el DTO. **Nunca `save`**:
    operacion de solo lectura (RF-02).
  - Export en `use_cases/requirement/__init__.py` (`__all__`); depende solo del puerto
    `RequirementRepository` existente (mismo molde que `GetVersion` en `list_versions.py`).

- [x] **T-06 — Pruebas del caso de uso** (CA-01, CA-02, CA-07 backend)
  - Nuevo `backend/tests/application/test_build_preview_document.py` con
    `InMemoryRequirementRepository`: devuelve la version pedida con encabezado correcto;
    `requirement_not_found` / `version_not_found` (CA-02); sin llamadas a `save` (RF-02);
    control de versiones con todas las versiones del agregado (CA-07).

## Fase C - API y contrato

Commit de fase: `SPEC-006: endpoint vista-previa con esquemas Preview`

- [x] **T-07 — Esquemas Pydantic** (RF-03, RF-04)
  - Nuevo `backend/app/api/schemas/preview.py`: `PreviewDocumentResponse`, `PreviewSectionResponse`,
    `PreviewBlockResponse` (`tipo`, `texto`, `items`), `PreviewVersionRowResponse`,
    `PreviewFirmasResponse`, `PreviewSignerResponse`, con `from_domain(...)` por clase (patron
    `VersionResponse.from_domain`); traduccion dominio (ingles) ↔ API (espanol), campos identicos al
    contrato de la spec.
  - Re-export en `backend/app/api/schemas/__init__.py` (`__all__`).

- [x] **T-08 — Endpoint `GET /requerimientos/{id}/versiones/{vid}/vista-previa`** (RF-01, RF-02, CA-01, CA-02)
  - Ruta en `backend/app/api/routers/requirements.py` (prefijo `/api/v1` existente), declarada
    despues de `GET /versiones/{version_id}`; `response_model=PreviewDocumentResponse`; sin logica de
    negocio: invoca el caso de uso y serializa.
  - `backend/app/api/dependencies.py`: fabrica `get_build_preview_document_use_case` con puertos por
    `Depends` (patron existente).
  - 404 sin cambios: envelope `requirement_not_found` / `version_not_found` (CA-02).

- [x] **T-09 — Pruebas de API** (CA-01, CA-02)
  - Nuevo `backend/tests/api/test_preview.py` (patron `_client_with_repository` de
    `tests/api/test_requirements.py`): `200` con contrato completo, `ticket = T#<folio>` y
    `version_documento` (CA-01); `404` con envelope para requerimiento/version inexistente (CA-02);
    la operacion no altera estado ni versiones.

## Fase D - Documentacion

Commit de fase: `SPEC-006: documentar endpoint vista-previa en api.md`

- [ ] **T-10 — Actualizar `doc/technical/api.md`** (RF-01, RF-03, RF-04)
  - Fila del nuevo `GET /requerimientos/{id}/versiones/{vid}/vista-previa` en "Catalogo de
    endpoints" (seccion Requerimientos) y resumen de `PreviewDocumentResponse` (+ bloques, control
    de versiones y firmas) en "Esquemas principales".
  - Nota de que el contrato es compartido con la futura generacion DOCX/PDF (SPEC-007) y de que no
    hay cambios de modelo ni migracion.

## Fase E - Frontend: cliente, hook y componentes

Commit de fase: `SPEC-006: cliente, hook y componentes de la vista previa`

- [ ] **T-11 — Tipos espejo y cliente `api/preview.ts`** (RF-01, RF-03, RF-04)
  - `frontend/src/api/types.ts`: `PreviewDocument`, `PreviewSection`, `PreviewBlock` (union
    discriminada por `tipo`), `PreviewVersionRow`, `PreviewFirmas`, `PreviewSigner` (snake_case
    identico al JSON).
  - `frontend/src/api/preview.ts`: `getPreview(requirementId, versionId): Promise<PreviewDocument>`
    con `request<>` de `client.ts` (ApiError con envelope ya manejado); export en `api/index.ts`.

- [ ] **T-12 — Hook `usePreview`** (RF-11, RF-16, CA-12)
  - Nuevo `frontend/src/hooks/usePreview.ts` con patron `{ data, loading, error, reload }` de
    `useRequirementsList.ts`: `AbortSignal` + flag de cancelacion, se activa cuando `requirementId` /
    `versionId` no son nulos, `reload()` re-pide la ultima version persistida.

- [ ] **T-13 — Componentes de la hoja y el contenido** (RF-03, RF-04, RF-09, RF-10, RF-14, CA-09)
  - Nueva carpeta `frontend/src/features/wizard/components/preview/`:
    - `PreviewSheet.tsx`: hoja de tamano carta (816 px @96dpi) con padding 2.5 cm sup/inf y 2 cm
      izq/der, encabezado institucional en texto (titulo institucional, ticket `T#`,
      `version_documento`), escala via `ResizeObserver` (`transform: scale`,
      `transform-origin: top center`) y fallback de desplazamiento horizontal (RF-14).
    - `PreviewSection.tsx`: titulo con `numero` + bloques (`parrafo` → `<p>`, `lista` → `<ul>`,
      `no_aplica` → texto literal); la seccion contenedora `4` pinta solo el encabezado.
    - `PreviewVersionTable.tsx`: tabla de control de versiones con `null` → "—" (CA-09).
    - `PreviewSignatures.tsx`: bloque de firmas con `null` → "—" (CA-08 UI).
  - Tokens de `src/index.css` (`@theme`); sin duplicar valores de `STITCH_DESIGN.md`; sin logica de
    negocio en el frontend.

- [ ] **T-14 — Aviso, error y reintento** (RF-13, RF-16, CA-10, CA-12)
  - `PreviewNotice.tsx`: estado "cambios sin guardar" (`dirty=true`) y estado "Actualizar vista
    previa" cuando `dirty` pasa de `true` a `false` (autosave completado) hasta pulsar `reload()`.
  - `PreviewError.tsx`: mensaje legible para 404 / error de red / envelope de error + boton
    "Reintentar" (`reload()`), sin romper el wizard.

- [ ] **T-15 — Integracion en el paso 13** (RF-11, RF-12, RF-13, CA-09, CA-10)
  - `frontend/src/features/wizard/steps/Step13Review.tsx`: conserva el resumen de pasos y el ticket;
    agrega la vista previa (carga inicial al activarse con `state.requirementId`/`state.versionId`).
  - `frontend/src/features/wizard/WizardPage.tsx` (case 12) pasa `dirty={autosave.dirty}` como prop.
  - Solo lectura: sin dispatch del reducer desde la vista previa (RF-12).

- [ ] **T-16 — Impresion** (RF-15, CA-11)
  - Boton "Imprimir" en la barra de acciones de la vista previa → `window.print()`.
  - Bloque `@media print` en `frontend/src/index.css`: `@page { size: letter; margin: 2.5cm 2cm; }`,
    oculta shell/sidebar/stepper/footer/acciones y muestra unicamente `.preview-sheet` a escala 1.

## Fase F - Pruebas e2e (Playwright)

Commit de fase: `SPEC-006: e2e del paso 13 con vista previa`

- [ ] **T-17 — Mock del endpoint en el backend falso** (RF-01, CA-09)
  - `frontend/e2e/support/backend.ts`: helper `previewDocument()` base y ruta
    `GET **/api/v1/requerimientos/*/versiones/*/vista-previa` registrada **antes** del fallback 404
    (linea 284), con soporte de error configurable (`createError`).

- [ ] **T-18 — Tests e2e del paso 13** (CA-09, CA-10, CA-11, CA-12)
  - `frontend/e2e/wizard.spec.ts` (usando `advanceTo(page, 12)`):
    - vista previa con encabezado, secciones y tablas coherentes con el DTO mockeado (CA-09).
    - cambios sin guardar → aviso; tras guardar → "Actualizar vista previa" recarga los datos (CA-10).
    - "Imprimir": `window.print` stubbeado con `addInitScript` y asertado; presencia de estilos
      `@media print` (CA-11).
    - fallo del endpoint (500/red) → mensaje + "Reintentar" con el wizard intacto (CA-12).

## Fase G - Calidad

Commit de fase: `SPEC-006: calidad (ruff, mypy, pytest, build, e2e)`

- [ ] **T-19 — Lint, tipos y pruebas backend** (RF-17, CA-13)
  - Desde `backend/`: `ruff check .`, `mypy --strict app`, `python -m pytest` en verde; la app
    arranca sin IA (`AI_PROVIDER=none`).

- [ ] **T-20 — Build frontend y e2e** (RF-14, RF-15, RF-17, CA-13)
  - Desde `frontend/`: `npm run build` (`tsc -b` + vite) sin errores de tipos; `npm run test:e2e` en
    verde con los tests nuevos del paso 13.

- [ ] **T-21 — Verificacion de alcance** (RF-17)
  - Confirmar que no hay tablas nuevas ni migraciones Alembic (`infrastructure/` sin cambios), ni
    dependencias nuevas en `backend/pyproject.toml` ni `frontend/package.json`, ni cambios en
    `docxtpl`/LibreOffice (SPEC-007).

## Trazabilidad CA → Tareas

| CA | Tareas |
|---|---|
| CA-01 | T-05, T-08, T-09 |
| CA-02 | T-05, T-06, T-08, T-09 |
| CA-03 | T-02, T-04 |
| CA-04 | T-02, T-04 |
| CA-05 | T-02, T-04 |
| CA-06 | T-03, T-04 |
| CA-07 | T-03, T-04, T-06 |
| CA-08 | T-03, T-04, T-13 |
| CA-09 | T-13, T-15, T-17, T-18 |
| CA-10 | T-14, T-15, T-18 |
| CA-11 | T-16, T-18, T-20 |
| CA-12 | T-12, T-14, T-18 |
| CA-13 | T-19, T-20 |
