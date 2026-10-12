# Flujo del wizard de captura

- Fuente funcional: `doc/product/01_SPEC_FUNCIONAL.md`.
- Estructura del documento: `templates/machote_requerimiento.docx` y `doc/documents/mapeo-machote.md`.
- Referencia visual: `doc/ui/design/STITCH_DESIGN.md`, `doc/ui/screens/` y `doc/ui/stitch-reference/` (solo estilo y estados).

El wizard sigue las secciones del machote institucional. No incorpora secciones ajenas al documento final.

## Pasos

| Paso | Pantalla | Contenido |
|---|---|---|
| 1 | Datos generales | Ticket (prefijo `T#` fijo + numero), titulo, tipo de cambio, sistema, version documental, fecha de version |
| 2 | Necesidad actual | Texto narrativo |
| 3 | Objetivos generales | Coleccion ordenada |
| 4 | Consideraciones | Coleccion ordenada |
| 5 | Beneficios esperados | Dos colecciones independientes: cualitativos y cuantitativos |
| 6 | Diagramas contextuales | Descripcion, manejo de errores (opcional) y anexos (imagenes) |
| 7 | Usuarios y permisos | Texto narrativo |
| 8 | Restricciones | Coleccion ordenada |
| 9 | Requisitos futuros | `No aplica` o texto/lista |
| 10 | Volumetria y rendimiento | Coleccion ordenada |
| 11 | Riesgos iniciales | Coleccion ordenada |
| 12 | Control documental | Elaboro, Reviso, Autorizo (nombre + cargo) y descripcion de cambio |
| 13 | Revision | Validacion integral, vista previa y generacion documental |

## Navegacion y estado de paso

- Cada paso expone: paso anterior, guardar borrador y siguiente.
- El boton "siguiente" se bloquea cuando el paso no cumple sus obligatorios (por ejemplo, al menos 1 objetivo general). El bloqueo explica el motivo.
- Estado visual del paso: `pendiente`, `activo`, `completado` o `error` (validacion no resuelta).

## Comportamiento de colecciones (pasos 3, 4, 5, 8, 10, 11)

- Cada elemento conserva id, orden, contenido y estado activo/eliminado.
- Operaciones: agregar, editar, eliminar y reordenar.
- Patron de estados de UI por coleccion: `empty`, `with-data`, `editing`, `validation-error`, `ai-suggestion`.
- Ver ejemplo de este patron en `doc/ui/screens/objetivos/`.

## Asistencia IA (opcional)

- Disponible por campo habilitado para IA; nunca sustituye contenido de forma automatica.
- Toda propuesta se presenta y requiere aceptacion explicita del usuario.
- La aplicacion opera sin IA (`AI_PROVIDER=none`).
