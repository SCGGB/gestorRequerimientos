# Plan tecnico - SPEC-006-vista-previa-a4

## Enfoque

El backend compone un DTO neutral `PreviewDocument` a partir de la version persistida (agregado cargado desde el repositorio, sin guardar nada) y el frontend solo lo pinta en el paso 13 como una hoja simulada de tamano carta con boton "Imprimir". SPEC-007 reutilizara el mismo contrato para DOCX/PDF.

Decisiones de diseno:

- **Contrato**: la spec define el contrato en la red como `PreviewDocument`. En el backend las clases de dominio llevan ese nombre (`app/domain/requirement/preview.py`) y los esquemas Pydantic siguen la convencion `*Response` del codebase (`PreviewDocumentResponse` con `from_domain`), con campos identicos a la spec. En el frontend los tipos espejo se llaman `PreviewDocument` (snake_case, identico al JSON).
- **Composicion en dominio puro**: `build_preview_document(requirement, version)` en `app/domain/requirement/preview.py` (dataclasses y funciones puras, sin imports de FastAPI/SQLAlchemy/Pydantic) aplica todas las reglas de normalizacion; el caso de uso solo orquesta y el router solo serializa.
- **Seccion 4 "Beneficios Esperados"** se emite como seccion contenedora (`numero: "4"`, `bloques: []`) que la UI pinta como encabezado, seguida de `4.1` y `4.2`, conforme al machote.
- **Secciones narrativas vacias** (necesidad actual, contexto, usuarios/permisos) devuelven siempre bloque `parrafo` con el texto capturado (puede ser vacio); el bloque `no_aplica` solo se emite donde la spec lo exige (coleccion vacia, RF-06, y requisitos futuros, RF-07).
- **Lectura**: `BuildPreviewDocument` usa `repository.get(requirement_id)` (mismo molde que `GetVersion`), resuelve `version_by_id` y nunca invoca `save`; el agregado ya trae todas las versiones y sus firmas para el control de versiones.
- **Frescura de datos**: el paso 13 siempre pide la ultima version persistida; los cambios sin guardar solo generan aviso + accion "Actualizar vista previa" (recarga del hook).

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic

Sin cambios. La spec prohíbe tablas nuevas y migraciones; todo dato proviene de `REQ_REQUERIMIENTO`, `REQ_VERSION`, las colecciones (`REQ_OBJETIVO`, `REQ_CONSIDERACION`, `REQ_BENEFICIO`, `REQ_RESTRICCION`, `REQ_VOLUMETRIA`, `REQ_RIESGO`, `REQ_REQUISITO_FUTURO`) y `REQ_FIRMA`, ya cargadas por `SqlAlchemyRequirementRepository._load` (`backend/app/infrastructure/adapters/requirement_repository.py:357`).

## Dominio y casos de uso

### Dominio (puro)

Nuevo modulo `backend/app/domain/requirement/preview.py`:

- Dataclasses congeladas: `PreviewDocument`, `PreviewSection`, `PreviewBlock` (con `tipo: Literal["parrafo","lista","no_aplica"]`), `PreviewVersionRow`, `PreviewFirmas`, `PreviewSigner`.
- `build_preview_document(requirement: Requirement, version: RequirementVersion) -> PreviewDocument`.
- Helpers puros:
  - `_format_date(d: date) -> str` → `dd-mm-aaaa`.
  - `_section(codigo, numero, titulo, bloques)`.
  - Bloques `lista` desde `version.active_objectives()` etc. (solo activos, orden por `orden`, items sin contenido se omiten).
  - Seccion de coleccion vacia → bloque `no_aplica` con texto `"No aplica"` (P-04).
  - Requisitos futuros: `future_requirements_applies=False` → `no_aplica` con `"No Aplica."`; `True` → bloque `parrafo` con `future_requirements_text` (si existe) y/o bloque `lista` con `active_future_requirements()`.
  - Control de versiones: una fila por cada `requirement.versions` ordenado por `number`, con `document_version`, `version_date` formateada, `descripcion_cambio: None`, `reviso`/`elaboro` = nombre (o `None`) tomados de `version.signatures_by_role(REVISO/ELABORO)`.
  - Firmas de la version consultada: `signatures_by_role(ELABORO/REVISO/AUTORIZO)` → `PreviewSigner(nombre, cargo)` o `None` por rol (ADR-007; no crea ni modifica firmas).
  - Encabezado: `folio`, `requirement.ticket` (`T#` + folio), `version.title`, `version.document_version`, `version.version_date` formateada.

Orden fijo de secciones (numeracion del machote, B-03):

| numero | codigo | titulo | origen |
|---|---|---|---|
| 1 | `necesidad_actual` | Necesidad Actual | `current_need` (parrafo) |
| 2 | `objetivos` | Objetivos Generales | `active_objectives` (lista / no_aplica) |
| 3 | `consideraciones` | Consideraciones | `active_considerations` |
| 4 | `beneficios` | Beneficios Esperados | contenedor, sin bloques |
| 4.1 | `beneficios_cualitativos` | Beneficios Cualitativos | `benefits` kind=CUALITATIVO |
| 4.2 | `beneficios_cuantitativos` | Beneficios Cuantitativos | `benefits` kind=CUANTITATIVO |
| 5 | `diagramas_contextuales` | Diagramas Contextuales | `context_description` (parrafo); `context_error_handling` como segundo parrafo si no esta vacio; sin anexos (fuera de alcance) |
| 6 | `usuarios_permisos` | Usuarios y Permisos | `users_permissions` (parrafo) |
| 7 | `restricciones` | Restricciones | `active_restrictions` |
| 8 | `requisitos_futuros` | Requisitos Futuros | ver RF-07 |
| 9 | `volumetria` | Volumetria y Rendimiento | `active_volumetry` |
| 10 | `riesgos` | Riesgos Iniciales | `active_risks` |

Secciones fuera de numeracion (sin `numero`, `numero: ""`): `control_versiones` y `firmas` se modelan fuera de `secciones` (campos dedicados del DTO, como en la spec).

### Aplicacion

Nuevo caso de uso `backend/app/application/use_cases/requirement/build_preview_document.py`:

```python
class BuildPreviewDocument:
    def __init__(self, repository: RequirementRepository) -> None: ...
    def execute(self, requirement_id: int, version_id: int) -> PreviewDocument:
        # repository.get(requirement_id) -> RequirementNotFoundError
        # requirement.version_by_id(version_id) or raise VersionNotFoundError
        # build_preview_document(requirement, version)  # nunca save
```

Export en `app/application/use_cases/requirement/__init__.py` (`__all__`).

## Puertos y adaptadores afectados

- **Puerto `RequirementRepository`**: sin cambios (el agregado completo ya incluye versiones, colecciones y firmas).
- **Adaptador Oracle `SqlAlchemyRequirementRepository`**: sin cambios.
- **Nuevo**: dependencia `get_build_preview_document_use_case` en `app/api/dependencies.py` (molde de `get_get_requirement_version_use_case`, linea 95).

## API (endpoints, contratos, errores)

### Endpoint

`GET /api/v1/requerimientos/{requirement_id}/versiones/{version_id}/vista-previa` en `app/api/routers/requirements.py` (prefijo `/api/v1` ya existente), declarado despues de `GET /versiones/{version_id}` (linea 96); `response_model=PreviewDocumentResponse`; inyeccion via `Annotated[BuildPreviewDocument, Depends(get_build_preview_document_use_case)]`.

- 200: `PreviewDocumentResponse` (campos identicos al contrato de la spec).
- 404: envelope unico existente - `requirement_not_found` / `version_not_found` (`app/api/errors.py:54-57`, sin cambios).
- Operacion de solo lectura: no body, no persistencia.

### Esquemas

Nuevo `backend/app/api/schemas/preview.py` (re-export en `schemas/__init__.py`):

- `PreviewDocumentResponse` (folio, ticket, titulo, version_documento, fecha_version, secciones, control_versiones, firmas) + `from_domain`.
- `PreviewSectionResponse`, `PreviewBlockResponse` (`tipo`, `texto?`, `items?`), `PreviewVersionRowResponse`, `PreviewFirmasResponse`, `PreviewSignerResponse`.

### Documentacion

Actualizar `doc/technical/api.md`: fila en "Catalogo de endpoints" (seccion Requerimientos) y resumen del esquema en "Esquemas principales".

## Frontend (pantallas, componentes, estado)

### Cliente y tipos

- `src/api/types.ts`: `PreviewDocument`, `PreviewSection`, `PreviewBlock` (union por `tipo`), `PreviewVersionRow`, `PreviewFirmas`, `PreviewSigner` (snake_case espejo).
- `src/api/preview.ts`: `getPreview(requirementId, versionId): Promise<PreviewDocument>` con `request<PreviewDocument>` de `client.ts`; export en `src/api/index.ts`.

### Hook

`src/hooks/usePreview.ts`, patron `{ data, loading, error, reload }` de `useRequirementsList.ts` con `AbortSignal` y guardia de cancelacion; se activa cuando `requirementId`/`versionId` no son nulos; `reload()` vuelve a pedir la ultima version persistida.

### Componentes (nueva carpeta `src/features/wizard/components/preview/`)

- `PreviewSheet.tsx`: hoja simulada - ancho fijo de carta (816 px @96dpi), margenes 2.5 cm sup/inf y 2 cm izq/der (`padding` en cm), encabezado institucional en texto (titulo institucional, ticket `T#`, version del documento), escala con `ResizeObserver` (`transform: scale` + `transform-origin: top center`) para caber en el area de trabajo; en pantallas pequenas, desplazamiento horizontal.
- `PreviewSection.tsx`: renderiza `codigo`/`numero`/`titulo` + bloques (`parrafo` → `<p>`, `lista` → `<ul>`, `no_aplica` → texto literal).
- `PreviewVersionTable.tsx`: tabla de control de versiones (version, fecha, descripcion del cambio, reviso, elaboro; `null` → "—").
- `PreviewSignatures.tsx`: bloque de firmas (elaboro/reviso/autorizo; `null` → "—").
- `PreviewNotice.tsx`: aviso "cambios sin guardar" y boton "Actualizar vista previa".
- `PreviewError.tsx`: mensaje de error (404/red/envelope) + boton "Reintentar".

Tokens de `index.css` (`@theme`); sin duplicar valores de `STITCH_DESIGN.md`. No hay componente `Table` generico: la tabla se maqueta inline (patron de `RequirementsListPage.tsx`).

### Integracion en el paso 13

- `Step13Review.tsx`: conserva el resumen de pasos y el ticket (RF-11); agrega la vista previa montada al activarse.
- `WizardPage.tsx` (renderStep case 12) pasa props nuevos a `Step13Review`: `dirty` (`autosave.dirty`) e ids (`state.requirementId`, `state.versionId` desde `useWizard()`); el hook decide la carga inicial.
- Flujo de frescura (RF-13/CA-10):
  - `dirty === true` → `PreviewNotice` en estado "cambios sin guardar" (la vista previa muestra la ultima version persistida).
  - Transicion `dirty: true → false` (autosave completado, `REFRESH_VERSION`) → el aviso cambia a boton "Actualizar vista previa" (estado pendiente hasta que se pulse `reload()`).
  - `reload()` tras el guardado refleja los datos persistidos.
- Solo lectura: la vista previa no despacha acciones del reducer.

### Impresion (RF-15)

- Boton "Imprimir" en la barra de acciones de la vista previa → `window.print()`.
- Bloque `@media print` en `src/index.css`:
  - `@page { size: letter; margin: 2.5cm 2cm; }`.
  - Oculta `AppLayout`/sidebar/stepper/footer/botones y el resto del paso 13; muestra unicamente `.preview-sheet` a escala 1.

## Docker / configuracion

Sin cambios. No hay configuracion nueva, ni secretos, ni dependencias (backend `pyproject.toml` y frontend `package.json` intactos). `AI_PROVIDER=none` opera igual.

## Estrategia de pruebas

### Backend unitarias

- `tests/domain/test_preview.py` (con `tests/factories.py::complete_version`):
  - solo elementos activos y en orden (CA-03); items sin contenido no generan viñeta (RF-05).
  - coleccion vacia → `no_aplica` "No aplica" conservando titulo (CA-04).
  - `requisitos_futuros_aplica` false/true (CA-05).
  - fechas `dd-mm-aaaa` (CA-06).
  - firmas null por rol y firmas presentes (CA-08, parte backend).
  - numeracion y orden de secciones del machote (RF-03, reglas de negocio).
- `tests/application/test_build_preview_document.py` (con `InMemoryRequirementRepository`):
  - devuelve el DTO de la version pedida; `requirement_not_found`/`version_not_found` (CA-02).
  - solo lectura: el repositorio no recibe `save` (RF-02).
  - control de versiones con todas las versiones y `descripcion_cambio = None` (CA-07).

### Backend API

- `tests/api/test_preview.py` (patron `_client_with_repository` de `test_requirements.py`):
  - 200 con contrato completo, `ticket` `T#` + folio y `version_documento` (CA-01).
  - 404 con envelope (`requirement_not_found` / `version_not_found`) (CA-02).

### Frontend e2e (Playwright)

- `e2e/support/backend.ts`: mock de `GET **/api/v1/requerimientos/*/versiones/*/vista-previa` con un `previewDocument()` base, registrado **antes** del fallback 404 (linea 284); soporte para `createError` del punto anterior.
- `e2e/wizard.spec.ts` (nuevos tests, usando `advanceTo(page, 12)`):
  - la vista previa muestra encabezado, secciones y tablas coherentes con el DTO (CA-09).
  - cambios sin guardar → aviso y, tras guardar, "Actualizar vista previa" recarga (CA-10).
  - "Imprimir": se stubbea `window.print` con `page.addInitScript` y se aserta la invocacion; ademas se verifica la presencia de los estilos `@media print` (CA-11).
  - fallo del endpoint (500/red) → mensaje + "Reintentar" con el wizard intacto (CA-12).

### Verificacion final (CA-13)

Desde `backend/`: `ruff check .`, `mypy --strict app`, `python -m pytest` (o via imagen `gestor-req-dev`). Desde `frontend/`: `npm run build` (incluye `tsc -b`) y `npm run test:e2e`.

## Riesgos y decisiones (ADRs relacionados)

| Riesgo/decision | Gestion |
|---|---|
| Divergencia vista previa / DOCX / PDF | Un unico `PreviewDocument` de dominio; SPEC-007 debe reutilizar `build_preview_document` sin reglas propias |
| Reglas de normalizacion duplicadas en el cliente | El backend emite bloques tipados; el frontend no aplica logica de negocio |
| Fidelidad limitada sin paginacion | Se declara simulacion A4/carta; paginacion y logotipos en SPEC-007 (ADR-006) |
| Firmas y "Descripcion del cambio" inexistentes | `null` en DTO, "—" en UI; no se crea ni modifica nada (ADR-007) |
| Acceso a `autosave.dirty` desde el paso 13 | `WizardPage` pasa `dirty` como prop al montar `Step13Review` (sin ampliar el reducer) |
| Escala de la hoja en distintos breakpoints | `ResizeObserver` + `transform: scale`; fallback scroll horizontal |
| ADRs relacionados | ADR-002 (hexagonal), ADR-006 (anexos fuera de alcance), ADR-007 (firmas segun estado) |
