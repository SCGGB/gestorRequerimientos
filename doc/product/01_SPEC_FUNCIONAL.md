# Especificacion funcional

## Objetivo
Construir una aplicacion que estandarice el levantamiento de requerimientos y genere la Especificacion de Requerimientos de Software con la estructura institucional del machote de referencia.

La informacion se captura una sola vez como datos estructurados y se reutiliza para validacion, asistencia opcional de IA, vista previa, versionado, generacion DOCX/PDF y consulta historica.

## Documento final de referencia
La salida documental del MVP debe conservar la estructura logica del archivo `templates/machote_requerimiento.docx`.

La estructura funcional identificada es:
1. Control de versiones.
2. Firmas: Elaboro, Reviso y Autorizo.
3. Necesidad Actual.
4. Objetivos Generales.
5. Consideraciones.
6. Beneficios Esperados.
   - Beneficios Cualitativos.
   - Beneficios Cuantitativos.
7. Diagramas Contextuales.
8. Usuarios y Permisos.
9. Restricciones.
10. Requisitos futuros.
11. Volumetria y Rendimiento.
12. Riesgos Iniciales.

El machote es la referencia de presentacion. El modelo estructurado almacenado en Oracle es la fuente de verdad.

## Tipos de cambio iniciales
- Nueva funcionalidad
- Correccion
- Reporte
- Integracion
- Base de datos
- Mejora tecnica

El catalogo debe ser configurable. El tipo de cambio puede agregar informacion complementaria, pero no debe romper la estructura documental institucional requerida para el MVP.

## Flujo principal
1. Crear un nuevo requerimiento.
2. Capturar datos generales y tipo de cambio.
3. Ejecutar captura escalonada segun las secciones del documento final.
4. Guardar borradores durante el proceso.
5. Validar campos obligatorios y reglas condicionales.
6. Permitir asistencia opcional de IA sobre campos habilitados.
7. Ejecutar validacion integral en el backend (FastAPI).
8. Mostrar vista previa con la misma estructura logica del documento.
9. Crear una version consistente del requerimiento.
10. Generar DOCX desde el machote versionado.
11. Generar PDF desde el mismo contenido/version.
12. Conservar datos, versiones y documentos en Oracle/repository definido.

## Wizard del MVP

El wizard sigue la estructura del machote institucional (secciones del documento final). Las referencias visuales de Stitch (`doc/ui/`) son guia de estilo, componentes y estados; no amplian el alcance funcional ni incorporan secciones ajenas al machote (por ejemplo, requerimientos funcionales/no funcionales o criterios IEEE 830).

### Paso 1 - Datos generales
- Ticket/folio externo (prefijo `T#` fijo definido por el sistema; el usuario captura unicamente el numero del folio, que es unico).
- Titulo del requerimiento.
- Tipo de cambio.
- Sistema.
- Version documental.
- Fecha de version.

### Paso 2 - Necesidad actual
Texto narrativo que describe la necesidad o problema que origina el requerimiento.

### Paso 3 - Objetivos generales
Coleccion ordenada. El usuario puede agregar, editar, eliminar y reordenar objetivos.

### Paso 4 - Consideraciones
Coleccion ordenada de reglas, condiciones, supuestos o elementos relevantes del requerimiento.

### Paso 5 - Beneficios esperados
Dos colecciones independientes:
- Cualitativos.
- Cuantitativos.

### Paso 6 - Diagramas contextuales
- Descripcion contextual.
- Uno o mas anexos/imagenes/diagramas cuando apliquen.
- Texto complementario, por ejemplo manejo de errores, cuando forme parte del contexto.

### Paso 7 - Usuarios y permisos
Descripcion de usuarios autorizados, alcance de acceso y restricciones funcionales conocidas.

### Paso 8 - Restricciones
Coleccion ordenada de restricciones.

### Paso 9 - Requisitos futuros
- Opcion `No aplica`.
- Si aplica, captura narrativa y/o lista de requisitos futuros.

### Paso 10 - Volumetria y rendimiento
Coleccion ordenada de elementos. Cada elemento describe informacion conocida sobre volumen, concurrencia, periodos criticos, tiempos o condiciones de rendimiento. Aplica el mismo comportamiento de colecciones que objetivos, consideraciones, restricciones y riesgos.

### Paso 11 - Riesgos iniciales
Coleccion ordenada de riesgos. Para el MVP se conserva el texto del riesgo; severidad, probabilidad y mitigacion pueden evolucionar posteriormente sin alterar el documento base.

### Paso 12 - Control documental
- Elaboro.
- Reviso.
- Autorizo.
- Cargo/puesto de cada participante cuando aplique.
- Descripcion de cambio para control de versiones.

### Paso 13 - Revision
- Validacion integral.
- Vista previa.
- Identificacion de sugerencias IA pendientes.
- Generacion documental cuando el estado lo permita.

## Comportamiento de colecciones
Objetivos, consideraciones, beneficios, restricciones, volumetria y riesgos no deben almacenarse como un unico bloque de texto cuando sean elementos multiples. Cada elemento debe conservar al menos:
- identificador;
- orden;
- contenido;
- estado activo/eliminado segun estrategia de versionado.

## Campos configurables y campos de dominio
La configuracion dinamica sigue siendo util para extensiones por tipo de cambio. Sin embargo, las secciones institucionales del machote son parte del contrato documental del MVP y deben tener soporte explicito en el dominio.

Los campos dinamicos adicionales pueden definir:
- `codigo`
- `etiqueta`
- `tipo`
- `obligatorio`
- `orden`
- `visible_si`
- `validacion`
- `ayuda`
- `ia_habilitada`
- `incluye_documento`

## Estados
`BORRADOR` -> `EN_REVISION` -> `VALIDADO` -> `APROBADO` -> `GENERADO`.

Estado alterno: `CANCELADO`.

Politica de firmas y transiciones (ver ADR-005):
- Las firmas `Elaboro` y `Reviso` se registran por version del requerimiento.
- La firma `Autorizo` se registra unicamente en el bloque de firmas de la version vigente.
- Las transiciones de estado son manuales y las ejecuta un usuario con el rol autorizado; el MVP no exige firma electronica.
- El cargo de cada firma proviene de un catalogo por rol, con valor por defecto editable en el requerimiento.

## Entregables MVP
- Registro estructurado en Oracle.
- Vista previa alineada al machote.
- DOCX generado desde plantilla versionada.
- PDF equivalente.
- Historico de versiones y documentos.

## Evolucion
- Criterios de aceptacion estructurados.
- Ficha tecnica.
- Plan de implementacion.
- Casos de prueba.
- Checklist de liberacion.
- Analisis tecnico estructurado por frontend/backend/BD/integraciones.

## Requisitos no funcionales
- Trazabilidad de cambios.
- Autorizacion por roles.
- Guardado resiliente de borradores.
- Auditoria.
- Consistencia entre vista previa, DOCX y PDF.
- Portabilidad del proveedor de IA.
- La aplicacion debe operar sin IA.

## Criterio funcional central
El sistema captura un modelo estructurado independiente del formato fisico del Word. El machote determina la presentacion final, no la estructura fisica de la base de datos.
