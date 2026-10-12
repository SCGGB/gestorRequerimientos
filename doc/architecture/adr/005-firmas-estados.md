# ADR-005 - Politica de firmas, estados y transiciones
- Estado: Aceptada
- Fecha: 2026-10-12
## Contexto
La spec funcional definia los estados `BORRADOR -> EN_REVISION -> VALIDADO -> APROBADO -> GENERADO` (con `CANCELADO` como alterno), pero dejaba sin definir la politica de aprobacion y firmas. El machote presenta una tabla de Control de versiones (con Revisó y Elaboró por version) y una tabla de Firmas (Elaboró, Revisó, Autorizó).
## Decision
- Las firmas `Elaboro` y `Reviso` se registran por version del requerimiento y quedan reflejadas en la tabla de Control de versiones.
- La firma `Autorizo` se registra unicamente en el bloque de firmas de la version vigente.
- El cargo de cada firma proviene de un catalogo por rol con valor por defecto editable en el requerimiento.
- Las transiciones de estado son manuales y las ejecuta un usuario con el rol autorizado. El MVP no exige firma electronica ni flujo de aprobacion automatico.
## Consecuencias
Modelo de firmas simple y consistente con el machote; se evita introducir firma electronica y proveedores de identidad reforzada en el MVP. Una politica de aprobacion con firma electronica podria requerir un ADR posterior.
## Alternativas consideradas
Firma electronica obligatoria por aprobacion; cierre global unico de firmas sin control por version.
