# API - requerimientos, validación y transiciones (SPEC-003 / SPEC-005 / SPEC-006 / SPEC-007)

## Prefijo

Todos los endpoints de negocio van bajo `/api/v1`. `/health` y `/version` permanecen en la raíz.

## Envelope de errores

Todas las respuestas de error usan el siguiente formato:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": { } | null
  }
}
```

Códigos por tipo:

| Excepción | HTTP | code |
|---|---|---|
| `InvalidStateTransitionError` | 409 | `invalid_state_transition` |
| `AuthorizationNotOnCurrentVersionError` | 409 | `authorization_not_on_current_version` |
| `MultipleWorkingVersionsError` | 409 | `multiple_working_versions` |
| `RequirementNotEditableError` | 409 | `not_editable` |
| `SignatureNotAllowedError` | 409 | `signature_not_allowed` |
| `DuplicateFolioError` | 409 | `duplicate_folio` |
| `DataConflictError` | 409 | `data_conflict` |
| `DomainError` (resto) | 409 | `domain_error` |
| `RequirementNotFoundError` | 404 | `requirement_not_found` |
| `VersionNotFoundError` | 404 | `version_not_found` |
| `CollectionItemNotFoundError` | 404 | `collection_item_not_found` |
| `AttachmentNotFoundError` | 404 | `attachment_not_found` |
| `DocumentNotFoundError` | 404 | `document_not_found` |
| `DocumentGenerationNotAllowedError` | 409 | `document_generation_not_allowed` |
| `DocumentGenerationError` | 500 | `document_generation_failed` |
| Errores de validación Pydantic | 422 | `validation_error` |
| HTTP genérico | según código | `http_error` |

Los campos `details` pueden incluir el detalle de validación (`RequestValidationError.errors()`) cuando aplica.

## Catálogo de endpoints

### Requerimientos

| Método | Ruta | Descripción | Éxito |
|---|---|---|---|
| POST | `/api/v1/requerimientos` | Crear requerimiento con versión 1 en BORRADOR | 201 `RequirementResponse` |
| GET | `/api/v1/requerimientos?estado=&folio=&page=&size=` | Listado paginado y filtrado | 200 `RequirementPage` |
| GET | `/api/v1/requerimientos/{id}` | Detalle completo (contenedor + versiones + colecciones + firmas + anexos) | 200 `RequirementResponse` |
| GET | `/api/v1/requerimientos/{id}/versiones` | Historial de versiones (ordenado) | 200 `list[VersionResponse]` |
| GET | `/api/v1/requerimientos/{id}/versiones/{vid}` | Detalle de versión | 200 `VersionResponse` |
| GET | `/api/v1/requerimientos/{id}/versiones/{vid}/vista-previa` | Vista previa del documento (solo lectura, desde la versión persistida) | 200 `PreviewDocumentResponse` |
| PATCH | `/api/v1/requerimientos/{id}/versiones/{vid}` | Editar cabecera/narrativa (solo versión de trabajo en BORRADOR) | 200 `VersionResponse` |
| POST | `/api/v1/requerimientos/{id}/versiones` | Congelar versión de trabajo y crear sucesora (copy-on-write) | 201 `RequirementResponse` |
| POST | `/api/v1/requerimientos/{id}/versiones/{vid}/validar` | Validación integral de la versión (dry-run, no persiste) | 200 `ValidationResultResponse` |
| POST | `/api/v1/requerimientos/{id}/transicionar` | Transición de estado con validación integral previa (SPEC-005) | 200 `StateTransitionResponse` |
| POST | `/api/v1/requerimientos/{id}/estado` | Cambiar estado sin validación integral (legacy, ver nota) | 200 `RequirementResponse` |

#### Validación y transición (SPEC-005)

- `POST /requerimientos/{id}/versiones/{vid}/validar` es **dry-run**: no modifica estado ni contenido. Devuelve
  `200` con `valido=false` y la lista de errores si la versión no cumple (no es un error HTTP). Body opcional
  `{ "a_estado": "GENERADO" }` para evaluar además las precondiciones de esa transición. Si `a_estado` no es un
  estado válido, responde `200` con `valido=false` y el error `unknown_target_state` (no es `422`).
- `POST /requerimientos/{id}/transicionar` recibe `{ a_estado, motivo?, actor_id? }`. Si la transición no está
  permitida o falla la validación integral, responde **`400`** con el cuerpo `StateTransitionResponse`
  (`transicion_valida=false` y `errores[]`); en éxito responde `200` con el mismo esquema. Este `400` **no**
  usa el envelope global, porque el contrato exige simultáneamente el código `400`, `transicion_valida=false`
  y el detalle por sección/campo.
- Códigos dentro de `errores[]`: `unknown_target_state`, `invalid_transition`, `required_field`,
  `min_active_items`, `future_requirements_missing`, `signatures_missing`.
- El control documental (`signers.ELABORO.nombre` y `signers.AUTORIZO.nombre`) se exige solo como
  precondición de `APROBADO→GENERADO`; el dry-run base no exige firmas.
- `motivo` y `actor_id` se aceptan y se registran en log, pero **no se persisten** (no existe historial de
  transiciones; deuda documentada para una spec de auditoría futura).
- No hay cambios de modelo Oracle ni migraciones: el estado ya vive en `REQ_REQUERIMIENTO.ESTADO`.

`POST /requerimientos/{id}/estado` se conserva como **alias legacy** con su contrato original; mantiene el
`409 invalid_state_transition` del envelope global. Para flujos nuevos usar `/transicionar`.

#### Vista previa (SPEC-006)

- `GET /requerimientos/{id}/versiones/{vid}/vista-previa` devuelve `200 PreviewDocumentResponse` compuesto
  **desde la versión persistida** (fuente de verdad). Es una operación de **solo lectura**: no persiste cambios,
  no crea firmas ni transiciona estados.
- Contrato: encabezado (`folio`, `ticket` = `T#` + folio, `titulo`, `version_documento`, `fecha_version` en
  `dd-mm-aaaa`) y `secciones[]` con `codigo`, `numero` (numeración del machote: Necesidad Actual = 1 … Riesgos
  = 10, incluida la contenedora `4` Beneficios Esperados y sus subsecciones `4.1`/`4.2`) y `bloques[]`.
- `PreviewBlock`: `tipo` (`parrafo` | `lista` | `no_aplica`) con `texto` y/o `items`. El backend decide el tipo y
  normaliza el contenido; el renderizador no aplica reglas de negocio. Colecciones: solo elementos activos
  ordenados por `orden`; colección vacía conserva el título y devuelve "No aplica". Requisitos futuros:
  `requisitos_futuros_aplica=false` → "No Aplica."; `true` → texto y/o lista de activos.
- `control_versiones[]` lista todas las versiones del requerimiento (versión, fecha, `descripcion_cambio`,
  `reviso`, `elaboro`). La "descripción del cambio" no existe en el modelo y se devuelve `null` (la UI muestra
  "—").
- `firmas` (elaboró/revisó/autorizó) de la versión consultada, con `nombre` y `cargo`, o `null` por rol cuando
  no existen (ADR-007). La vista previa solo las representa; no las captura ni las modifica.
- Este mismo `PreviewDocument` es el contrato neutral que reutiliza la generación DOCX/PDF (SPEC-007), para
  mantener consistentes vista previa, DOCX y PDF. No hay cambios de modelo Oracle ni migraciones.

### Documentos generados (SPEC-007)

| Método | Ruta | Descripción | Éxito |
|---|---|---|---|
| POST | `/api/v1/requerimientos/{id}/documentos` | Genera DOCX y PDF de la versión vigente (o `version_id` opcional en el body) y registra ambos | 201 `list[GeneratedDocumentResponse]` |
| GET | `/api/v1/requerimientos/{id}/documentos` | Histórico completo de documentos generados, sin binario | 200 `list[GeneratedDocumentResponse]` |
| GET | `/api/v1/requerimientos/{id}/documentos/{did}/descarga` | Descarga el binario del documento | 200 binario |

- La generación es **síncrona** y usa como única entrada el `PreviewDocument` de SPEC-006 compuesto desde la
  versión persistida: vista previa, DOCX y PDF comparten contenido y versión (RF-01, RF-09).
- Solo se permite cuando el estado y las firmas lo habilitan (ADR-005/ADR-007): estado `APROBADO` (o `GENERADO`
  para regenerar) y firmas requeridas. En caso contrario responde `409` con `invalid_state_transition` o
  `document_generation_not_allowed` (este último con `details` = motivos de validación) y **no registra
  documentos ni transiciona** (CA-10).
- Tras una generación exitosa el requerimiento pasa automáticamente a `GENERADO` (RF-12, CA-11).
- Cada documento (DOCX y PDF) se registra como fila independiente de `REQ_DOCUMENTO` en Oracle, con el binario
  persistido como **BLOB** (no hay rutas físicas ni object store). Una nueva generación agrega filas y no
  sobrescribe las anteriores (RF-13, CA-12).
- La descarga devuelve `Content-Disposition: attachment; filename="T#<folio>-v<version>.<ext>"` (por ejemplo
  `T#1234-v3.docx`) y el `media_type` según el formato (RF-19, CA-16).
- Body opcional del `POST`: `{ "version_id": 123 }`; si se omite, se usa la versión vigente del requerimiento.
- Errores: `404 requirement_not_found` / `version_not_found` / `document_not_found` (documento inexistente o
  ajeno al requerimiento); `409` transición/estado o firmas no permitidas; `422 validation_error` (body
  inválido); `500 document_generation_failed` (fallo de render o conversión, con mensaje en español y sin
  registrar documentos ni transicionar, RF-15).

### Colecciones

Recursos `{c}`: `objetivos`, `consideraciones`, `beneficios`, `restricciones`, `volumetria`, `riesgos`, `requisitos-futuros`. Mapa explícito recurso → `CollectionKind`.

| Método | Ruta | Descripción | Éxito |
|---|---|---|---|
| POST | `/api/v1/requerimientos/{id}/versiones/{vid}/{c}` | Agregar elemento (beneficios requieren `tipo` en esquema) | 201 `VersionResponse` |
| PATCH | `/api/v1/requerimientos/{id}/versiones/{vid}/{c}/{itemId}` | Editar contenido | 200 `VersionResponse` |
| DELETE | `/api/v1/requerimientos/{id}/versiones/{vid}/{c}/{itemId}` | Baja lógica | 204 |
| PUT | `/api/v1/requerimientos/{id}/versiones/{vid}/{c}/orden` | Reordenar por lista de ids | 200 `VersionResponse` |

### Firmas

| Método | Ruta | Descripción | Éxito |
|---|---|---|---|
| POST | `/api/v1/requerimientos/{id}/versiones/{vid}/firmas` | Registrar firma | 201 `SignatureResponse` |

#### Política de firmas (ADR-007)

Las firmas se registran **solo** en estados finales (`APROBADO`/`GENERADO`) y **únicamente sobre la versión vigente** del requerimiento. Intentar firmar fuera de esos estados o sobre una versión distinta a la vigente produce `409` con `code` `signature_not_allowed`.

### Anexos (metadatos)

Los anexos son registrados únicamente como metadato (`nombre`, `tipo_mime`, `orden`, `leyenda`, `storage_key`). No se sube binario en esta spec.

| Método | Ruta | Descripción | Éxito |
|---|---|---|---|
| POST | `/api/v1/requerimientos/{id}/versiones/{vid}/anexos` | Agregar metadato de anexo | 201 `AttachmentResponse` |
| PATCH | `/api/v1/requerimientos/{id}/versiones/{vid}/anexos/{aid}` | Actualizar metadato | 200 `AttachmentResponse` |
| DELETE | `/api/v1/requerimientos/{id}/versiones/{vid}/anexos/{aid}` | Baja lógica | 204 |
| PUT | `/api/v1/requerimientos/{id}/versiones/{vid}/anexos/orden` | Reordenar anexos por lista de ids | 200 `list[AttachmentResponse]` |

### Catálogos (lectura)

| Método | Ruta | Descripción | Éxito |
|---|---|---|---|
| GET | `/api/v1/catalogos/tipos-cambio` | Tipos de cambio activos | 200 `list[ChangeTypeResponse]` |
| GET | `/api/v1/catalogos/cargos?rol=` | Cargos activos, filtrados por `rol` si se informa | 200 `list[PositionResponse]` |

## Mapa de nombres de recursos de colecciones

| Nombre recurso API | `CollectionKind` |
|---|---|
| `objetivos` | `OBJETIVOS` |
| `consideraciones` | `CONSIDERACIONES` |
| `beneficios` | `BENEFICIOS` |
| `restricciones` | `RESTRICCIONES` |
| `volumetria` | `VOLUMETRIA` |
| `riesgos` | `RIESGOS` |
| `requisitos-futuros` | `REQUISITOS_FUTUROS` |

## Esquemas principales (resumen)

- Entrada: `RequirementCreate`, `VersionUpdate`, `NewVersionRequest`, `StatusChangeRequest`, `SignatureCreate`, `CollectionItemCreate`, `BenefitCreate`, `CollectionItemUpdate`, `ReorderRequest`, `AttachmentCreate`, `AttachmentUpdate`, `ValidationRequest`, `StateTransitionRequest`, `GenerateDocumentsRequest`.
- Salida: `RequirementResponse`, `RequirementSummary`, `RequirementPage`, `VersionResponse`, `CollectionItemResponse`, `BenefitResponse`, `SignatureResponse`, `AttachmentResponse`, `ChangeTypeResponse`, `PositionResponse`, `ValidationErrorSchema`, `ValidationResultResponse`, `StateTransitionResponse`, `PreviewDocumentResponse` (+ `PreviewSectionResponse`, `PreviewBlockResponse`, `PreviewVersionRowResponse`, `PreviewFirmasResponse`, `PreviewSignerResponse`), `GeneratedDocumentResponse`.

`GeneratedDocumentResponse` (metadatos, nunca el binario): `id`, `formato` (`DOCX` | `PDF`), `version_id`,
`plantilla_version`, `nombre_archivo`, `mime_type`, `tamano_bytes`, `generado_at` y `generado_by`.

`RequirementSummary` (item del listado paginado) incluye `id`, `folio`, `ticket` (`T#` + folio), `titulo` (título de la versión vigente; cadena vacía si no hubiera versión), `estado` y `version_actual_id`.

## Referencia OpenAPI

La especificación OpenAPI está disponible en `/openapi.json`. El contrato de errores y todos los endpoints arriba listados se corresponden con lo expuesto allí.
