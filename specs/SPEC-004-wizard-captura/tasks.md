# Tareas - SPEC-004

Tareas atomicas, ordenadas por dependencia. Cada una referencia el criterio de aceptacion (CA) que cubre.

## Fase A - Backend acotado

- [x] **T-01 — `titulo` en `RequirementSummary`** (CA-13)
  - Anadir `titulo: str` a `RequirementSummary` en `backend/app/api/schemas/requirement.py` y mapearlo en `from_domain` desde la version vigente (fallback seguro si no existe).
  - Actualizar `doc/technical/api.md` (esquema `RequirementSummary`).
  - Test de API que verifique que `GET /api/v1/requerimientos` devuelve `titulo`.
  - Verificacion: `ruff check .`, `mypy --strict app`, `pytest` (los tres desde `backend/`).

## Fase B - Frontend: base

- [x] **T-02 — Cliente HTTP y DTOs** (CA-11, CA-12)
  - `frontend/src/api/client.ts`: `request()` con base `/api/v1`, parseo del envelope de error → `ApiError { status, code, message, details }`.
  - `frontend/src/api/types.ts`: DTOs espejo (`RequirementSummary`, `RequirementPage`, `RequirementResponse`, `VersionResponse`, `CollectionItemResponse`, `BenefitResponse`, `SignatureResponse`, `AttachmentResponse`, `ChangeTypeResponse`, `PositionResponse`) y enums de UI.
  - Verificacion: `tsc -b`.

- [x] **T-03 — Funciones API de dominio** (CA-04, CA-02, CA-06, CA-13)
  - `api/requirements.ts` (listar, crear, obtener, patch version, versiones), `api/collections.ts` (add/update/delete/reorder por recurso), `api/catalogs.ts` (tipos-cambio, cargos).

- [x] **T-04 — Primitivas de UI** (CA-01)
  - `components/ui/`: `Button`, `Input`, `Textarea`, `Select`, `Badge`, `StatusBadge` (reubicar el existente) usando tokens de `index.css`.

- [x] **T-05 — Shell con barra lateral** (CA-01)
  - `components/layout/AppLayout.tsx` (header + sidebar + main), `Sidebar.tsx` (Requerimientos, Nuevo Requerimiento, Plantillas ERS/SRS, Repositorio Documental, Configuracion y Catalogos), `PlaceholderPage.tsx`.
  - Navegacion por `NavContext`; `App.tsx` alterna vista; default `Requerimientos`.

## Fase C - Frontend: listado

- [x] **T-06 — Listado de requerimientos** (CA-02, CA-03)
  - `features/requirements/RequirementsListPage.tsx` + `useRequirementsList.ts`: filtros `estado`/`folio`, paginacion `page`/`size`, columnas ticket (`T#`+folio), titulo y estado; accion "Nuevo" abre el wizard.

## Fase D - Frontend: wizard

- [x] **T-07 — Estado del wizard y definicion de pasos** (CA-04, CA-05)
  - `features/wizard/state/{types,reducer,WizardProvider,useWizard}.ts`: `WizardState`/acciones.
  - `wizardSteps.ts`: 13 pasos con obligatorios y `isComplete(state, step)`.

- [x] **T-08 — Shell del wizard** (CA-04, CA-05)
  - `WizardPage.tsx`, `components/WizardStepper.tsx` (estados `pendiente/activo/completado/error`), `components/WizardFooter.tsx` (anterior, guardar borrador, siguiente con bloqueo y motivo), `components/FieldError.tsx`, `NarrativeField.tsx`.

- [x] **T-09 — Autosave** (CA-04, CA-09)
  - `hooks/useAutosave.ts` (debounce) + serializacion de escrituras por requerimiento; refresco del `VersionResponse`.

- [x] **T-10 — Paso 1: datos generales** (CA-04, CA-03)
  - `Step01GeneralData.tsx`: folio (solo numero, `T#` fijo), titulo, tipo de cambio (catalogo), sistema, version documental, fecha; crea via `POST`, luego `PATCH`.

- [x] **T-11 — Pasos narrativos 2, 6 y 7** (CA-09)
  - `Step02CurrentNeed`, `Step06Context` (descripcion + manejo de errores, sin imagenes), `Step07UsersPermissions`; `PATCH` de version.

- [x] **T-12 — Editor de colecciones reutilizable** (CA-06, CA-07)
  - `components/CollectionEditor.tsx` + `CollectionItemRow.tsx`: agregar, editar, eliminar (baja logica) y reordenar; soporte de `tipo` para beneficios.

- [x] **T-13 — Pasos de coleccion 3, 4, 8, 10 y 11** (CA-06)
  - `Step03Objectives`, `Step04Considerations`, `Step08Restrictions`, `Step10Volumetry`, `Step11Risks` sobre `CollectionEditor`.

- [x] **T-14 — Paso 5: beneficios** (CA-07)
  - `Step05Benefits.tsx`: dos secciones (cualitativos/cuantitativos) sobre `beneficios` con `tipo`.

- [x] **T-15 — Paso 9: requisitos futuros** (CA-08)
  - `Step09FutureRequirements.tsx`: toggle "No aplica" (`requisitos_futuros_aplica=false`), texto y coleccion `requisitos-futuros`.

- [x] **T-16 — Paso 12: control documental** (CA-10)
  - `Step12DocumentControl.tsx`: Elaboro/Reviso/Autorizo (nombre + cargo desde catalogo), UI-only; sin registro de firmas.

- [x] **T-17 — Paso 13: shell de revision** (CA-01)
  - `Step13Review.tsx`: resumen de pasos y estados; sin vista previa ni generacion.

## Fase E - Infraestructura

- [x] **T-18 — Proxy de API** (CA-12)
  - `frontend/vite.config.ts`: proxy `/api` → `VITE_BACKEND_URL`.
  - `docker/frontend.nginx.conf`: `location /api/ { proxy_pass http://backend:8000; }`.

## Fase F - Pruebas y calidad

- [x] **T-19 — E2E Playwright** (CA-01..CA-11)
  - Cubrir shell/sidebar, listado con filtros/paginacion, "Nuevo" → paso 1, alta, bloqueo de "siguiente", colecciones, beneficios, requisitos futuros, paso 6 sin imagenes, paso 12 sin firmas, error `duplicate_folio`.
  - Actualizar `frontend/e2e/layout.spec.ts` al nuevo default conservando aserciones de tipografia/paleta.

- [x] **T-20 — Calidad** (CA-14)
  - `frontend`: `tsc -b` y `vite build` sin errores; `test:e2e` en verde.
  - `backend`: `ruff check .`, `mypy --strict app`, `pytest` en verde.

## Trazabilidad CA → Tareas

| CA | Tareas |
|---|---|
| CA-01 | T-04, T-05, T-17 |
| CA-02 | T-03, T-06 |
| CA-03 | T-06, T-10 |
| CA-04 | T-03, T-07, T-08, T-09, T-10 |
| CA-05 | T-07, T-08 |
| CA-06 | T-03, T-12, T-13 |
| CA-07 | T-12, T-14 |
| CA-08 | T-15 |
| CA-09 | T-09, T-11 |
| CA-10 | T-16 |
| CA-11 | T-02 |
| CA-12 | T-02, T-18 |
| CA-13 | T-01, T-03, T-06 |
| CA-14 | T-20 |
