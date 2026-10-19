# SPEC-005 - Validación integral y máquina de estados

- Estado: Aprobado
- Fecha: 2026-10-16
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/007-firmas-segun-estado.md`, `doc/development/convenciones.md`, `doc/technical/api.md`
- Depende de: SPEC-001-fundaciones, SPEC-002-modelo-dominio-requerimiento, SPEC-003-api-requerimientos, SPEC-004-wizard-captura

## Contexto y objetivo

SPEC-004 deja el wizard funcional con guardado en borrador y navegación por pasos. Sin embargo, la especificación funcional exige una validación integral en el backend antes de permitir transiciones de estado, así como una máquina de estados explícita con sus reglas.

El objetivo de esta SPEC es añadir:
- Validación integral de una versión de requerimiento (secciones, colecciones, reglas condicionales, consistencia) accesible vía API (dry-run).
- Máquina de estados con transiciones válidas y sus precondiciones, respetando ADR-005 y ADR-007.
- Endpoints para validar y para transicionar estado, con respuestas claras por sección/campo.

## Alcance

### Incluye
- Dominio: estados, transiciones válidas, reglas de validación integral por sección del machote (pasos 1-12 relevantes para completitud).
- Application: casos de uso `ValidateRequirementVersion` y `TransitionRequirementState` con puertos.
- API: `POST /requerimientos/{id}/versiones/{v}/validar` (dry-run) y `POST /requerimientos/{id}/transicionar`.
- Esquemas: `ValidationResult`, `ValidationError`, `StateTransitionRequest`, `StateTransitionResponse`.
- Regla condicional para paso 9: si `requisitos_futuros_aplica = false`, no se exigen `requisitos_futuros_texto` ni elementos en `requisitos_futuros`; si `true`, se exige al menos uno (texto o lista activa).
- Coherencia con firmas según ADR-005/ADR-007 (solo `APROBADO`/`GENERADO` permiten registrar firmas; transiciones no las generan).
- Pruebas unitarias de dominio y de API. Calidad: `ruff`, `mypy --strict`, `pytest`.

### No incluye
- Generación DOCX/PDF (SPEC-007).
- Vista previa (SPEC-006).
- Autorización por roles más allá de lo necesario para validar las precondiciones documentadas (SPEC-008).
- Firma electrónica o flujo automático de aprobación.
- Migraciones de BD distintas a las necesarias para soportar estado/transiciones si ya existen (se reutilizan columnas/estado existentes cuando aplique).

## Requisitos funcionales

RF-01 La aplicación debe definir explícitamente los estados: `BORRADOR`, `EN_REVISION`, `VALIDADO`, `APROBADO`, `GENERADO`, `CANCELADO`.
RF-02 Debe existir un validador integral backend que verifique: datos generales (paso 1), necesidad actual (paso 2), colecciones con al menos un elemento activo (objetivos, consideraciones, beneficios, restricciones, volumetría, riesgos) según corresponda, contexto (paso 6), usuarios/permisos (paso 7), requisitos futuros con regla condicional (paso 9), control documental mínimo según transición (paso 12) y consistencia entre campos.
RF-03 `requisitos_futuros_aplica = false` → no se exige `requisitos_futuros_texto` ni `requisitos_futuros` activos.
RF-04 `requisitos_futuros_aplica = true` → se exige al menos un activo en `requisitos_futuros` o texto no vacío en `requisitos_futuros_texto`.
RF-05 Exponer `POST /requerimientos/{id}/versiones/{v}/validar` con respuesta `ValidationResult` (valido boolean, errores[], advertencias[]). Debe incluir `path` (campo/sección), `codigo`, `mensaje`, `seccion`.
RF-06 Exponer `POST /requerimientos/{id}/transicionar` con body `{ a_estado, motivo?, actor_id? }` y respuesta `{ estado_anterior, estado_actual, transicion_valida }`.
RF-07 Las transiciones permitidas deben ser explícitas. Intento de transición no permitida → `400` con error estructurado.
RF-08 Respetar ADR-005/ADR-007: firmas solo en `APROBADO`/`GENERADO`; transiciones no crean firmas.
RF-09 Validación integral debe poder ejecutarse en `BORRADOR` (dry-run) sin cambiar estado.
RF-10 Errores de validación deben ser accionables (indicar sección + campo afectado).

## Criterios de aceptacion

CA-01 Dado un requerimiento en `BORRADOR` con campos obligatorios incompletos, al validar `/requerimientos/{id}/versiones/{v}/validar` retorna `valido=false` con errores por sección/campo.
CA-02 Dado un requerimiento completo según reglas, la validación retorna `valido=true` sin errores bloqueantes.
CA-03 Dado `requisitos_futuros_aplica=false`, no se reporta error aunque `requisitos_futuros_texto` vacío y sin elementos activos.
CA-04 Dado `requisitos_futuros_aplica=true` sin texto ni elementos activos, se reporta error en sección "Requisitos futuros".
CA-05 Al intentar transición no permitida (p.ej. `BORRADOR`→`APROBADO` sin pasar por los estados intermedios), retorna `400` y `transicion_valida=false`.
CA-06 Transición válida ejecuta cambio de estado y registra `estado_anterior/estado_actual`.
CA-07 `POST /requerimientos/{id}/transicionar` rechaza solicitudes con `a_estado` inválido → `400`.
CA-08 Firmas siguen restringidas a `APROBADO`/`GENERADO` (ADR-007) — comportamiento existente no se rompe.
CA-09 Validación no modifica estado (dry-run).
CA-10 Respuesta de validación incluye `path`, `codigo`, `mensaje`, `seccion` para cada error.

## Reglas de negocio y validaciones

- Estados: `BORRADOR`, `EN_REVISION`, `VALIDADO`, `APROBADO`, `GENERADO`, `CANCELADO`.
- Transiciones iniciales: `BORRADOR→EN_REVISION`, `EN_REVISION→VALIDADO`, `VALIDADO→APROBADO`, `APROBADO→GENERADO`. Retrocesos permitidos: `EN_REVISION→BORRADOR`, `VALIDADO→EN_REVISION` (coherente con SPEC-002 y el dominio existente). Cancelaciones: `BORRADOR→CANCELADO`, `EN_REVISION→CANCELADO`, `VALIDADO→CANCELADO`, `APROBADO→CANCELADO`. Cualquier otra transición es inválida.
- Validación integral verifica: header (folio/título/tipo_cambio/sistema/version_documento/fecha_version), necesidad_actual no vacío, colecciones activas >=1: objetivos, consideraciones, beneficios, restricciones, volumetría, riesgos. Contexto: `contexto_descripcion` no vacío. Usuarios/permisos: `usuarios_permisos` no vacío. Requisitos futuros: regla condicional RF-03/RF-04. Control documental: `signers.ELABORO.nombre` y `signers.AUTORIZO.nombre` no vacíos (coherente con wizard), exigido únicamente como precondición de la transición a `GENERADO`.
- ADR-005/007: firmas solo `APROBADO`/`GENERADO`. La máquina de estados no crea firmas.
- Validación es idempotente (dry-run). No escribe cambios salvo la transición explícita.

## Datos involucrados (a nivel funcional)

- `Requirement.estado` (enum/string).
- `ValidationError`: `{ path: string, codigo: string, mensaje: string, seccion: string }`
- `ValidationResult`: `{ valido: boolean, errores: ValidationError[], advertencias: ValidationError[] }`
- `StateTransitionRequest`: `{ a_estado: string, motivo?: string, actor_id?: number }`
- `StateTransitionResponse`: `{ estado_anterior: string, estado_actual: string, transicion_valida: boolean, errores?: ValidationError[] }`

## Requisitos no funcionales aplicables

- Arquitectura hexagonal: dominio puro (sin imports FastAPI/SQLAlchemy), application con puertos, infrastructure/adaptadores, api/routers.
- Tipado completo, `ruff check .`, `mypy --strict app`.
- Pruebas: pytest (unitarios + API). No añadir dependencias nuevas.
- Errores estructurados, mensajes en español, identificadores/códigos en inglés.
- Sin cambios de comportamiento de firmas fuera de lo ya definido (ADR-007).

## Preguntas abiertas

Ninguna. La información de ADR-005/007 y SPECs previas es suficiente para implementar esta especificación.
