# Verificacion - SPEC-007

- Estado: Cumple
- Fecha: 2026-10-19
- Commit verificado: 454f3cd ("SPEC-007: calidad e integracion (BLOB y conversion PDF)"), mas la correccion
  de CA-05 (T-027) verificada en la misma fecha.
- Rama: spec/SPEC-007-generacion-docx-pdf
- Alcance revisado: dominio/aplicacion/API/infraestructura backend, migracion 0003, plantilla docxtpl, frontend del paso 13 y pruebas (unitarias, integracion, build y e2e).

## Comandos ejecutados

1. Backend lint/tipos/unitarias (imagen `gestor-req-dev`):
   `ruff check . && mypy --strict app && python -m pytest -q -p no:cacheprovider`
   - `ruff`: `All checks passed!`
   - `mypy`: `Success: no issues found in 86 source files`
    - `pytest`: **183 unitarias en verde** (progreso 72 + 72 + 39).
2. Integracion (imagen `gestor-req-integration`, Testcontainers + Oracle + LibreOffice):
   `python -m pytest -m integration tests/integration -p no:cacheprovider -q`
   - **26 pruebas en verde** (incluye `test_document_conversion.py` y `test_requirement_document_repository.py`).
3. Frontend (`frontend/`): `npm run build` y `npm run test:e2e`
   - `npm run build`: `tsc -b && vite build` OK (87 modulos, sin errores).
   - `npm run test:e2e`: **22/22 passed (21.6s)**.
4. Comprobaciones puntuales (contenedor, sin tocar el repo): render real de `PreviewDocument` con y sin texto de requisitos futuros, y conversion DOCX->PDF con extraccion `pdftotext`.
   - Requisitos futuros `aplica=true` con **solo texto**: antes de T-027 `HAS_FUTURE_TEXT: False`,
     `HAS_NO_APLICA: True`; tras T-027 el texto se incluye y no aparece `No Aplica.` (cubierto por
     `test_render_future_requirements_includes_text_without_items` y por la clave `futuros clave` del PDF).
   - Encabezado generado: `HEADER_HAS_TICKET: True`, `HEADER_HAS_VERSION: True`; numeracion `1. Necesidad Actual ... 4.1 ... 4.2 ... 5. Diagramas Contextuales`.

## Criterios de aceptacion

| Criterio | Resultado | Evidencia |
|---|---|---|
| CA-01 | Cumple | `backend/tests/infrastructure/test_document_renderer.py:44` (`test_render_includes_header_ticket_and_document_version`, header1/header2 con `T#1` y `2.1`); `backend/tests/domain/test_preview.py:40` (numeracion 1..10 y 4.1/4.2); render real: `HEADER_HAS_TICKET: True` / `HEADER_HAS_VERSION: True` y secciones numeradas en PDF. |
| CA-02 | Cumple | `backend/tests/integration/test_document_conversion.py:104` (`test_pdf_preserves_key_texts_from_docx`): PDF obtenido del DOCX con LibreOffice y textos clave equivalentes; el PDF no se genera con otro motor (`document_converter.py:32-58`). Equivalencia muestreada (4 textos), no exhaustiva. |
| CA-03 | Cumple | `backend/tests/domain/test_preview.py:73` (`test_only_active_items_in_order_and_empty_content_omitted`) y `backend/tests/domain/test_preview.py:100` (beneficios por tipo/orden). |
| CA-04 | Cumple | `backend/tests/infrastructure/test_document_renderer.py:70` (`test_render_empty_collection_shows_no_aplica`); render real: `4.2 Beneficios Cuantitativos. No aplica`. |
| CA-05 | Cumple | Rama `false` OK (`test_document_renderer.py:76`, `test_preview.py:120`). Rama `true` corregida en T-027: `document_renderer.py` mapea la seccion con `_future_requirement_entries` (parrafos + items ordenados) y la plantilla imprime el texto; cubierto por `test_document_renderer.py::test_render_future_requirements_includes_text_without_items` y `::test_render_future_requirements_includes_text_and_ordered_items`, y en el PDF por la clave `futuros clave` de `test_document_conversion.py::test_pdf_preserves_key_texts_from_docx`. |
| CA-06 | Cumple | `test_document_renderer.py:64` (saltos de linea `<w:br/>`), `test_document_renderer.py:91` (escapado `a &lt; b &amp; c`), `test_document_renderer.py:86` (fecha `05-03-2026` en control de versiones); formato centralizado en `preview.py:77-79`. |
| CA-07 | Cumple | `backend/tests/domain/test_preview.py:190` (`test_version_control_lists_all_versions_ordered_with_null_description`) y `test_document_renderer.py:82` (tabla + firmas). `preview.py:86-94` lista todas las versiones ordenadas por numero. |
| CA-08 | Cumple | `test_preview.py:230` (roles en `None` cuando no hay firma) y `test_preview.py:238` (nombre/cargo cuando existe); `document_renderer.py:116-127` mapea a vacio sin alterar firmas. Spec admite vacio o "-". |
| CA-09 | Cumple | `backend/tests/application/test_generate_documents.py:53` (2 documentos con metadatos y BLOB); `backend/tests/infrastructure/test_document_mappers.py:23`; integracion `test_requirement_document_repository.py:95` (`test_blob_round_trip` real en Oracle); API `backend/tests/api/test_documents.py:83`. |
| CA-10 | Cumple | `test_generate_documents.py:73` y `:86` (sin registros ni transicion); API `test_documents.py:108` (`409 invalid_state_transition`) y `:127` (`409 document_generation_not_allowed`); mapeo en `errors.py:69-80`. |
| CA-11 | Cumple | `test_generate_documents.py:53` (transiciona a `GENERADO`); `test_documents.py:103` (GET requerimiento devuelve `GENERADO`). `generate_documents.py:84-86`. |
| CA-12 | Cumple | `test_generate_documents.py:101` (`test_regeneration_adds_documents_without_overwriting`, 4 filas, ids disjuntos); API `test_documents.py:157` (historico 4 sin binario); integracion lista sin `CONTENIDO` (`:115`). |
| CA-13 | Cumple | e2e `frontend/e2e/wizard.spec.ts:368` (deshabilitado con motivo) y `:385` (habilitado en `APROBADO`); `DocumentActions.tsx:8-16,48-54`; `Step13Review.tsx:130-144`. |
| CA-14 | Cumple | e2e `wizard.spec.ts:418` (fallo de generacion -> alerta y reintento sin romper el wizard); manejo de error en `useRequirementDocuments.ts:85-90` y `:105-107`. |
| CA-15 | Cumple | Comandos 1, 2 y 3 en verde (183 unitarias, 26 integracion, build OK, 22/22 e2e). |
| CA-16 | Cumple | `backend/tests/domain/test_document.py:12-33` (`T#1-v1.0.docx/pdf`); API `test_documents.py:178` (`Content-Disposition` con `T#1234-v1.0.docx`); e2e `wizard.spec.ts:415` (`suggestedFilename()`); schema en `document.py:32-36` y `client.ts:104-110`. |

## Hallazgos

1. **CA-05 - texto de requisitos futuros (corregido en T-027).**
   Hallazgo original: `document_renderer.py` trataba `requisitos_futuros` como coleccion y solo extraia
   bloques `lista`; el texto (`future_requirements_text`, bloque `parrafo` en `preview.py:249-251`) se
   descartaba y el DOCX mostraba `No Aplica.` con `aplica=true` y solo texto. Correccion: se elimino
   `requisitos_futuros` de `_COLLECTION_CODES` y se agrego `_future_requirement_entries`, que respeta el
   orden parrafo/lista y conserva saltos de linea (`Listing`). No se modifico la plantilla (ADR-004).

2. **Desviacion no documentada en `Step13Review.tsx` (GET al montar).**
   `Step13Review.tsx:38-47` refresca el estado con `getRequirement` y hace `SET_STATUS`, en lugar de
   derivarlo solo del `RequirementStatus` del wizard (plan T-022). No contradice CA-13/RF-14 (las pruebas
   de estado y el motivo deshabilitado siguen pasando), pero agrega una peticion extra y sobrescribe el
   estado local; conviene registrar la decision o alinearla con el plan.

3. **RF-03 - "primera fila" de control de versiones.** `preview.py:86` ordena ascendente por numero de
   version, por lo que la primera fila es la version mas antigua y no necesariamente la version
   documental consultada (que si aparece en los encabezados). Solo es observable con mas de una version;
   conviene confirmar la intencion con el machote.

4. **RF-18 / deuda de logotipos inconsistente.** El encabezado de `templates/ers_plantilla_v1.docx`
   referencia `media/image1.png` y `media/image2.png` (`word/_rels/header1.xml.rels`), con hash identico a
   las imagenes del `machote_requerimiento.docx`. Es decir, los logotipos del machote **si** estan
   incorporados, mientras el plan/T-001/verify declaran "espacio reservado, logotipos como deuda".
   Hay que aclarar si son los logos definitivos (y retirar la deuda) o placeholders.

5. **Generacion no atomica.** `generate_documents.py:71-86` persiste DOCX y PDF en transacciones
   independientes (`requirement_document_repository.py:44`) y la transicion de estado en otra; un fallo a
   mitad deja registros parciales sin transicion. Riesgo de baja probabilidad, no cubierto por pruebas.

6. **Restriccion unica con `GENERADO_AT`.** `REQ_DOCUMENTO_UQ` incluye `(REQUERIMIENTO_ID, VERSION_ID,
   FORMATO, GENERADO_AT)`; dos regeneraciones en el mismo instante (microsegundos) producirian
   `IntegrityError` -> 500. La prueba `test_duplicate_regeneration_timestamp_is_rejected` lo evidencia como
   comportamiento esperado, pero no como riesgo de concurrencia.

7. **Cobertura de pruebas desbalanceada.** No hay prueba de integracion que ejercite el caso de uso
   completo (renderer + converter + Oracle); el renderer ya cubre el caso "solo texto"/texto+items de CA-05
   (T-027) y falta una version con multiples filas de control. La equivalencia DOCX/PDF es muestreada.

## Arquitectura hexagonal y convenciones

- Cumple: `domain/requirement/document.py` es puro (sin FastAPI/SQLAlchemy/docxtpl); los puertos viven en
  `application/ports/*` y los adaptadores en `infrastructure/adapters/*`; el router `api/routers/documents.py`
  solo valida/invoca/serializa; no hay logica de negocio en rutas. DDL solo via Alembic
  (`0003_documentos_generados.py`). BLOB con `LargeBinary` en `tables.py:229`.
- Sin violaciones de hexagono detectadas.

## Deuda tecnica registrada

- `document_max_bytes` (`config.py:32`, `.env.example`) **no se aplica** en ningun adaptador: el limite de
  tamano del plan no se enforce. No hay error ni prueba asociada.
- Logotipos del encabezado: contradiccion entre "deuda pendiente" y la presencia real de imagenes del
  machote (ver Hallazgo 4).
- `GENERADO_BY` fijo en `SYSTEM` (actor real diferido a SPEC-008; `generate_documents.py:30,59`).
- Descripcion del cambio en control de versiones vacia/"-": deuda del modelo aceptada por la spec
  (`document_renderer.py:110`).
- Anexos/imagenes de "Diagramas Contextuales" diferidos a la spec de storage: siguen como metadatos.
- Equivalencia DOCX/PDF verificada por muestreo de textos (no comparacion estructural completa).

## Criterios no verificados o parciales

- CA-05: **Cumple** tras la correccion T-027 (antes No cumple).
- CA-02: verificado por integracion y por construccion (PDF del DOCX), pero la equivalencia no se comprueba
  estructuradamente de forma exhaustiva.
