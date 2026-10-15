# SPEC-003 - Casos de uso y API de requerimientos

- Estado: Approved
- Fecha: 2026-10-14
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/documents/mapeo-machote.md`, `doc/ui/wizard-flow.md`, `doc/development/convenciones.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/003-autenticacion.md`, `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/006-almacenamiento-objetos-dev.md`, `doc/architecture/adr/007-firmas-segun-estado.md`
- Depende de: SPEC-001, SPEC-002

## Contexto y objetivo
Exponer el modelo de dominio del requerimiento (ya persistido en Oracle por SPEC-002) mediante casos de uso y endpoints HTTP `/api/v1`, de modo que el wizard (SPEC-004) y el resto del sistema operen sobre la base de datos como fuente de verdad sin acceder directamente a la persistencia.

## Alcance

### Incluye
- Casos de uso (capa `application`) para crear, consultar, listar, editar el borrador, versionar, cambiar de estado, firmar y gestionar anexos de un requerimiento.
- Endpoints HTTP `/api/v1` para requerimientos, versiones, colecciones, firmas, anexos, estado y catálogos de lectura.
- Convención de API: prefijo `/api/v1`, envelope de error propio y mapeo de errores de dominio a códigos HTTP.
- Listado filtrado y paginado (por estado y folio) mediante extensión del puerto `RequirementRepository`.
- Documento de contrato de API en `doc/technical/api.md` apoyado en el OpenAPI generado por FastAPI.
- Pruebas de casos de uso y de API (patrón `tests/api/test_health.py`), más la verificación de calidad (`ruff`, `mypy --strict`, `pytest`).

### No incluye
- Pantallas, wizard y estados de UI (SPEC-004); esta spec solo publica la API que el frontend consumirá.
- Reglas de negocio ejecutables y validación integral (SPEC-005): aquí solo se valida la forma (tipos, longitudes, esquema Pydantic) y las invariantes ya existentes en el dominio.
- Asistencia IA (SPEC-006).
- Generación DOCX/PDF y vista previa documental (SPEC-007); `POST /estado` a `GENERADO` solo ejecuta la transición, no genera archivos.
- Autenticación JWT, usuarios, roles y auditoría funcional (SPEC-008); los endpoints quedan sin enforcement de rol, dejando el punto de extensión `AuthProvider`.
- Subida de binarios de anexos y adaptador de `StoragePort` (ADR-006): los anexos se registran solo como metadato con `storage_key` provisto por el cliente.
- Firma electrónica (ADR-005): las firmas son registros de texto, sin mecanismo criptográfico.

## Requisitos funcionales
- RF-01. El sistema expone `POST /api/v1/requerimientos` para crear un requerimiento con folio (entero único capturado por el cliente) y la cabecera de su versión 1 (`titulo`, `tipo_cambio_id`, `sistema`, `version_documento`, `fecha_version`); el estado inicial es `BORRADOR` y la versión 1 es la de trabajo.
- RF-02. El sistema expone `GET /api/v1/requerimientos` con filtros opcionales `estado` y `folio` y paginación `page`/`size`, devolviendo el envelope `{items, total, page, size}`.
- RF-03. El sistema expone `GET /api/v1/requerimientos/{id}` con el agregado completo (contenedor, versiones, colecciones, firmas y anexos).
- RF-04. El sistema expone `GET /api/v1/requerimientos/{id}/versiones` y `GET /api/v1/requerimientos/{id}/versiones/{vid}` para el histórico y el detalle de una versión.
- RF-05. El sistema expone `PATCH /api/v1/requerimientos/{id}/versiones/{vid}` para actualizar los campos de cabecera y narrativos de una versión, permitido únicamente sobre la versión de trabajo y cuando el estado es `BORRADOR`.
- RF-06. El sistema expone CRUD por colección (objetivos, consideraciones, beneficios, restricciones, volumetría, riesgos, requisitos futuros): `POST` para agregar, `PATCH` para editar contenido, `DELETE` para eliminar (soft-delete) y `PUT .../orden` para reordenar por lista de identificadores; los `Beneficio` distinguen `CUALITATIVO`/`CUANTITATIVO` con el discriminador `tipo`.
- RF-07. El sistema expone `POST .../versiones/{vid}/firmas` para registrar firmas. Las firmas (`ELABORO`, `REVISO`, `AUTORIZO`) solo se registran cuando el estado del requerimiento es `APROBADO` o `GENERADO` y quedan asociadas a la versión vigente; en cualquier otro estado o sobre una versión no vigente la API responde `409`. `AUTORIZO` se enruta por `Requirement.authorize`.
- RF-08. El sistema expone CRUD de anexos por versión como metadato (`nombre`, `tipo_mime`, `orden`, `leyenda`, `storage_key`); el binario no se guarda en Oracle ni se sube en esta spec.
- RF-09. El sistema expone `POST /api/v1/requerimientos/{id}/versiones` que congela la versión de trabajo y crea la sucesora por copy-on-write (solo elementos activos, preservando orden), recibiendo `version_documento`, `fecha_version` y `titulo` (con valor por defecto tomado de la versión vigente).
- RF-10. El sistema expone `POST /api/v1/requerimientos/{id}/estado` con `{"nuevo_estado": "..."}` que aplica las transiciones permitidas del dominio y rechaza las no permitidas.
- RF-11. El sistema expone `GET /api/v1/catalogos/tipos-cambio` y `GET /api/v1/catalogos/cargos?rol=` para consultar los catálogos sembrados en SPEC-002.
- RF-12. El sistema centraliza el manejo de errores: un `exception_handler` global mapea los errores de dominio a códigos HTTP y devuelve el envelope `{"error": {"code", "message", "details"}}`.
- RF-13. Los casos de uso residen en `application` y los routers solo orquestan validación de entrada, invocación del caso de uso y serialización; no hay lógica de negocio en los routers.
- RF-14. El listado filtrado/paginado se implementa extendiendo el puerto `RequirementRepository` con una búsqueda paginada y su implementación en el adaptador SQLAlchemy (LIMIT/OFFSET + COUNT).
- RF-15. El contrato de la API queda documentado en `doc/technical/api.md`, describiendo prefijo, envelope de error, catálogo de endpoints, códigos de estado y la referencia a `/openapi.json`.
- RF-16. La aplicación arranca y sirve estos endpoints sin IA (`AI_PROVIDER=none`) y sin autenticación activa, dejando preparado el punto de extensión de `AuthProvider`.

## Criterios de aceptacion
- CA-01. Dado un folio válido y la cabecera de la versión 1, cuando se ejecuta `POST /api/v1/requerimientos`, entonces responde `201` con el recurso creado en estado `BORRADOR` y su versión 1 como versión de trabajo.
- CA-02. Dado un folio ya existente, cuando se intenta crear otro requerimiento con el mismo folio, entonces la API responde `409` con el envelope de error y `code` de conflicto de unicidad.
- CA-03. Dados varios requerimientos, cuando se ejecuta `GET /api/v1/requerimientos` con filtros `estado`/`folio` y `page`/`size`, entonces devuelve `200` con `{items, total, page, size}` acotado a los filtros y a la página solicitada.
- CA-04. Dado un requerimiento existente, cuando se ejecuta `GET /api/v1/requerimientos/{id}`, entonces devuelve `200` con el agregado completo (versiones, colecciones, firmas y anexos); con un `id` inexistente devuelve `404`.
- CA-05. Dado un requerimiento en `BORRADOR`, cuando se ejecuta `PATCH` sobre su versión de trabajo, entonces actualiza los campos y devuelve `200`; cuando el requerimiento no está en `BORRADOR` (o se intenta editar una versión congelada), entonces devuelve `409`.
- CA-06. Dada una colección, cuando se agrega, edita, elimina o reordena un elemento, entonces los cambios se reflejan al consultar el agregado; el `DELETE` marca el elemento como inactivo (no lo borra físicamente) y `PUT .../orden` renumera según la lista de ids.
- CA-07. Dado un requerimiento con beneficios, cuando se registran beneficios cualitativos y cuantitativos, entonces cada uno conserva su `tipo` y se recuperan en su colección correspondiente.
- CA-08. Dado un requerimiento en `APROBADO`, cuando se registra `ELABORO`, `REVISO` o `AUTORIZO` sobre su versión vigente, entonces cada firma queda asociada a esa versión y devuelve `201`; cuando el estado no es `APROBADO`/`GENERADO` o la versión no es la vigente, entonces devuelve `409`.
- CA-09. Dado un requerimiento con elementos activos e inactivos, cuando se ejecuta `POST /api/v1/requerimientos/{id}/versiones`, entonces se congela la versión de trabajo, se crea la sucesora con solo los elementos activos conservando el orden, y la nueva versión queda como versión de trabajo.
- CA-10. Dado un requerimiento en un estado dado, cuando se solicita una transición permitida en `POST /api/v1/requerimientos/{id}/estado`, entonces el estado cambia; cuando se solicita una transición no permitida, entonces devuelve `409` sin modificar el estado.
- CA-11. Cuando se ejecuta `GET /api/v1/catalogos/tipos-cambio` y `GET /api/v1/catalogos/cargos?rol=`, entonces devuelve `200` con los catálogos sembrados (seis tipos de cambio y cargos por rol).
- CA-12. Dado el árbol del repositorio, cuando se ejecutan `ruff check .`, `mypy --strict app` y `pytest`, entonces no hay errores; y `GET /openapi.json` expone todos los endpoints de esta spec.

## Reglas de negocio y validaciones
- Prefijo `/api/v1` para routers de negocio; `/health` y `/version` permanecen en la raíz.
- `folio`: entero positivo capturado por el cliente; único. Duplicado → `409`; valor inválido (≤ 0 o mal formado) → `422`. El ticket mostrado es `T#` + folio.
- La edición (`PATCH` y CRUD de colecciones/firmas de borrador) solo aplica a la versión de trabajo y con estado `BORRADOR`; en cualquier otro estado o versión congelada → `409`.
- Las transiciones de estado siguen el mapa de dominio: `BORRADOR → EN_REVISION|CANCELADO`; `EN_REVISION → VALIDADO|BORRADOR|CANCELADO`; `VALIDADO → APROBADO|EN_REVISION|CANCELADO`; `APROBADO → GENERADO|CANCELADO`; `GENERADO` y `CANCELADO` son terminales. Transición no permitida → `409`.
- Firmas: solo se registran con estado `APROBADO`/`GENERADO` y sobre la versión vigente. Estado distinto u otra versión → `409` (`signature_not_allowed`). `AUTORIZO` se enruta por `Requirement.authorize`.
- Como máximo una versión no congelada por requerimiento; `POST /versiones` con una versión ya congelada o sin versión de trabajo → `409`.
- Colecciones: elementos independientes con `id`, `orden`, `contenido` y `activo`; nunca un bloque de texto. `DELETE` es soft-delete (`activo='N'`).
- Anexos: solo metadato; el binario no se guarda en Oracle y no se sube en esta spec.
- Validación estructural (Pydantic): tipos, longitudes y campos requeridos → `422`. Las reglas de negocio condicionales y la validación integral quedan para SPEC-005.
- Sin enforcement de rol en esta spec (SPEC-008 introduce auth); se deja el punto de extensión.
- Los casos de uso viven en `application`; los routers no contienen lógica de negocio.
- El envelope de error es siempre `{"error": {"code", "message", "details"}}` con un `code` estable por tipo de error.

## Datos involucrados (a nivel funcional)

Convención de recursos (todos bajo `/api/v1`):

Requerimiento y versiones:
- `POST /requerimientos` → crea folio + versión 1.
- `GET /requerimientos?estado=&folio=&page=&size=` → listado paginado.
- `GET /requerimientos/{id}` → agregado.
- `GET /requerimientos/{id}/versiones` y `/{vid}` → histórico y detalle.
- `PATCH /requerimientos/{id}/versiones/{vid}` → cabecera/narrativa de la versión.
- `POST /requerimientos/{id}/versiones` → congelar y avanzar (copy-on-write).

Colecciones (`{c}` ∈ `objetivos`, `consideraciones`, `beneficios`, `restricciones`, `volumetria`, `riesgos`, `requisitos-futuros`):
- `POST /requerimientos/{id}/versiones/{vid}/{c}`
- `PATCH /requerimientos/{id}/versiones/{vid}/{c}/{itemId}`
- `DELETE /requerimientos/{id}/versiones/{vid}/{c}/{itemId}` (soft-delete)
- `PUT /requerimientos/{id}/versiones/{vid}/{c}/orden` (lista de ids)

Firmas y anexos:
- `POST /requerimientos/{id}/versiones/{vid}/firmas`
- `POST|PATCH|DELETE /requerimientos/{id}/versiones/{vid}/anexos[/{aid}]`
- `PUT /requerimientos/{id}/versiones/{vid}/anexos/orden`

Estado y catálogos:
- `POST /requerimientos/{id}/estado` (body `{"nuevo_estado": "..."}`)
- `GET /catalogos/tipos-cambio`
- `GET /catalogos/cargos?rol=`

Envelope de error:
- `{"error": {"code": string, "message": string, "details": object|null}}`

Mapeo de errores de dominio a HTTP:
- `InvalidStateTransitionError`, `AuthorizationNotOnCurrentVersionError`, `MultipleWorkingVersionsError`, `SignatureNotAllowedError`, folio duplicado, edición fuera de `BORRADOR`/versión congelada → `409`.
- Recurso inexistente (`RequirementNotFound` o equivalente en el caso de uso) → `404`.
- `InvalidFolioError` y validación estructural de Pydantic → `422`.

## Requisitos no funcionales aplicables
- Tipado completo con `ruff` y `mypy --strict` sin errores.
- Separación hexagonal estricta: sin lógica de negocio en routers; casos de uso en `application`; persistencia solo vía puertos.
- Reutilizar el dominio y los adaptadores de SPEC-002 sin duplicar reglas.
- Los identificadores de los sub-recursos (colecciones, firmas y anexos) son estables entre escrituras.
- Respuestas y errores consistentes (envelope único) y códigos HTTP predecibles.
- Endpoints documentados en OpenAPI (`/openapi.json`) y en `doc/technical/api.md`.
- La aplicación funciona sin IA (`AI_PROVIDER=none`).
- Pruebas de casos de uso sin base de datos y de API con el cliente de FastAPI; integración donde aplique.

## Decisiones tomadas
- **Sí:** prefijo `/api/v1` para negocio; `/health` y `/version` sin tocar.
- **Sí:** envelope de error propio con `code` estable por tipo de error.
- **Sí:** ciclo de vida completo por API (crear, consultar, listar, editar borrador, versionar, cambiar estado, firmar, anexos, catálogos) sin UI.
- **Sí:** creación con cabecera de la versión 1; nueva versión recibe su propia cabecera con default de la vigente.
- **Sí:** congelado explícito vía `POST /versiones`; el cambio de estado es independiente.
- **Sí:** transición de estado con un endpoint único y estado destino.
- **Sí:** firmas con un endpoint único, registrables solo en estado `APROBADO`/`GENERADO` y sobre la versión vigente (ADR-007); `AUTORIZO` enrutado por `Requirement.authorize`.
- **Sí:** edición solo en `BORRADOR` y sobre la versión de trabajo; en otro caso `409`.
- **Sí:** soft-delete y reorden por lista de ids en colecciones.
- **Sí:** ids de sub-recursos estables entre escrituras (upsert por fila en el adaptador, sin migración).
- **Sí:** listado con filtros `estado`/`folio` y paginación; se extiende el puerto `RequirementRepository`.
- **Sí:** anexos solo como metadato; subida de binario y `StoragePort` en otra spec.
- **No:** enforcement de rol y JWT (SPEC-008); se deja punto de extensión.
- **No:** validación de negocio condicional e integral (SPEC-005).
- **No:** generación documental al pasar a `GENERADO` (SPEC-007).

## Riesgos identificados

| Riesgo | Mitigacion |
|---|---|
| Edición concurrente del borrador (DT-03 de SPEC-002: la versión única no congelada solo se valida en dominio) | Documentar el límite; mantener la validación de dominio y evaluar bloqueo optimista en una spec de endurecimiento |
| `authorize` acepta `version_id=None` (H-07/DT-06 de SPEC-002) | Validar en el caso de uso que la versión exista y sea la vigente antes de firmar; prueba de API dedicada |
| Extender el puerto `RequirementRepository` rompe adaptadores existentes | Añadir el método de búsqueda manteniendo la compatibilidad de `list()`; cubrir con pruebas de integración |
| Mapeo de errores inconsistente entre endpoints | Un único `exception_handler` global y `code` estable por error; prueba de contrato del envelope |
| Ambigüedad entre acción y estado al exponer transiciones | Endpoint único con estado destino y rechazo explícito de transiciones no permitidas |
| Convención de nombres de rutas de colecciones distinta a las columnas de dominio | Mapeo explícito de nombres de recurso en el router; documentado en `doc/technical/api.md` |
| Firmas solo en estado final (ADR-007): la tabla *Control de versiones* del machote solo tendría firmantes en la versión final | ADR-007 documenta la política; el ajuste de render se aborda en SPEC-007 |
| `save` reescribía todos los hijos (ids no estables, auditoría reiniciada) | Upsert por fila en el adaptador: `UPDATE` si hay `id`, `INSERT` si no, borrar solo ausentes; reorden en dos fases por el UQ `(VERSION_ID, ORDEN)`; prueba de integración que verifica ids estables |

## Preguntas resueltas (2026-10-14)
- **Alcance:** ciclo de vida completo por API, sin UI.
- **Auth/roles:** sin enforcement; punto de extensión `AuthProvider` para SPEC-008.
- **Validación:** solo estructural; reglas de negocio a SPEC-005.
- **Convención:** `/api/v1` + envelope de error propio; OpenAPI auto + `doc/technical/api.md`.
- **Borrador/concurrencia:** sub-recursos + `PATCH`; la concurrencia fuerte queda como deuda registrada.
- **Versionado:** congelado explícito por endpoint.
- **Estado:** endpoint único con estado destino.
- **Firmas:** solo en estado `APROBADO`/`GENERADO` y sobre la versión vigente (ADR-007).
- **Ids de sub-recursos:** estables entre escrituras (upsert por fila en el adaptador).
- **Anexos:** solo metadato.
- **Colecciones:** soft-delete + reorden por lista.
- **Listado:** filtros estado/folio + paginación, extendiendo el puerto.

## Que **no** esta en esta spec
- Wizard, pantallas y estados de UI.
- Reglas de negocio ejecutables y validación integral.
- IA y sugerencias.
- Generación DOCX/PDF y vista previa documental.
- Usuarios, roles, JWT y auditoría funcional.
- Subida de binarios de anexos y adaptador de storage.
- Firma electrónica.

Cada uno de estos temas, si se aborda, va en su propia spec.
