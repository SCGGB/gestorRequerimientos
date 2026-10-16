# verify.md — SPEC-004 Wizard de captura

- Spec: `specs/SPEC-004-wizard-captura/spec.md` (Estado: Aprobada)
- Plan: `specs/SPEC-004-wizard-captura/plan.md`
- Tareas: `specs/SPEC-004-wizard-captura/tasks.md` (T-01..T-20 marcadas `[x]`)
- Rama: `spec/SPEC-004-wizard-captura`
- Fecha de verificación: 2026-10-16
- Revisor: `reviewer`

## Estado global

| Resultado | Detalle |
|---|---|
| Criterios cumplidos | CA-01, CA-02, CA-03, CA-04, CA-05, CA-06, CA-07, CA-08, CA-09, CA-10, CA-11, CA-12, CA-13, CA-14 |
| Criterios parciales | Ninguno |
| Criterios no cumplidos | Ninguno |
| Arquitectura hexagonal | Sin violaciones |
| Calidad (lint/tipos/build/e2e) | Todo en verde |

## Comandos ejecutados (evidencia)

| Comando | Resultado |
|---|---|
| `npm run build` (frontend = `tsc -b && vite build`) | OK — 75 módulos, `dist/assets/index-C2blHVI_.js` |
| `npx playwright test` (frontend) | **15 passed** (6.7 s) |
| `ruff check .` (backend, imagen `gestor-req-dev`) | `All checks passed!` |
| `mypy --strict app` (backend) | `Success: no issues found in 66 source files` |
| `python -m pytest` (backend) | **79 passed** (72+7) |
| Grep del bundle `dist/assets/*.js` | Solo `/api/v1`; **sin** `localhost:8000` / `backend:8000` / `127.0.0.1` |

---

## Verificación por criterio de aceptación

### CA-01 — Shell, sidebar y placeholders — **Cumple**

- Código: `frontend/src/App.tsx` (vista por defecto `list`, sin router), `frontend/src/components/layout/AppLayout.tsx` (header/sidebar/main/footer), `frontend/src/components/layout/Sidebar.tsx` (5 entradas: `Requerimientos`, `Nuevo Requerimiento`, `Plantillas ERS/SRS`, `Repositorio Documental`, `Configuracion y Catalogos`), `frontend/src/components/layout/PlaceholderPage.tsx`.
- Pruebas: `frontend/e2e/layout.spec.ts:6` (layout + tipografía + paleta), `frontend/e2e/layout.spec.ts:65` (navegación y placeholders de Plantillas/Repositorio).
- Observación menor: no hay aserción explícita para el placeholder `Configuracion y Catalogos` (mismo componente/camino).

### CA-02 — Listado con filtros y paginación — **Cumple**

- Código: `frontend/src/features/requirements/RequirementsListPage.tsx`, `.../useRequirementsList.ts`, `frontend/src/api/requirements.ts` (`buildQuery` con `estado`/`folio`/`page`/`size`).
- Columnas: ticket (`item.ticket`), título (`item.titulo`) y estado (`StatusBadge`) en `RequirementsListPage.tsx:106-151`.
- Pruebas: `frontend/e2e/wizard.spec.ts:12` (estado, folio, paginación, `Mostrando 1-10 de 11`, `Pagina 1 de 2`); `frontend/e2e/layout.spec.ts:42` (título visible).

### CA-03 — "Nuevo" abre wizard paso 1 con `T#` fijo y folio vacío — **Cumple**

- Código: `RequirementsListPage.tsx:53-57` (`Nuevo` → `navigate({name:"wizard"})`); `Step01GeneralData.tsx:84-97` (span `T#` de solo lectura + input de folio vacío por defecto `emptyHeader().folio = ""`).
- Pruebas: `frontend/e2e/support/wizard.ts:13` (`openWizard`) + `frontend/e2e/wizard.spec.ts:36` verifican la apertura en `Paso 1: Datos generales`, la visibilidad del prefijo `T#` y el folio inicial vacío (`toHaveValue("")`).

### CA-04 — Alta vía `POST` y avance conservando `id`/versión — **Cumple**

- Código: `Step01GeneralData.tsx:46-69` (`createRequirement` → `LOAD_REQUIREMENT` + `SET_STEP 1`); `reducer.ts:140-159` (`stateFromRequirement` fija `requirementId`, `versionId`).
- Prueba: `frontend/e2e/wizard.spec.ts:48` verifica el body del `POST` y el avance a paso 2; al volver, `Ticket: T#123` y folio deshabilitado (confirma `id`/versión conservados).

### CA-05 — Bloqueo de "siguiente" con motivo visible — **Cumple**

- Código: `frontend/src/features/wizard/wizardSteps.ts` (`isComplete`, `completionIssue`, `computeStepStatuses`), `WizardFooter.tsx:45-53` (motivo con `aria-live`), `WizardPage.tsx:117-124` (`canGoForward`/`blockingReason`).
- Prueba: `frontend/e2e/wizard.spec.ts:36` (bloqueo paso 1 por falta de creación) + `frontend/e2e/wizard.spec.ts:48` (bloqueo paso 2 por obligatorios: `Complete los obligatorios del paso 2: necesidad actual.` y habilitación al completar).

### CA-06 — Colecciones: agregar/editar/eliminar/reordenar y baja lógica — **Cumple**

- Código: `frontend/src/features/wizard/components/CollectionEditor.tsx` (add/edit/delete/reorder), `CollectionItemRow.tsx`, `frontend/src/api/collections.ts`; filtrado de activos `activo !== false` en `CollectionEditor.tsx:44-52` y `wizardSteps.ts:144-146`.
- Baja lógica (backend): `backend/app/domain/requirement/collections.py:118-120` (`active=False`).
- Prueba: `frontend/e2e/wizard.spec.ts:83` (paso 3: agregar, reordenar, editar, eliminar y verificar que el eliminado deja de listarse).
- Observación: el backend simulado del e2e elimina físicamente (`e2e/support/backend.ts:274-282`); la baja lógica se evidencia en el dominio backend, no end-to-end.

### CA-07 — Beneficios cuali/cuanti con `tipo` — **Cumple**

- Código: `Step05Benefits.tsx` (dos secciones sobre `beneficios`), `CollectionEditor` con `kind`.
- Prueba: `frontend/e2e/wizard.spec.ts:122` verifica secciones independientes, aislamiento y `tipo` en los `POST` (`["CUALITATIVO","CUANTITATIVO"]`).

### CA-08 — Paso 9 "No aplica" → `requisitos_futuros_aplica=false` — **Cumple**

- Código: `Step09FutureRequirements.tsx:13-19` (`handleToggle` → `SET_NARRATIVE_FIELD` + `MARK_DIRTY`); autosave en `WizardPage.tsx:106-111` + `useAutosave.ts`.
- Prueba: `frontend/e2e/wizard.spec.ts:193` verifica que al marcar "No aplica", el texto/colección se ocultan y se captura un `PATCH` con `requisitos_futuros_aplica: false`.

### CA-09 — Paso 6: descripción contextual/errores persistidos; sin imágenes/anexos — **Cumple**

- Código: `Step06Context.tsx`, `NarrativeField.tsx`; sin `input[type=file]` ni endpoints de anexos.
- Prueba: `frontend/e2e/wizard.spec.ts:166` verifica el mensaje "sin carga de imagenes", ausencia de `input[type=file]` y que el autosave captura `contexto_descripcion` y `contexto_manejo_errores`.

### CA-10 — Paso 12 UI-only, sin registro de firmas — **Cumple**

- Código: `Step12DocumentControl.tsx` (solo `SET_SIGNER_FIELD` local; no invoca endpoints de firmas), contrato ADR-007.
- Prueba: `frontend/e2e/wizard.spec.ts:178` verifica secciones Elaboró/Revisó/Autorizó, selects de cargo, ausencia de botón "firmar" y el mensaje informativo.
- Observación: no se asevera explícitamente la ausencia de un `POST /firmas` (no existe tal llamada en el código).

### CA-11 — Envelope de error mostrado sin perder datos — **Cumple**

- Código: `frontend/src/api/client.ts:37-52` (`toApiError` con envelope `{error:{code,message,details}}`), `ApiError`; `state/errors.ts toWizardError`; `Step01GeneralData.tsx:63-65` (`SET_ERROR` sin limpiar `header`).
- Prueba: `frontend/e2e/wizard.spec.ts:80` (folio duplicado `409` → `role="alert"` con mensaje, permanencia en el paso 1 y conservación de `Folio` y `Titulo`).

### CA-12 — Bundle de producción usa `/api/v1` relativo — **Cumple**

- Código: `frontend/src/api/client.ts:7` (`API_BASE = "/api/v1"`); `frontend/vite.config.ts:11-15` (proxy `/api`, `/health`, `/version`); `docker/frontend.nginx.conf` (`location /api/ → http://backend:8000`).
- Evidencia: grep sobre `frontend/dist/assets/*.js` → único base `/api/v1`; sin URLs internas del backend embebidas.
- Prueba: `frontend/e2e/layout.spec.ts:95` ("cliente usa rutas relativas /api/v1 (humo de proxy)") verifica que todas las peticiones `/api/v1/*` se realizan al origen actual.

### CA-13 — `RequirementSummary` incluye `titulo` y la tabla lo muestra — **Cumple**

- Backend: `backend/app/api/schemas/requirement.py` (`RequirementSummary.titulo`, `from_domain` toma `current.title` con fallback `""`); `doc/technical/api.md:113` actualizado.
- Frontend: `RequirementsListPage.tsx:141` (columna Título).
- Pruebas: `backend/tests/api/test_requirements.py:69` (`test_list_requirements_includes_titulo`); `frontend/e2e/layout.spec.ts:42`.

### CA-14 — Calidad frontend/backend — **Cumple**

- `npm run build` (`tsc -b` + `vite build`): OK.
- `npx playwright test`: 15 passed.
- Backend `ruff check .`: OK; `mypy --strict app`: OK; `pytest`: 79 passed.

---

## Arquitectura hexagonal

- **Sin violaciones.** El cambio de backend se limita a la capa `api` (`app/api/schemas/requirement.py`, y un ajuste de tipado en `app/api/routers/catalogs.py`); no se toca `domain` ni `application`.
- El frontend actúa como adaptador de entrada: toda la comunicación HTTP se aísla en `frontend/src/api/*` (`client.ts`, `types.ts`, `requirements.ts`, `collections.ts`, `catalogs.ts`), sin acceso directo a persistencia.
- Estado del cliente en `Context`/`useReducer` (`state/WizardProvider.tsx`, `reducer.ts`) y `navigation/NavContext.tsx`; navegación por estado interno sin router.
- Sin dependencias nuevas: `frontend/package.json` no aparece modificado en `git status` (React, Vite, TS, Tailwind, Playwright son las ya declaradas) — RF-16 cumplido.

## Falta de pruebas (hallazgos)

1. **Regla "edición deshabilitada si no `BORRADOR` (409)"** (`Step01/06/09/12`, `CollectionEditor`) no tiene prueba e2e (pendiente menor, fuera de los 14 criterios).
2. **Mock e2e de colecciones** elimina físicamente; no reproduce la baja lógica (`activo=false`) del backend (observación de implementación, sin impacto en cumplimiento).
3. **CA-10**: no se asevera ausencia de `POST` de firmas (aunque no existe la llamada en el código; observación menor).

## Deuda técnica

- **"Descripción del cambio"** del control de versiones: sin campo en el modelo; no se captura (deuda ya registrada para una spec de backend).
- **Paso 12 (firmantes)**: captura de UI que no se persiste en `BORRADOR` (ADR-007); riesgo de confusión mitigado con mensaje informativo.
- **Paso 13**: el texto "La vista previa y la generacion de documentos se realizan al finalizar la captura" puede inducir a error, ya que ambas están fuera de alcance (SPEC-007).
- **Concurrencia de autosave**: mitigada con cola de escrituras por `requerimiento:version` (`useAutosave.ts:15-27`), pero el límite DT-03 de SPEC-002 permanece documentado y no eliminado.
- **Anexos/imágenes** del paso 6 diferidos a la spec de storage (ADR-006).
- Acción `RESET` definida en el reducer sin uso aparente en la UI (menor).

## Conclusión

La SPEC-004 está **implementada, verificada y cerrable**. Los 14 criterios de aceptación están en **Cumple**; CA-03 quedó evidenciado con aserciones explícitas de `T#` visible y folio vacío en `wizard.spec.ts:36`. La calidad de frontend (tipos, build, e2e — 15 passed) y backend (ruff, mypy, 79 tests passed) está en verde. No se detectaron violaciones de arquitectura hexagonal ni dependencias no justificadas. Quedan como hallazgo menor la prueba de "edición deshabilitada si no `BORRADOR`" (fuera de los 14 criterios, ver Falta de pruebas).
