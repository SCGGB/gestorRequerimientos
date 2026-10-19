# Verificacion - SPEC-006 (Vista previa A4 del requerimiento)

- Spec: `specs/SPEC-006-vista-previa-a4/spec.md` (estado: aprobado)
- Rama: `spec/SPEC-006-vista-previa-a4`
- Commits: `SPEC-006: dominio de composicion del PreviewDocument`, `SPEC-006: caso de uso BuildPreviewDocument`, `SPEC-006: endpoint vista-previa con esquemas Preview`, `SPEC-006: cliente, hook y componentes de la vista previa`, `SPEC-006: impresion de la vista previa (boton y estilos @media print)`, `SPEC-006: e2e del paso 13 con vista previa`, `SPEC-006: calidad (ruff, mypy, pytest, build, e2e)`.

## Criterios de aceptacion

| Criterio | Resultado | Evidencia |
|---|---|---|
| CA-01 | Cumple | `app/api/routers/requirements.py:113` (endpoint `GET .../vista-previa`) + `app/api/schemas/preview.py:97` (`PreviewDocumentResponse`). Test `tests/api/test_preview.py:33` (`test_preview_returns_document_contract`) valida 200, `ticket="T#5"`, `version_documento="1.0"`. |
| CA-02 | Cumple | `tests/api/test_preview.py:88` (`requirement_not_found`) y `:97` (`version_not_found`) validan 404 con envelope. Caso de uso `build_preview_document.py:16` lanza `VersionNotFoundError`. |
| CA-03 | Cumple | `preview.py:228` (`_collection_blocks`), `:235` (`_contents`: solo contenido no vacio, ordenado por `order`) y `version.active_*()` (solo activos). Test `test_preview.py:test_only_active_items_in_order_and_empty_content_omitted`. |
| CA-04 | Cumple | `preview.py:230-231` devuelve `no_aplica` con `NOT_APPLICABLE_TEXT="No aplica"` (`:12`) conservando titulo. Tests `test_empty_collection_keeps_title_and_returns_not_applicable`, `tests/api/test_preview.py:71-73`. |
| CA-05 | Cumple | `preview.py:240` (`_future_requirement_blocks`): `false` -> `"No Aplica."` (`:13`); `true` -> texto y/o lista. Tests `test_future_requirements_not_applying_returns_not_applicable`, `test_future_requirements_applying_returns_text_and_items`, `test_future_requirements_applying_with_items_only_returns_list`. |
| CA-06 | Cumple | `preview.py:77` (`format_date` -> `%d-%m-%Y`), usado en encabezado (`:92`) y control de versiones (`:102`). Tests `test_header_uses_...`, `test_version_control_lists_all_versions_ordered...`, `tests/api/test_preview.py:52,83`. |
| CA-07 | Cumple | `preview.py:86,94` ordena todas las versiones por `number` y `_version_row` deja `change_description=None`. Test `tests/application/test_build_preview_document.py:test_version_control_lists_all_versions_ordered` y `test_version_control_lists_all_versions_ordered_with_null_description`. |
| CA-08 | Cumple | `preview.py:117-130` (`_signer`/`_signatures`) devuelve `None` por rol cuando no hay firmas; `PreviewSignatures.tsx:3` muestra `"—"` (EMPTY_VALUE) y `:12` nombre+cargo cuando existen. Tests `test_signatures_are_null_per_role_when_missing`, `test_signatures_include_name_and_position_when_registered`. |
| CA-09 | Cumple | `Step13Review.tsx:78-91` integra `PreviewSheet` con datos de `usePreview`. `PreviewSheet.tsx` (hoja carta 816px, encabezado, secciones, tabla y firmas) + `PreviewSection.tsx` (parrafo/lista/no_aplica). E2E `wizard.spec.ts:254` ("la vista previa refleja el DTO del backend"). |
| CA-10 | Cumple | `PreviewNotice.tsx` (dirty -> aviso; transicion true->false -> "Actualizar vista previa"). `WizardPage.tsx:174` pasa `dirty={autosave.dirty}`; `PreviewNotice` invoca `preview.reload` (`usePreview.reload`). E2E `wizard.spec.ts:276` ("aviso de cambios sin guardar y actualizacion tras autosave"). |
| CA-11 | Cumple | Boton "Imprimir" en `Step13Review.tsx` -> `window.print()`; `index.css` bloque `@media print` con `@page { size: letter; margin: 2.5cm 2cm; }` que oculta shell/sidebar/stepper/footer/acciones (`data-print-hide`, `.preview-actions`) y muestra `.preview-sheet` a escala 1. E2E `wizard.spec.ts:300` verifica invocacion de `window.print` y presencia de estilos print. |
| CA-12 | Cumple | `PreviewError.tsx` (mensaje legible para 404/red/envelope + "Reintentar" -> `onRetry`). `Step13Review.tsx:81-83` lo monta sin despachar acciones de wizard. E2E `wizard.spec.ts:343` ("fallo de la vista previa muestra error y reintenta sin romper el wizard"). |
| CA-13 | Cumple | `ruff check .` OK; `mypy --strict app` OK (74 archivos); `pytest` 147 passed / 19 deselected; `npm run build` OK; `npm run test:e2e` 19 passed. App importa con `AI_PROVIDER=none`. |

## Evidencia de comandos

- Backend (imagen `gestor-req-dev`): `ruff check . && mypy --strict app && python -m pytest -q -p no:cacheprovider` -> `All checks passed!`, `Success: no issues found in 74 source files`, `147 passed, 19 deselected`.
- App sin IA: `AI_PROVIDER=none python -c "from app.main import app"` -> `app import ok`.
- Frontend: `npm run build` -> OK; `npm run test:e2e` -> `19 passed`.

## Alcance (T-21)

- Sin tablas nuevas ni migraciones Alembic (`infrastructure/` sin cambios).
- Sin dependencias nuevas en `backend/pyproject.toml` ni `frontend/package.json`.
- Sin cambios en `docxtpl`/LibreOffice (corresponde a SPEC-007).

## Hallazgos

- La spec (RF-14) habla de "hoja A4 simulada" pero usando tamano carta; la implementacion usa `size: letter` y ancho 816px @96dpi, coherente con RF-14 y T-16.
- `PreviewError` usa la forma real de `ApiError` (`status`/`code`/`details`), no `error.error.message`.

## Deuda tecnica registrada

- Ninguna deuda pendiente bloqueante. Fuera de alcance (SPEC-007): paginacion real y logotipos en la hoja; generacion DOCX/PDF reutilizando el mismo `PreviewDocument` sin reglas propias.
