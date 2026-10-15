# ADR-007 - Momento de registro de las firmas
- Estado: Aceptada
- Fecha: 2026-10-14
## Contexto
ADR-005 definio que `Elaboro` y `Reviso` se registran por version del requerimiento (para la tabla de Control de versiones del machote) y que `Autorizo` se registra solo en la version vigente, sin fijar en que estado del ciclo de vida pueden capturarse las firmas. SPEC-003 (API de requerimientos) necesita una regla explicita para exponer el endpoint de firmas.

Durante la definicion de SPEC-003 se decidio restringir la captura de firmas al momento en que el documento ya es final, para que el bloque de Firmas del machote corresponda al archivo final y no a versiones de trabajo intermedias.
## Decision
- Las firmas `Elaboro`, `Reviso` y `Autorizo` solo se registran cuando el estado del requerimiento es `APROBADO` o `GENERADO`.
- Las firmas se asocian a la version vigente del requerimiento; un intento sobre una version no vigente o en un estado distinto devuelve `409` (`signature_not_allowed`).
- `Autorizo` se sigue enrutando por `Requirement.authorize` (solo version vigente).
- Las firmas siguen siendo registros de texto (sin firma electronica), conforme a ADR-005.
## Consecuencias
- Este ADR reemplaza, para el aspecto de *cuando* se capturan, la politica de ADR-005; el resto de ADR-005 (catalogo de cargos por rol, firma no electronica) permanece vigente.
- La tabla *Control de versiones* del machote solo tendra firmantes `Elaboro`/`Reviso` en la version final; el ajuste de renderizado se aborda en SPEC-007.
- La maquina de estados no cambia: las firmas no disparan transiciones; el cambio de estado sigue siendo manual.
## Alternativas consideradas
- Mantener `Elaboro`/`Reviso` capturables en cualquier estado y version (politica original de ADR-005).
- Permitir firmar unicamente en `BORRADOR` mientras el documento es editable.
- Exigir firma electronica o flujo de aprobacion automatico (fuera del MVP).
