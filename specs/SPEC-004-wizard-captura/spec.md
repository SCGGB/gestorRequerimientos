# SPEC-004 - Wizard de captura

- Estado: Aprobada
- Fecha: 2026-10-15
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/ui/wizard-flow.md`, `doc/ui/componentes.md`, `doc/ui/design/STITCH_DESIGN.md`, `doc/documents/mapeo-machote.md`, `doc/technical/api.md`, `doc/development/convenciones.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/007-firmas-segun-estado.md`
- Depende de: SPEC-001, SPEC-003

## Contexto y objetivo
Construir la interfaz web del frontend (React + Vite + TypeScript + Tailwind) que guía al usuario en la captura escalonada del requerimiento según las secciones del machote institucional, además del listado de requerimientos, consumiendo la API `/api/v1` publicada por SPEC-003 sin acceder directamente a la persistencia. El modelo estructurado en Oracle sigue siendo la fuente de verdad; las screens de Stitch son referencia visual y su HTML no es código del proyecto.

## Alcance

### Incluye
- Shell de aplicación con barra lateral de navegación: `Requerimientos` y `Nuevo Requerimiento` operativas; `Plantillas ERS/SRS`, `Repositorio Documental` y `Configuración y Catálogos` como páginas placeholder.
- Pantalla de listado de requerimientos: filtros por `estado` y `folio`, paginación, badges de estado y acción de alta.
- Wizard de captura de 13 pasos con riel vertical (stepper) y estados `pendiente`, `activo`, `completado` y `error`; pasos 1 a 12 funcionales y paso 13 como shell de revisión.
- Paso 1 (datos generales) con alta del requerimiento y edición de cabecera; el ticket se muestra como `T#` + folio.
- Pasos narrativos (2 necesidad, 6 descripción contextual y manejo de errores, 7 usuarios y permisos, 9 requisitos futuros) mediante edición de la versión.
- Pasos de colección (3 objetivos, 4 consideraciones, 5 beneficios cualitativos/cuantitativos, 8 restricciones, 10 volumetría, 11 riesgos) con agregar, editar, eliminar (baja lógica) y reordenar.
- Paso 6 acotado a descripción contextual y manejo de errores (texto), sin anexos ni imágenes.
- Paso 12 (control documental) como captura de UI de Elaboró/Revisó/Autorizó (nombre + cargo desde catálogo), sin persistencia de firmas.
- Paso 13 como shell de revisión (sin vista previa ni generación documental).
- Catálogos de lectura para poblar selects: tipos de cambio y cargos por rol.
- Bloqueo de la acción "siguiente" cuando el paso no cumple sus obligatorios, con el motivo visible.
- Guardado del borrador con autosave (debounce) más acción explícita "Guardar borrador".
- Manejo en la UI del envelope de error de la API (`{"error": {"code", "message", "details"}}`).
- Presentación del estado del requerimiento con los badges definidos en `doc/ui/componentes.md`.
- Pruebas end-to-end con Playwright y verificación de calidad del frontend (tipos y build).

### No incluye
- Vista previa A4 y generación de DOCX/PDF (SPEC-007); el paso 13 no genera documentos.
- Reglas de negocio condicionales y validación integral del requerimiento (SPEC-005); aquí solo se valida la forma y los obligatorios por paso en el cliente.
- Asistencia IA y panel de sugerencias (SPEC-006); cualquier referencia visual de IA queda deshabilitada.
- Autenticación, usuarios, roles, login y enforcement (SPEC-008).
- Subida de binarios de anexos y adaptador de `StoragePort` (ADR-006); los anexos se difieren y el paso 6 solo captura texto.
- "Descripción del cambio" de la tabla Control de versiones: el modelo no tiene ese campo; no se captura ni persiste. Deuda registrada para una spec de backend.
- CRUD de catálogos (solo lectura).
- Firma electrónica (ADR-005).

## Requisitos funcionales
- RF-01. El frontend presenta un shell con barra lateral de navegación; las entradas operativas son `Requerimientos` y `Nuevo Requerimiento`, y las restantes (`Plantillas ERS/SRS`, `Repositorio Documental`, `Configuración y Catálogos`) muestran una página placeholder.
- RF-02. La pantalla de listado consume `GET /api/v1/requerimientos` con filtros opcionales `estado` y `folio` y paginación `page`/`size`, y muestra cada requerimiento con su ticket (`T#` + folio), su título y su estado.
- RF-03. El listado ofrece una acción para crear un requerimiento nuevo que abre el wizard en el paso 1.
- RF-04. El wizard se compone de 13 pasos con un riel vertical que refleja el estado de cada paso (`pendiente`, `activo`, `completado`, `error`), y expone las acciones "paso anterior", "guardar borrador" y "siguiente"; "siguiente" se bloquea cuando el paso no cumple sus obligatorios e indica el motivo.
- RF-05. El paso 1 captura folio (solo número; el prefijo `T#` es fijo y de solo lectura), título, tipo de cambio (desde catálogo), sistema, versión documental y fecha de versión; al confirmar crea el requerimiento con `POST /api/v1/requerimientos`. Una vez creado, la edición de la cabecera usa `PATCH /api/v1/requerimientos/{id}/versiones/{vid}`.
- RF-06. Los pasos 2 (necesidad actual), 6 (descripción contextual y manejo de errores), 7 (usuarios y permisos) y 9 (requisitos futuros, con opción "No aplica") editan la versión vigente mediante `PATCH /api/v1/requerimientos/{id}/versiones/{vid}`.
- RF-07. Los pasos de colección (3 objetivos, 4 consideraciones, 5 beneficios, 8 restricciones, 10 volumetría, 11 riesgos) permiten agregar, editar, eliminar (baja lógica) y reordenar elementos contra los endpoints de colecciones; cada elemento conserva identificador, orden, contenido y estado activo.
- RF-08. El paso 5 presenta dos secciones independientes (beneficios cualitativos y cuantitativos) sobre la colección `beneficios`, enviando el discriminador `tipo` al crear.
- RF-09. El paso 9 permite marcar "No aplica" (`requisitos_futuros_aplica=false`); cuando aplica, captura el texto (`requisitos_futuros_texto`) y administra la colección `requisitos-futuros`.
- RF-10. El paso 12 captura Elaboró, Revisó y Autorizó (nombre y cargo) usando el catálogo de cargos por rol; esta captura es solo de UI y no registra firmas en la API.
- RF-11. El paso 13 presenta un shell de revisión con el resumen de los pasos y su estado, sin vista previa ni generación documental, y sin registrar firmas.
- RF-12. El frontend ofrece autosave con debounce para los campos de cabecera y narrativa de la versión, además de una acción explícita "Guardar borrador"; las operaciones de colecciones se persisten al ejecutarse.
- RF-13. El frontend consume `GET /api/v1/catalogos/tipos-cambio` para el paso 1 y `GET /api/v1/catalogos/cargos?rol=` para el paso 12.
- RF-14. El frontend interpreta el envelope de error de la API (`{"error": {"code", "message", "details"}}`) y lo presenta de forma legible en la interfaz, sin romper el estado del formulario.
- RF-15. El frontend consume la API bajo el prefijo `/api/v1` mediante un cliente HTTP propio; en desarrollo usa el proxy de Vite y en producción el proxy de Nginx, sin exponer la URL interna del backend en el código del bundle del navegador.
- RF-16. El frontend no introduce dependencias nuevas más allá de las ya declaradas (React, Vite, TypeScript, Tailwind, Playwright); la navegación lista/wizard y el estado se implementan con estado interno y `Context`/`useReducer`.
- RF-17. El backend expone el `titulo` de la versión vigente en el resumen del listado (`RequirementSummary`), de modo que la tabla del listado pueda mostrar la columna de título.

## Criterios de aceptacion
- CA-01. Dado el frontend cargado, cuando se abre la aplicación, entonces se muestra el shell con la barra lateral y la entrada `Requerimientos` activa; las entradas no operativas muestran su página placeholder.
- CA-02. Dado el listado, cuando se aplican filtros `estado`/`folio` y se cambia de página, entonces la tabla refleja `{items, total, page, size}` devuelto por la API, mostrando ticket (`T#` + folio), título y estado.
- CA-03. Dado el listado, cuando se pulsa "Nuevo", entonces se abre el wizard en el paso 1 con el prefijo `T#` fijo y el folio vacío.
- CA-04. Dado el paso 1 con datos válidos, cuando se confirma, entonces se crea el requerimiento vía `POST /api/v1/requerimientos` y el wizard avanza conservando el `id` y la versión de trabajo creados.
- CA-05. Dado un paso con obligatorios sin cumplir, cuando se intenta avanzar, entonces la acción "siguiente" queda bloqueada y se muestra el motivo.
- CA-06. Dado el paso 3 (objetivos) u otra colección, cuando se agrega, edita, elimina o reordena un elemento, entonces el cambio se refleja al recargar el agregado y el elemento eliminado deja de listarse (baja lógica).
- CA-07. Dado el paso 5, cuando se registran beneficios cualitativos y cuantitativos, entonces cada uno se muestra en su sección y conserva su `tipo`.
- CA-08. Dado el paso 9 con "No aplica" activado, cuando se guarda el borrador, entonces la versión queda con `requisitos_futuros_aplica=false`.
- CA-09. Dado el paso 6, cuando se captura la descripción contextual y el manejo de errores, entonces se persisten en la versión; el paso no ofrece carga de imágenes ni anexos.
- CA-10. Dado el paso 12 con nombre y cargo seleccionados, cuando se avanza, entonces la captura es de UI y no se registra ninguna firma en la API.
- CA-11. Dado un error de negocio de la API (por ejemplo folio duplicado `409`), cuando el frontend recibe el envelope de error, entonces muestra el mensaje correspondiente sin perder los datos del formulario.
- CA-12. Dado el frontend en ejecución, cuando se consulta el bundle de producción, entonces las llamadas se realizan contra `/api/v1` de forma relativa (proxy), sin URLs internas del backend embebidas.
- CA-13. Dado un listado con requerimientos, cuando el backend responde `RequirementSummary`, entonces cada item incluye `titulo` y la tabla lo muestra.
- CA-14. Dado el árbol del repositorio, cuando se ejecutan las verificaciones de calidad del frontend (compilación de tipos y build de producción) y las pruebas e2e de Playwright, entonces no hay errores.

## Reglas de negocio y validaciones
- El wizard sigue las secciones del machote; no incorpora secciones ajenas (requerimientos funcionales/no funcionales, IEEE 830).
- Ticket: prefijo `T#` fijo y de solo lectura; el usuario captura únicamente el número de folio (entero positivo).
- Edición: el wizard opera sobre la versión de trabajo; si el requerimiento no está en `BORRADOR`, la edición se deshabilita en la UI y se informa el motivo (la API responde `409`).
- Validación de UI: solo obligatorios y forma por paso (bloqueo de "siguiente"); la validación condicional e integral es responsabilidad de SPEC-005.
- Colecciones: elementos independientes con id, orden, contenido y estado; la eliminación es baja lógica; el reorden se envía como lista de ids.
- Beneficios: cualitativos y cuantitativos comparten la colección `beneficios` y se separan por el discriminador `tipo`.
- Requisitos futuros: "No aplica" fuerza `requisitos_futuros_aplica=false`; si aplica, se permite texto y/o elementos.
- Paso 12: la captura de firmantes no se persiste en `BORRADOR` (ADR-007); se trata como captura de UI.
- Autosave: la versión se actualiza con debounce; las operaciones sobre colecciones se persisten inmediatamente.
- La aplicación opera sin IA; cualquier elemento de IA en la referencia visual se muestra deshabilitado o ausente.
- Los textos de usuario se muestran en español; el código y los identificadores en inglés.

## Datos involucrados (a nivel funcional)

Contratos consumidos de la API (SPEC-003):
- `POST /api/v1/requerimientos` → `RequirementResponse`.
- `GET /api/v1/requerimientos?estado=&folio=&page=&size=` → `RequirementPage` (`items[]` con `id`, `folio`, `ticket`, `titulo`, `estado`, `version_actual_id`).
- `GET /api/v1/requerimientos/{id}` → `RequirementResponse` (contenedor + versiones + colecciones + firmas + anexos).
- `PATCH /api/v1/requerimientos/{id}/versiones/{vid}` → `VersionResponse`.
- `POST|PATCH|DELETE /api/v1/requerimientos/{id}/versiones/{vid}/{coleccion}[/{itemId}]` y `PUT .../orden`.
- `GET /api/v1/catalogos/tipos-cambio` y `GET /api/v1/catalogos/cargos?rol=`.

Envelope de error: `{"error": {"code": string, "message": string, "details": object|null}}`.

Modelo de UI del wizard (estado en cliente):
- Recurso: `id`, `folio`, `ticket`, `estado`, `version_actual_id`.
- Versión de trabajo: cabecera (`titulo`, `tipo_cambio_id`, `sistema`, `version_documento`, `fecha_version`) y narrativa (`necesidad_actual`, `contexto_descripcion`, `contexto_manejo_errores`, `usuarios_permisos`, `requisitos_futuros_aplica`, `requisitos_futuros_texto`).
- Colecciones: objetivos, consideraciones, beneficios (con `tipo`), restricciones, volumetría, riesgos, requisitos futuros.
- Estado del wizard: paso actual, estado por paso, banderas de guardado y errores.

Cambio de backend acotado a esta spec:
- `RequirementSummary` incorpora `titulo` (tomado de la versión vigente); actualiza su `from_domain` y las pruebas; se documenta en `doc/technical/api.md`.

## Requisitos no funcionales aplicables
- Tipado completo en TypeScript; compilación de tipos y build de producción sin errores.
- Sin dependencias nuevas no justificadas (regla 6 de `AGENTS.md`).
- Separación: el frontend consume únicamente la API `/api/v1`; no conoce la persistencia.
- Fidelidad visual: tokens de `doc/ui/design/STITCH_DESIGN.md` ya reflejados en `frontend/src/index.css`; no duplicar valores en componentes.
- Respuestas y errores consistentes con el envelope único de la API.
- La aplicación funciona sin IA (`AI_PROVIDER=none`).
- Pruebas end-to-end con Playwright; mocking de la API mediante interceptación de rutas.
- El listado y el wizard deben ser usables en los breakpoints definidos en el sistema de diseño (móvil, tablet, escritorio).

## Decisiones tomadas
- **Sí:** wizard de pasos 1-12 funcionales y paso 13 como shell de revisión.
- **Sí:** una sola spec para el wizard de captura y el listado.
- **Sí:** navegación lista/wizard por estado interno, sin router.
- **Sí:** estado y llamadas a la API con hooks + `Context`/`useReducer` + `fetch`, sin librerías de terceros.
- **Sí:** autosave con debounce más acción explícita "Guardar borrador"; colecciones persisten por operación.
- **Sí:** sidebar completo con placeholders para las entradas no operativas.
- **Sí:** incluir el listado de requerimientos con filtros y paginación.
- **Sí:** paso 12 como captura de UI sin persistir firmas (ADR-007).
- **Sí:** paso 6 acotado a texto; anexos/imágenes diferidos a la spec de storage (ADR-006).
- **Sí:** agregar `titulo` a `RequirementSummary` (cambio de backend acotado) para el listado.
- **Sí:** pruebas de UI solo con Playwright e2e, sin runner de componentes.
- **No:** "Descripción del cambio" del control de versiones (requiere campo nuevo en `REQ_VERSION`); deuda registrada.
- **No:** vista previa y generación documental (SPEC-007).
- **No:** validación integral/reglas condicionales (SPEC-005).
- **No:** IA (SPEC-006) y auth/roles (SPEC-008).
- **No:** CRUD de catálogos y firma electrónica.

## Riesgos identificados

| Riesgo | Mitigacion |
|---|---|
| Autosave con debounce y operaciones de colección pueden provocar escrituras concurrentes sobre la misma versión | Serializar las escrituras por requerimiento en el cliente y recargar la versión tras cada operación; documentar el límite (DT-03 de SPEC-002) |
| El paso 12 captura firmantes que no se persisten (ADR-007) y puede confundir al usuario | Indicar en la UI que la captura no se registra en `BORRADOR`; registrar como deuda |
| Ausencia de "Descripción del cambio" en el modelo | Documentar la brecha; no capturar el campo; evaluar campo nuevo en una spec de backend |
| Anexos imposibles de subir sin storage | Diferir el bloque de anexos a la spec de storage; el paso 6 no muestra carga de imágenes |
| Los contratos de la API cambian y rompen la UI | Cliente HTTP tipado con DTOs espejo y pruebas e2e con mocking; alinear con `doc/technical/api.md` y `/openapi.json` |
| Diferencias entre el proxy de desarrollo (Vite) y producción (Nginx) | Configurar `/api` en ambos entornos y cubrir con prueba de humo |

## Preguntas resueltas (2026-10-15)
- **Alcance del wizard:** pasos 1-12 funcionales y paso 13 shell.
- **Tamaño:** una sola SPEC-004.
- **Navegación:** estado interno, sin router.
- **Estado/datos:** sin dependencias nuevas (hooks + Context/useReducer + fetch).
- **Guardado:** autosave con debounce + botón "Guardar borrador".
- **Listado:** incluido, con filtros y paginación.
- **Paso 12:** captura de UI sin persistir firmas.
- **Sidebar:** completo con placeholders.
- **Descripción del cambio:** fuera de alcance (deuda de backend).
- **Anexos (paso 6):** diferidos; solo texto.
- **Título en listado:** se agrega `titulo` a `RequirementSummary`.
- **Pruebas:** solo Playwright e2e.

## Preguntas abiertas
Ninguna.
