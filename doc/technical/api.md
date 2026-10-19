# API - requerimientos, validación y transiciones (SPEC-003 / SPEC-005)

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
| PATCH | `/api/v1/requerimientos/{id}/versiones/{vid}` | Editar cabecera/narrativa (solo versión de trabajo en BORRADOR) | 200 `VersionResponse` |
| POST | `/api/v1/requerimientos/{id}/versiones` | Congelar versión de trabajo y crear sucesora (copy-on-write) | 201 `RequirementResponse` |
| POST | `/api/v1/requerimientos/{id}/versiones/{vid}/validar` | Validación integral de la versión (dry-run, no persiste) | 200 `ValidationResultResponse` |
| POST | `/api/v1/requerimientos/{id}/transicionar` | Transición de estado con validación integral previa (SPEC-005) | 200 `StateTransitionResponse` |
| POST | `/api/v1/requerimientos/{id}/estado` | Cambiar estado sin validación integral (legacy, ver nota) | 200 `RequirementResponse` |

#### Validación y transición (SPEC-005)

- `POST /requerimientos/{id}/versiones/{vid}/validar` es **dry-run**: no modifica estado ni contenido. Devuelve
  `200` con `valido=false` y la lista de errores si la versión no cumple (no es un error HTTP). Body opcional
  `{ "a_estado": "GENERADO" }` para evaluar además las precondiciones de esa transición.
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

- Entrada: `RequirementCreate`, `VersionUpdate`, `NewVersionRequest`, `StatusChangeRequest`, `SignatureCreate`, `CollectionItemCreate`, `BenefitCreate`, `CollectionItemUpdate`, `ReorderRequest`, `AttachmentCreate`, `AttachmentUpdate`, `ValidationRequest`, `StateTransitionRequest`.
- Salida: `RequirementResponse`, `RequirementSummary`, `RequirementPage`, `VersionResponse`, `CollectionItemResponse`, `BenefitResponse`, `SignatureResponse`, `AttachmentResponse`, `ChangeTypeResponse`, `PositionResponse`, `ValidationErrorSchema`, `ValidationResultResponse`, `StateTransitionResponse`.

`RequirementSummary` (item del listado paginado) incluye `id`, `folio`, `ticket` (`T#` + folio), `titulo` (título de la versión vigente; cadena vacía si no hubiera versión), `estado` y `version_actual_id`.

## Referencia OpenAPI

La especificación OpenAPI está disponible en `/openapi.json`. El contrato de errores y todos los endpoints arriba listados se corresponden con lo expuesto allí.
