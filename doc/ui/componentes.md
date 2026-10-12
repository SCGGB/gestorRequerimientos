# Componentes y estados de UI

Sistema de diseno y tokens: `doc/ui/design/STITCH_DESIGN.md` (paleta institucional, tipografia Inter / JetBrains Mono, grid de 12 columnas, elevacion y formas).

Referencias: `doc/ui/screens/` (capturas) y `doc/ui/stitch-reference/` (HTML). El HTML de Stitch es referencia visual, **no** codigo fuente del proyecto (AGENTS regla 5).

## Estructura de pantalla

- Barra lateral de navegacion (Requerimientos, Nuevo Requerimiento, Plantillas ERS/SRS, Repositorio Documental, Configuracion y Catalogos).
- Encabezado con busqueda, notificaciones y perfil de usuario.
- Shell del wizard: riel de pasos (izquierda) y area de trabajo (derecha).
- Barra inferior de acciones: paso anterior, guardar borrador, siguiente.

## Componentes

| Componente | Descripcion |
|---|---|
| Stepper vertical | Nodos conectados: completado, activo, pendiente, error |
| Campos de formulario | Inputs/selects/textarea con etiqueta y marcador de obligatorio |
| Mensajes de validacion | Debajo del campo; borde y texto de error con icono |
| Item de lista dinamica | Fila con asa de reorden, id, contenido y acciones en linea; boton "agregar" punteado |
| Badges de estado | `Borrador`, `En Revision`, `Validado`, `Generado` |
| Panel de asistente IA | Compara original vs propuesta con "Aceptar propuesta" / "Descartar" |
| Vista previa A4 | Pagina simulada con encabezado institucional, tablas y firmas |
| Bloque de anexos | Imagen centrada (ancho util 17.4 cm) con leyenda numerada |

## Estados de coleccion

Patron aplicable a pasos de coleccion, ejemplificado con Objetivos:

| Estado | Referencia | Descripcion |
|---|---|---|
| Empty | `screens/objetivos/empty.png` | Sin elementos; accion de agregar y sugerencia IA |
| With data | `screens/objetivos/with-data.png` | Listado con elementos ordenables |
| Editing | `screens/objetivos/editing.png` | Formulario de alta/edicion |
| Validation error | `screens/objetivos/validation-error.png` | Elemento o seccion con error |
| AI suggestion | `screens/objetivos/ai-suggestion.png` | Propuesta IA pendiente de aceptar/descartar |
