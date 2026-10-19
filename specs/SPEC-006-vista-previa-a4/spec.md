# SPEC-006 - Vista previa A4 del requerimiento

- Estado: verificada
- Fecha: 2026-10-19
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/documents/mapeo-machote.md`, `doc/ui/wizard-flow.md`, `doc/ui/componentes.md`, `doc/ui/design/STITCH_DESIGN.md`, `doc/technical/api.md`, `doc/development/convenciones.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/007-firmas-segun-estado.md`
- Depende de: SPEC-001-fundaciones, SPEC-002-modelo-dominio-requerimiento, SPEC-003-api-requerimientos, SPEC-004-wizard-captura, SPEC-005-validacion-integral-y-maquina-de-estados

## Contexto y objetivo

SPEC-004 dejo el paso 13 del wizard como un shell de revision sin vista previa, y SPEC-005 dejo disponible la validacion integral y el estado persistido. La spec funcional y el mapeo del machote exigen que la vista previa, el DOCX y el PDF se construyan desde el mismo contenido y version, sin que ningun renderizador consulte datos vivos.

El objetivo de esta SPEC es mostrar en el paso 13 del wizard una vista previa A4 de solo lectura, fiel a la estructura del machote, construida por el backend desde la version persistida mediante un DTO neutral de renderizado que la futura generacion DOCX/PDF (SPEC-007) reutilizara.

## Alcance

### Incluye

- Backend: caso de uso `BuildPreviewDocument` que compone el DTO de renderizado a partir de una version persistida.
- Backend: endpoint `GET /api/v1/requerimientos/{id}/versiones/{vid}/vista-previa` con el contrato `PreviewDocument`.
- Backend: reglas de normalizacion del contenido (solo elementos activos, orden, secciones vacias como "No aplica", requisitos futuros condicionales, fechas `dd-mm-aaaa`).
- Backend: tabla de control de versiones (historico) y bloque de firmas de la version consultada, con valores nulos cuando no existen.
- Frontend: vista previa A4 simulada en el paso 13, con encabezado institucional en texto (titulo institucional, ticket `T#` y version del documento), secciones, tablas de control de versiones y firmas.
- Frontend: cliente `GET .../vista-previa`, tipos espejo, hook de carga y manejo de errores.
- Frontend: aviso de cambios sin guardar y accion "Actualizar vista previa" tras el autosave.
- Frontend: boton "Imprimir" con estilos de impresion que muestran solo la hoja A4.
- Pruebas backend (dominio/aplicacion/API) y pruebas e2e del paso 13 con Playwright.
- Documentacion del contrato en `doc/technical/api.md`.

### No incluye

- Generacion de DOCX/PDF ni la plantilla `docxtpl` (SPEC-007).
- Paginacion real, saltos de pagina exactos del machote y numeracion de paginas del documento (SPEC-007).
- Logotipos institucionales reales: el encabezado reserva un espacio neutro; la extraccion de los PNG del machote y la fidelidad final quedan para SPEC-007.
- Anexos e imagenes en "Diagramas Contextuales" (ADR-006 y spec de storage).
- Captura de "Descripcion del cambio" y de firmas: se representan con "—"; persisten como deuda.
- Vista previa desde el listado de requerimientos o una pantalla de detalle (solo paso 13).
- Asistencia IA (spec final, posterior a DOCX/PDF).
- Autenticacion, roles y enforcement (SPEC-008).
- Nuevas tablas Oracle, migraciones Alembic o cambios de persistencia.

## Requisitos funcionales

- RF-01. El backend expone `GET /api/v1/requerimientos/{id}/versiones/{vid}/vista-previa`, que devuelve el `PreviewDocument` de la version indicada.
- RF-02. El `PreviewDocument` se construye exclusivamente desde la version persistida (fuente de verdad); la operacion es de solo lectura, no persiste cambios ni altera estado.
- RF-03. El DTO incluye encabezado (`folio`, `ticket`, `titulo`, `version_documento`, `fecha_version`) y una lista ordenada de secciones con `codigo`, `numero`, `titulo` y bloques de contenido.
- RF-04. Los bloques de contenido son de tipo `parrafo` (texto), `lista` (elementos) o `no_aplica`; el backend decide el tipo y normaliza el contenido para que ningun renderizador aplique reglas propias.
- RF-05. Las colecciones incluyen solo elementos activos, ordenados por `orden`; los elementos sin contenido no generan viñeta.
- RF-06. Una seccion de coleccion sin elementos conserva su titulo y devuelve un bloque `no_aplica` ("No aplica").
- RF-07. Requisitos futuros: si `requisitos_futuros_aplica=false`, devuelve bloque `no_aplica` ("No Aplica."); si aplica, devuelve el texto y/o los elementos activos ordenados. Se permiten texto y lista en la misma seccion.
- RF-08. Las fechas se devuelven formateadas como `dd-mm-aaaa`.
- RF-09. El DTO incluye la tabla de control de versiones con todas las versiones del requerimiento ordenadas, cada una con version, fecha, descripcion del cambio (`null` en esta spec), reviso y elaboro.
- RF-10. El DTO incluye el bloque de firmas de la version consultada (`elaboro`, `reviso`, `autorizo`) con nombre y cargo, o `null` cuando no existen, conforme a ADR-007.
- RF-11. El paso 13 conserva el resumen del estado de los pasos y agrega la vista previa A4 de la version de trabajo actual, cargada desde el endpoint.
- RF-12. La vista previa es de solo lectura y no modifica el estado del wizard, el requerimiento ni sus versiones.
- RF-13. Si el wizard tiene cambios sin guardar, la vista previa lo advierte y ofrece "Actualizar vista previa" despues del autosave; la vista previa siempre refleja la ultima version persistida.
- RF-14. La hoja A4 simulada usa tamano carta, margenes de 2.5 cm (superior/inferior) y 2 cm (izquierdo/derecho), tipografia y estructura de secciones del machote, y se escala para caber en el area de trabajo sin perder legibilidad.
- RF-15. El boton "Imprimir" abre el dialogo de impresion del navegador con estilos `@media print` que ocultan el shell de la aplicacion y muestran unicamente la hoja A4.
- RF-16. Si la carga falla (404, error de red o envelope de error), el paso 13 muestra el mensaje correspondiente sin romper el wizard y permite reintentar.
- RF-17. La funcionalidad opera sin IA (`AI_PROVIDER=none`) y no incorpora dependencias nuevas no justificadas.

## Criterios de aceptacion

- CA-01. Dado un requerimiento y version existentes, cuando se consulta `GET .../vista-previa`, entonces responde `200` con `PreviewDocument` y el encabezado incluye `ticket` (`T#` + folio) y `version_documento`.
- CA-02. Dado un requerimiento o version inexistente, cuando se consulta el endpoint, entonces responde `404` con el envelope de error (`requirement_not_found` / `version_not_found`).
- CA-03. Dada una version con elementos activos e inactivos, cuando se genera la vista previa, entonces solo aparecen los activos y en el orden definido por `orden`.
- CA-04. Dada una coleccion sin elementos activos, cuando se genera la vista previa, entonces la seccion conserva su titulo y devuelve un bloque `no_aplica` con el texto "No aplica".
- CA-05. Dado `requisitos_futuros_aplica=false`, cuando se genera la vista previa, entonces la seccion devuelve "No Aplica." y no incluye texto ni elementos; dado `true`, entonces incluye el texto y/o la lista capturada.
- CA-06. Dadas las fechas de version y de control de versiones, cuando se genera el DTO, entonces todas se devuelven en formato `dd-mm-aaaa`.
- CA-07. Dado un requerimiento con varias versiones, cuando se genera la vista previa, entonces la tabla de control de versiones incluye todas ordenadas y la descripcion del cambio se representa como `null`.
- CA-08. Dada una version sin firmas registradas, cuando se genera la vista previa, entonces `firmas` devuelve `null` por rol y la UI muestra "—"; dada una version con firmas (estado `APROBADO`/`GENERADO`), entonces muestra nombre y cargo sin crear ni modificar firmas.
- CA-09. Dado el paso 13, cuando se activa la vista previa, entonces se muestra la hoja A4 con encabezado, secciones, listas y tablas coherentes con el DTO recibido y con el machote.
- CA-10. Dado el paso 13 con cambios sin guardar, cuando se activa la vista previa, entonces se muestra el aviso y, tras guardar, "Actualizar vista previa" refleja los datos persistidos.
- CA-11. Dado el paso 13 con la vista previa visible, cuando se pulsa "Imprimir", entonces el dialogo de impresion presenta solo la hoja A4, sin barra lateral ni acciones de la aplicacion.
- CA-12. Dado un fallo del endpoint, cuando se activa la vista previa, entonces se muestra un mensaje legible, el wizard conserva su estado y se ofrece reintentar.
- CA-13. Dado el repositorio, cuando se ejecutan `ruff check .`, `mypy --strict app`, `pytest`, la compilacion de tipos y el build del frontend y las pruebas e2e del paso 13, entonces no hay errores.

## Reglas de negocio y validaciones

- La base de datos es la fuente de verdad: la vista previa se genera desde la version persistida y nunca desde el estado local del wizard.
- La vista previa es de solo lectura: no crea firmas, no transiciona estados y no persiste cambios.
- Solo se incluyen elementos activos, ordenados por `orden`; los elementos sin contenido no generan viñeta.
- Seccion de coleccion vacia: se conserva el titulo y se imprime "No aplica" (decision P-04 de `doc/documents/mapeo-machote.md`).
- Requisitos futuros: `false` se representa como "No Aplica."; `true` admite texto y/o elementos activos.
- Beneficios: cualitativos y cuantitativos son subsecciones independientes (4.1 y 4.2) dentro de "Beneficios Esperados".
- Numeracion del machote: Necesidad Actual = 1, Objetivos = 2, Consideraciones = 3, Beneficios = 4 (4.1/4.2), Diagramas Contextuales = 5, Usuarios y Permisos = 6, Restricciones = 7, Requisitos futuros = 8, Volumetria = 9, Riesgos = 10. Control de versiones y Firmas no se numeran (B-03).
- No se incorporan secciones ajenas al machote (por ejemplo, requerimientos funcionales/no funcionales o IEEE 830).
- Fechas siempre en `dd-mm-aaaa`.
- "Descripcion del cambio" no existe en el modelo: se devuelve `null` y la UI muestra "—".
- Firmas: solo existen si fueron registradas en `APROBADO`/`GENERADO` (ADR-007); la vista previa no las captura ni las altera.
- La aplicacion opera sin IA; no hay sugerencias ni contenido generado automaticamente.

## Datos involucrados (a nivel funcional)

Contrato API consumido:

```
GET /api/v1/requerimientos/{id}/versiones/{vid}/vista-previa

PreviewDocument {
  folio: number
  ticket: string
  titulo: string
  version_documento: string
  fecha_version: string            // dd-mm-aaaa
  secciones: PreviewSection[]
  control_versiones: PreviewVersionRow[]
  firmas: PreviewFirmas
}

PreviewSection {
  codigo: string                   // "necesidad_actual", "objetivos", "beneficios_cualitativos", ...
  numero: string                   // "1" .. "10", "4.1", "4.2"
  titulo: string
  bloques: PreviewBlock[]
}

PreviewBlock {
  tipo: "parrafo" | "lista" | "no_aplica"
  texto?: string
  items?: string[]
}

PreviewVersionRow {
  version: string
  fecha: string                    // dd-mm-aaaa
  descripcion_cambio: string | null
  reviso: string | null
  elaboro: string | null
}

PreviewFirmas {
  elaboro: PreviewSigner | null
  reviso: PreviewSigner | null
  autorizo: PreviewSigner | null
}

PreviewSigner {
  nombre: string
  cargo: string | null
}
```

Modelo de UI en el frontend:
- `PreviewDocument` y tipos espejo del contrato.
- Cliente `api/preview.ts` y hook de carga por `requerimiento_id`/`version_id`.
- Componentes: hoja A4, seccion con bloques, tabla de control de versiones, bloque de firmas y aviso de cambios sin guardar.
- Estado: carga, datos, error y reintento; sin persistencia propia.

Persistencia: sin cambios. No hay tablas nuevas ni migraciones Alembic.

## Requisitos no funcionales aplicables

- Arquitectura hexagonal: la composicion del documento vive en `application`/`domain`; el router solo valida entrada, invoca el caso de uso y serializa.
- Tipado completo; `ruff check .`, `mypy --strict app` y `pytest` sin errores.
- Frontend con TypeScript estricto, compilacion de tipos y build de produccion sin errores.
- Sin dependencias nuevas no justificadas (regla 6 de `AGENTS.md`).
- Fidelidad visual basada en los tokens de `doc/ui/design/STITCH_DESIGN.md` ya reflejados en `frontend/src/index.css`; no duplicar valores en componentes.
- Estilos de impresion aislados con `@media print`; la hoja debe imprimirse en tamano carta con los margenes definidos.
- La vista previa debe ser usable en los breakpoints del sistema de diseno; en pantallas pequenas se permite desplazamiento/zoom sin romper la hoja.
- Errores consistentes con el envelope unico de la API y mensajes de usuario en espanol.
- La aplicacion funciona sin IA (`AI_PROVIDER=none`).
- Pruebas e2e con Playwright, con mock de la API por interceptacion de rutas.

## Decisiones tomadas

- **Si:** DTO neutral de renderizado generado por el backend; el frontend solo pinta y SPEC-007 reutiliza el mismo contrato para DOCX/PDF.
- **Si:** vista previa disponible solo en el paso 13 del wizard (componente reutilizable para futuras pantallas).
- **Si:** la vista previa muestra la version persistida; los cambios sin guardar solo generan aviso y accion de actualizacion.
- **Si:** hoja A4 simulada continua con boton "Imprimir"; paginacion exacta y PDF quedan para SPEC-007.
- **Si:** representar datos ausentes con "—" (descripcion del cambio y firmas), sin capturarlos en esta spec.
- **Si:** sin tablas nuevas ni migraciones Alembic.
- **No:** logotipos reales en esta spec (se reserva espacio; extraccion y fidelidad final en SPEC-007).
- **No:** anexos/imagenes, vista previa desde listado/detalle, IA y auth/roles.

## Riesgos identificados

| Riesgo | Mitigacion |
|---|---|
| Divergencia entre vista previa, DOCX y PDF | Un unico `PreviewDocument` construido por el backend; pruebas del contrato y reutilizacion obligatoria en SPEC-007 |
| Fidelidad visual limitada al no paginar como Word | Se comunica como simulacion A4; paginacion real y comparacion visual en SPEC-007 |
| Reglas de normalizacion ("No aplica", activos, orden) duplicadas en el cliente | El backend decide bloques y contenido; el frontend no aplica reglas de negocio |
| Confusion por cambios sin guardar | Aviso explicito y accion "Actualizar vista previa" tras el autosave |
| Crecimiento del DTO con requerimientos grandes | DTO plano de secciones y bloques; sin imagenes ni anexos en esta spec |

## Preguntas abiertas

Ninguna. Las decisiones de alcance, contrato, frescura de datos, fidelidad y datos ausentes fueron cerradas con el usuario el 2026-10-19.
