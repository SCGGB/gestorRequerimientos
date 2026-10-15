# Plan tecnico - SPEC-004

## Enfoque
SPEC-004 es una spec de **frontend**. Construye el shell de la aplicación, el listado de requerimientos y el wizard de captura (pasos 1-12 funcionales y 13 shell) como una SPA React 19 + Vite + TypeScript + Tailwind 4, consumiendo la API `/api/v1` de SPEC-003. No hay lógica de negocio en el frontend: solo captura, validación de forma por paso y presentación. El backend solo recibe un cambio acotado: exponer `titulo` en `RequirementSummary`.

Principios rectores:
- Hexagonal en backend: el frontend es un adaptador de entrada más; solo habla HTTP con `/api/v1`.
- Regla 6 de `AGENTS.md`: **sin dependencias nuevas**. Navegación por estado interno, estado con `Context`/`useReducer`, datos con `fetch`.
- La fuente de verdad es Oracle; el wizard recarga el agregado tras cada operación para evitar divergencias.

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic
- **No se introduce ninguna tabla ni columna nueva ni migración.** El título ya existe en `REQ_VERSION.TITULO`; SPEC-004 solo lo expone en el resumen.
- El cambio backend (`RequirementSummary.titulo`) no requiere Alembic.

## Dominio y casos de uso
- **Sin cambios en `domain`** ni en `application`. La UI no contiene reglas de negocio; consume los casos de uso ya expuestos por SPEC-003.
- Cambio acotado en la capa `api` (backend), capa de presentación:
  - `app/api/schemas/requirement.py`: añadir `titulo: str` a `RequirementSummary` y mapearlo en `from_domain` desde la versión vigente (`Requirement.current_version()` / `version_by_id(current_version_id)`), con valor por defecto seguro si no hubiera versión vigente.
- No se toca `RequirementPage` (ya agrega los summaries) ni el router (el listado ya serializa summaries).

## Puertos y adaptadores afectados
- Backend: ninguno nuevo. El router `GET /api/v1/requerimientos` no cambia su firma; solo el DTO de salida.
- Frontend: nuevo **adaptador HTTP** (puerto implícito) `src/api/*`, aislado del resto de la UI para permitir cambiar el transporte sin tocar componentes.

## API (endpoints, contratos, errores)
Contratos consumidos (ya existentes en SPEC-003, documentados en `doc/technical/api.md`):
- `POST /api/v1/requerimientos` → `RequirementResponse`.
- `GET /api/v1/requerimientos?estado=&folio=&page=&size=` → `RequirementPage`.
- `GET /api/v1/requerimientos/{id}` → `RequirementResponse`.
- `GET /api/v1/requerimientos/{id}/versiones[/{vid}]` → `VersionResponse`/`list`.
- `PATCH /api/v1/requerimientos/{id}/versiones/{vid}` → `VersionResponse`.
- `POST|PATCH|DELETE .../versiones/{vid}/{coleccion}[/{itemId}]`, `PUT .../orden`.
- `POST .../estado` (opcional en UI; no requerido por CA de esta spec).
- `GET /api/v1/catalogos/tipos-cambio`, `GET /api/v1/catalogos/cargos?rol=`.

Contrato de error: envelope `{"error": {"code", "message", "details"}}`. El cliente HTTP lo transforma en un tipo `ApiError { status, code, message, details }` que la UI muestra.

Cambio de contrato (esta spec):
- `RequirementSummary` incluye `titulo: string`. Actualizar `doc/technical/api.md` (sección de esquemas).

## Frontend (pantallas, componentes, estado)

### Estructura de archivos propuesta
```
frontend/src/
  api/
    client.ts          # request(), ApiError, base "/api/v1", parseo del envelope
    types.ts           # DTOs espejo de los esquemas de la API + enums de UI
    requirements.ts    # listRequirements, createRequirement, getRequirement, updateVersion, ...
    collections.ts     # add/update/delete/reorder por recurso
    catalogs.ts        # listChangeTypes, listPositions
    index.ts
  features/
    requirements/
      RequirementsListPage.tsx
      useRequirementsList.ts
    wizard/
      WizardPage.tsx
      wizardSteps.ts        # definicion de los 13 pasos + validaciones de obligatorios
      state/
        types.ts            # WizardState, WizardAction
        reducer.ts
        WizardProvider.tsx  # Context + useReducer
        useWizard.ts
      steps/
        Step01GeneralData.tsx ... Step13Review.tsx
      components/
        WizardStepper.tsx
        WizardFooter.tsx
        NarrativeField.tsx
        CollectionEditor.tsx
        CollectionItemRow.tsx
        FieldError.tsx
  components/
    layout/
      AppLayout.tsx      # shell (header + sidebar + main), reusa tokens
      Sidebar.tsx
      PlaceholderPage.tsx
    ui/
      Button.tsx
      Input.tsx
      Textarea.tsx
      Select.tsx
      Badge.tsx
      StatusBadge.tsx    # reubicado desde components/StatusBadge.tsx
  hooks/
    useAutosave.ts
    useCatalogs.ts
  pages/
    OverviewPage.tsx     # se conserva; se accesible desde el shell
  App.tsx                # alterna vista: list | wizard | placeholder | overview
```

### Navegación (sin router)
- `App` mantiene `view: { name: "list" } | { name: "wizard"; requirementId?: number } | { name: "placeholder"; title: string } | { name: "overview" }`.
- `Sidebar` y acciones disparan cambios de vista mediante callbacks/Context ligero de navegacion (`NavContext`).
- Default: `Requerimientos` (lista). La `OverviewPage` (estado del sistema) queda accesible como entrada secundaria o dentro del shell (decision de UI menor); su prueba e2e se ajusta.

### Estado del wizard
- `WizardProvider` con `useReducer`. `WizardState`:
  - `view`: `"list" | "wizard"`.
  - `requirementId: number | null`, `folio`, `ticket`, `estado`, `versionId: number | null`.
  - `header`: campos de cabecera de la version.
  - `narrative`: campos narrativos.
  - `collections`: map por recurso (`objetivos`, `consideraciones`, `beneficios`, `restricciones`, `volumetria`, `riesgos`, `requisitos-futuros`).
  - `stepIndex`, `stepStatus` (por paso), `dirty`, `saving`, `error`.
- Acciones: `LOAD_REQUIREMENT`, `SET_STEP`, `SET_HEADER_FIELD`, `SET_NARRATIVE_FIELD`, `SET_COLLECTION`, `MARK_DIRTY`, `SET_SAVING`, `SET_ERROR`.
- `wizardSteps.ts` define id, titulo, obligatorios y funcion `isComplete(state, step)` usada por el stepper y el bloqueo de "siguiente".

### Pasos (mapeo a API)
| Paso | Componente | Persistencia |
|---|---|---|
| 1 | `Step01GeneralData` | `POST /requerimientos`; luego `PATCH` cabecera |
| 2 | `Step02CurrentNeed` | `PATCH` `necesidad_actual` |
| 3 | `Step03Objectives` | coleccion `objetivos` |
| 4 | `Step04Considerations` | coleccion `consideraciones` |
| 5 | `Step05Benefits` | coleccion `beneficios` (secciones cuali/cuanti con `tipo`) |
| 6 | `Step06Context` | `PATCH` `contexto_descripcion`, `contexto_manejo_errores` |
| 7 | `Step07UsersPermissions` | `PATCH` `usuarios_permisos` |
| 8 | `Step08Restrictions` | coleccion `restricciones` |
| 9 | `Step09FutureRequirements` | `PATCH` `requisitos_futuros_aplica`/`_texto` + coleccion `requisitos-futuros` |
| 10 | `Step10Volumetry` | coleccion `volumetria` |
| 11 | `Step11Risks` | coleccion `riesgos` |
| 12 | `Step12DocumentControl` | UI-only (cargos desde catalogo); no firma |
| 13 | `Step13Review` | shell (resumen); sin preview/generacion |

### Autosave
- `useAutosave` recibe el `dirty` de cabecera/narrativa y un `save()` debounced (p.ej. 600-800 ms).
- Colecciones persisten al ejecutar la operacion (add/edit/delete/reorder), no por autosave.
- Serializacion por requerimiento: una cola simple evita escrituras concurrentes sobre la misma version; tras cada escritura se refresca el `VersionResponse` devuelto.

### Presentacion y errores
- `StatusBadge` y `Badge` siguen los tokens de `frontend/src/index.css` / `doc/ui/design/STITCH_DESIGN.md`.
- `ApiError` de negocio (`409`, `404`, `422`) se muestra junto al control afectado y en un aviso no bloqueante; el formulario no pierde datos.
- Textos de UI en espanol; identificadores en ingles.

## Docker / configuracion
- `frontend/vite.config.ts`: anadir `"/api": { target: backendUrl, changeOrigin: true }` al `server.proxy` para desarrollo.
- `docker/frontend.nginx.conf`: anadir `location /api/ { proxy_pass http://backend:8000; }` (produccion); ajustar segun el nombre de servicio del backend.
- `docker-compose.yml`: el servicio `frontend` ya usa Vite dev con `VITE_BACKEND_URL`; no requiere cambios mas alla del proxy.
- Sin secretos en imagenes; configuracion por `.env`.

## Estrategia de pruebas
- **E2E Playwright** (unico runner; sin dependencias nuevas), con mocking de la API por `page.route` (patron de `frontend/e2e/layout.spec.ts`):
  - CA-01 shell + sidebar + placeholders.
  - CA-02 listado con filtros y paginacion.
  - CA-03 "Nuevo" abre wizard en paso 1 con `T#`.
  - CA-04 alta del requerimiento (mock `POST` 201) y avance.
  - CA-05 bloqueo de "siguiente" por obligatorios.
  - CA-06 coleccion add/edit/delete/reorder (mock de respuestas de colecciones).
  - CA-07 beneficios cuali/cuanti.
  - CA-08 requisitos futuros "No aplica".
  - CA-09 paso 6 sin carga de imagenes.
  - CA-10 paso 12 no emite `POST` de firmas (asercion de que no se llamo).
  - CA-11 error `duplicate_folio` mostrado sin perder datos.
- Actualizar `frontend/e2e/layout.spec.ts` para el nuevo default (lista) conservando las aserciones de tipografia/paleta.
- **Backend**: prueba de `RequirementSummary` con `titulo` (unit/API) en `backend/tests/api/test_requirements.py`; `ruff` + `mypy --strict` + `pytest`.
- **Frontend**: `tsc -b` (tipos) y `vite build` (build de produccion) sin errores.

## Riesgos y decisiones (ADRs relacionados)
- **ADR-002 (hexagonal/Docker):** el frontend es un adaptador de entrada; no accede a la persistencia.
- **ADR-007 (firmas segun estado):** justifica que el paso 12 no persista firmas en `BORRADOR`.
- **ADR-006 (almacenamiento objetos dev):** justifica diferir anexos/imagenes del paso 6.
- **DT-03 (SPEC-002, edicion concurrente del borrador):** el autosave serializado mitiga, pero no elimina, el riesgo de concurrencia; se documenta.
- **Brecha "Descripcion del cambio":** sin campo en el modelo; registrada como deuda para una spec de backend.
- **Contratos de UI vs backend:** DTOs espejo + e2e con mocking reducen el riesgo de desalineacion; el contrato de referencia es `doc/technical/api.md` y `/openapi.json`.
