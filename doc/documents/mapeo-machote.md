# Mapeo del machote institucional a modelo de datos y plantilla DOCX

Fuente analizada: `templates/machote_requerimiento.docx` (versión de referencia, no modificar).
Este documento es el contrato entre el modelo estructurado (Oracle) y la presentación (Word).

## 1. Hallazgos sobre el archivo

1. **El machote no es una plantilla vacía**: es un requerimiento ya redactado (Tesorería / pases de caja) y sin etiquetas de plantilla. Hay que derivar una plantilla `docxtpl` (ver sección 5). El original se conserva intacto como referencia visual.
2. **Hoja Carta**, márgenes de 2.5 cm (sup/inf) y 2 cm (izq/der), **primera página distinta** (`titlePg`) y numeración que inicia en 0.
3. **Encabezado** (2 archivos: página normal `header1` y primera página `header2`) con logotipos, el texto "Especificación de Requerimientos de Software", el **ticket** (`T#64508394`) y **"VERSIÓN DOCUMENTO: 1.0"**. Los valores de ticket y versión deben sustituirse en ambos encabezados.
4. **Pie de página**: solo número de página (campo `PAGE`) y elementos decorativos; sin datos variables.
5. **Cuerpo**: 2 tablas (Control de versiones y Firmas) y 12 secciones con estilos propios (`Ttulo1`, `Ttulo2`, `Ttulo3`, `textotitulo2`, `Prrafodelista`, etc.). Los títulos `Ttulo2` usan numeración automática de Word (lista 8); los subtítulos 4.1 y 4.2 llevan el número **escrito a mano**.
6. **Controles de contenido (sdt)** en celdas de las tablas y en dos textos del cuerpo: deben aplanarse en la plantilla porque complican el reemplazo.
7. **Sin imágenes en el cuerpo**: los 4 PNG del archivo son del encabezado y pie. El soporte de anexos en "Diagramas Contextuales" no tiene referencia visual y debe definirse (tamaño, alineación, leyenda).
8. **Defectos del machote a limpiar** al derivar la plantilla:
   - 3 viñetas numeradas vacías (1., 2., 3.) al inicio de "Consideraciones".
   - Párrafos vacíos sueltos entre secciones y filas vacías en las tablas.
   - El segundo riesgo usa el estilo `Listaconnmeros` y no el de viñeta del resto.
   - "Manejo de errores" tiene espacios iniciales en lugar de sangría.

## 2. Mapeo de secciones

| # Doc | Sección | Tipo | Campo de dominio | Construcción en plantilla |
|---|---|---|---|---|
| — | Control de versiones | Tabla (5 columnas) | `versiones[]`: versión, fecha, descripción del cambio, revisó, elaboró | Fila repetida `{%tr for v in versiones %}` |
| — | Firmas | Tabla (3 columnas) | `firmantes`: elaboró, revisó, autorizó (nombre + cargo) | Texto simple `{{ firmas.elaboro.nombre }}` y cargo |
| 1 | Necesidad Actual | Párrafo | `necesidad_actual` (texto) | `{{ necesidad_actual }}` |
| 2 | Objetivos Generales | Lista de viñetas | `objetivos[]` | `{%p for o in objetivos %}` … `{{ o.contenido }}` … `{%p endfor %}` |
| 3 | Consideraciones | Lista de viñetas | `consideraciones[]` | Igual que objetivos |
| 4 | Beneficios Esperados | Contenedor | — | Título fijo |
| 4.1 | Beneficios Cualitativos | Lista de viñetas | `beneficios[tipo=CUALITATIVO]` | Bucle de párrafo |
| 4.2 | Beneficios Cuantitativos | Lista de viñetas | `beneficios[tipo=CUANTITATIVO]` | Bucle de párrafo |
| 5 | Diagramas Contextuales | Párrafo + subsección + imágenes | `contexto.descripcion`, `contexto.manejo_errores` (opcional), `anexos[]` | `{{ }}`, bloque condicional `{%p if %}` y `InlineImage` por anexo |
| 6 | Usuarios y Permisos | Párrafo | `usuarios_permisos` (texto) | `{{ }}` |
| 7 | Restricciones | Lista de viñetas | `restricciones[]` | Bucle de párrafo |
| 8 | Requisitos futuros | Párrafo / lista | `requisitos_futuros.aplica`, `.texto`, `.items[]` | `{%p if aplica %}` lista/texto `{%p else %}` "No Aplica." |
| 9 | Volumetría y Rendimiento | Lista de viñetas | `volumetria[]` | Bucle de párrafo |
| 10 | Riesgos Iniciales | Lista de viñetas | `riesgos[]` (MVP: solo texto) | Bucle de párrafo |

### Encabezado y pie

| Elemento | Origen | Archivos a etiquetar |
|---|---|---|
| Ticket / folio externo | `requerimiento.ticket` | `header1.xml` y `header2.xml` |
| Versión del documento | `version.version_documento` | `header1.xml`, `header2.xml` y primera fila de control de versiones |
| Número de página | Campo Word `PAGE` | Sin cambio |

La versión documental se captura **una sola vez** y alimenta los tres lugares donde aparece.

## 3. Reglas de generación

- Colecciones: solo elementos con `activo = 'S'`, ordenados por `orden`. Un elemento sin contenido no genera viñeta.
- Sección sin elementos: se conserva el título, no queda viñeta vacía y se imprime el texto **"No aplica"** (ver P-04).
- Texto del usuario con saltos de línea: se convierte a saltos de línea Word (`RichText`/`Listing` de `docxtpl`) y se escapa el XML (`autoescape`).
- Fechas en formato `dd-mm-aaaa`.
- Vista previa, DOCX y PDF consumen **el mismo DTO de renderizado** construido a partir de una versión congelada; ningún renderizador consulta datos vivos.
- El PDF se obtiene convirtiendo el DOCX generado con LibreOffice (ADR-001), no con un segundo motor.
- Fuentes del machote instaladas en la imagen Docker para que el PDF no sustituya tipografías.

## 4. Brechas entre la spec funcional y el machote

| Id | Observación | Propuesta |
|---|---|---|
| B-01 | La tabla de control de versiones tiene **Revisó y Elaboró por versión** pero no Autorizó; la spec solo describe un Elaboró/Revisó/Autorizó global. | Resuelto: guardar Elaboró y Revisó en cada versión; Autorizó solo en la tabla de firmas de la versión vigente. |
| B-02 | La spec define Volumetría como texto; el machote la presenta con viñetas. | Resuelto (P-01): Volumetría se modela como colección ordenada de elementos. |
| B-03 | Spec lista Control de versiones y Firmas como secciones 1 y 2; en el documento no están numeradas (la numeración inicia en Necesidad Actual). | Resuelto: numerar el contenido como en el machote (Necesidad Actual = 1). |
| B-04 | Los cargos de la tabla de Firmas vienen precargados en el machote. | Resuelto (P-02): catálogo por rol con valor por defecto editable. |

## 5. Preparación de la plantilla `docxtpl`

Archivo objetivo: `templates/ers_plantilla_v1.docx` (versionada). Pasos:

1. Copiar el machote y **quitar el contenido de ejemplo**.
2. Aplanar los controles de contenido (sdt).
3. Eliminar viñetas vacías, párrafos sueltos y filas sobrantes de las tablas.
4. Unificar estilo de viñeta (el segundo riesgo).
5. Convertir 4.1 y 4.2 a numeración automática de lista multinivel.
6. Insertar etiquetas Jinja asegurando que **cada etiqueta quede en un solo "run"** de Word (si Word la parte, no se reemplaza).
7. Etiquetar `header1.xml` y `header2.xml`.
8. Definir el bloque de anexos con `InlineImage`: ancho máximo = ancho útil de página (17.4 cm aprox.), imagen centrada y leyenda/pie de figura numerado por anexo (ver P-05).
9. Prueba de humo: renderizar un dataset de ejemplo y comparar visualmente con el machote original (DOCX → PDF → imagen).

Riesgo principal del proyecto: **fidelidad DOCX/PDF**. Se recomienda un *spike* técnico temprano (antes de SPEC-007) que renderice el machote con datos de ejemplo.

## 6. Decisiones tomadas (antes preguntas pendientes)

| Id | Pregunta | Decision |
|---|---|---|
| P-01 | Volumetría y Rendimiento: ¿lista de elementos o texto narrativo? | Lista de elementos (colección ordenada con id, orden, contenido y estado), igual que objetivos y riesgos. |
| P-02 | Cargos de firmas: ¿fijos institucionales o catálogo? | Catálogo por rol con valor por defecto editable en el requerimiento. |
| P-03 | Ticket: ¿el prefijo `T#` es fijo o el folio se captura completo? | Prefijo `T#` fijo definido por el sistema; el usuario captura solo el número, que es único. |
| P-04 | Sección de colección vacía: ¿omitir o "No aplica"? | Se conserva el título y se imprime **"No aplica"**. |
| P-05 | Anexos: tamaño, alineación y leyenda. | Ancho útil (17.4 cm), centrada y con leyenda/pie de figura numerado. |

Regla de alcance UI: los mockups de Stitch (`doc/ui/`) son guía de estilo, componentes y estados. El wizard sigue las secciones del machote; no se incorporan secciones ajenas (requerimientos funcionales/no funcionales, IEEE 830).
