# SPEC-007 - Generacion de documentos DOCX y PDF

- Estado: aprobado
- Fecha: 2026-10-19
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/documents/mapeo-machote.md`, `doc/technical/api.md`, `doc/development/convenciones.md`, `doc/architecture/adr/001-backend-python-fastapi.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/004-plantilla-docxtpl-derivada.md`, `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/006-almacenamiento-objetos-dev.md`, `doc/architecture/adr/007-firmas-segun-estado.md`.
- Depende de: SPEC-001-fundaciones, SPEC-002-modelo-dominio-requerimiento, SPEC-003-api-requerimientos, SPEC-004-wizard-captura, SPEC-005-validacion-integral-y-maquina-de-estados, SPEC-006-vista-previa-a4.
- Prerrequisito: spike tecnico de derivacion de la plantilla DOCX a partir del machote institucional (recomendado en `doc/documents/mapeo-machote.md`), previo a la implementacion de RF-17.

## Contexto y objetivo

SPEC-006 dejo disponible la vista previa A4 como representacion de lectura construida por el backend desde la version persistida mediante un DTO neutral de renderizado, y declaro explicitamente que la generacion DOCX/PDF (esta spec) reutilizaria ese mismo contenido.

La especificacion funcional exige que la salida documental del MVP conserve la estructura del machote institucional (`templates/machote_requerimiento.docx`) y que el DOCX se genere desde una plantilla versionada, con un PDF equivalente obtenido a partir del mismo contenido/version. Vista previa, DOCX y PDF deben ser consistentes entre si, y el modelo estructurado en Oracle sigue siendo la fuente de verdad: los documentos son representaciones generadas, no la fuente.

El objetivo de esta spec es: generar el DOCX del requerimiento desde la plantilla derivada del machote y su PDF equivalente, a partir de una version persistida; registrar cada documento generado con su trazabilidad (version del requerimiento, version de plantilla, formato, fecha y actor); permitir su descarga y su regeneracion sin perder el historico; e integrar la accion de generacion en el paso 13 del wizard cuando el estado del requerimiento lo permita.

## Alcance

### Incluye

- Derivacion y versionado de la plantilla DOCX a partir del machote institucional (`templates/ers_plantilla_v1.docx`), conservando el machote original como referencia inmutable (ADR-004), previa realizacion del spike tecnico prerrequisito.
- Generacion del DOCX a partir de una version persistida del requerimiento y del mismo contenido normalizado que alimenta la vista previa.
- Generacion del PDF equivalente a partir del DOCX generado.
- Sustitucion del ticket (`T#` + folio) y de la version documental en encabezados y en la primera fila de control de versiones.
- Tabla de control de versiones (todas las versiones) y bloque de firmas (elaboro/reviso/autorizo) segun ADR-007.
- Reglas de contenido del machote: colecciones activas y ordenadas, seccion de coleccion vacia como "No aplica", requisitos futuros condicionales, fechas `dd-mm-aaaa`, saltos de linea del usuario y escapado de contenido.
- Registro y trazabilidad de cada documento generado (formato, version del requerimiento, version de plantilla, fecha/hora y actor) y su referencia al binario para consulta historica y descarga.
- Regeneracion de documentos sin sobrescribir los generados previamente.
- Condicion de generacion ligada al estado del requerimiento y a las firmas requeridas (ADR-005/ADR-007), con mensajes claros cuando no esta permitida.
- Integracion de la accion de generacion/descarga en el paso 13 del wizard, con manejo de errores.
- Pruebas backend (dominio/aplicacion/API) y verificacion de equivalencia DOCX/PDF y de consistencia con la vista previa.
- Documentacion del contrato funcional en `doc/technical/api.md`.

### No incluye

- Vista previa A4 y su contrato `PreviewDocument` (SPEC-006); esta spec lo reutiliza, no lo redefine.
- Subida de binarios de anexos y el adaptador de `StoragePort` (ADR-006 y su spec de storage).
- Imagenes/anexos reales dentro de "Diagramas Contextuales": se difieren a la spec de storage.
- Firma electronica o flujo automatico de aprobacion (ADR-005).
- Descripcion del cambio de la tabla de control de versiones: sigue sin existir en el modelo y se representa vacia/"—".
- Asistencia de IA (spec posterior).
- Autenticacion, roles y enforcement (SPEC-008).
- Nuevas secciones ajenas al machote (por ejemplo, criterios IEEE 830).

## Requisitos funcionales

- RF-01. El sistema genera el DOCX de un requerimiento a partir de una version persistida y congelada, reutilizando el mismo contenido normalizado que la vista previa; ningun renderizador consulta datos vivos ni el estado local del wizard.
- RF-02. El DOCX conserva la estructura y la presentacion del machote institucional: tamano de hoja y margenes del machote, primera pagina distinta, encabezados con ticket (`T#` + folio) y la leyenda de version documental, numeracion de pagina, tabla de control de versiones, bloque de firmas y las doce secciones del documento.
- RF-03. El ticket (`T#` + folio) y la version documental de la version consultada se reflejan en los encabezados y en la primera fila de la tabla de control de versiones; la version documental se captura una sola vez y alimenta todos los lugares donde aparece.
- RF-04. La tabla de control de versiones lista todas las versiones del requerimiento con su version, fecha, descripcion del cambio, reviso y elaboro; cuando la descripcion del cambio no existe en el modelo, la celda queda vacia (o "—").
- RF-05. El bloque de firmas muestra elaboro, reviso y autorizo con nombre y cargo de la version consultada; los roles sin firma registrada se representan con la celda vacia (o "—"), sin crear ni modificar firmas.
- RF-06. Las colecciones del documento incluyen unicamente elementos activos, ordenados por su orden; un elemento sin contenido no genera viñeta; una seccion de coleccion sin elementos activos conserva su titulo e imprime "No aplica".
- RF-07. Requisitos futuros: si no aplica, el documento imprime "No Aplica."; si aplica, incluye el texto y/o la lista de elementos activos ordenados.
- RF-08. Las fechas del documento se presentan en formato `dd-mm-aaaa`; los textos del usuario con saltos de linea se conservan y el contenido se escapa de forma que no corrompa el documento.
- RF-09. El PDF se obtiene convirtiendo el DOCX generado, de modo que DOCX y PDF sean equivalentes en contenido y estructura; no se genera el PDF con un motor distinto.
- RF-10. Cada documento generado (DOCX y PDF) se registra con al menos: formato, version del requerimiento, version de plantilla utilizada, fecha y hora de generacion, actor que la solicito y referencia al binario generado; el binario se persiste en Oracle (BLOB) gestionado por el adaptador de persistencia, sin exponer rutas fisicas ni secretos.
- RF-11. La generacion esta disponible solo cuando el estado del requerimiento y las firmas requeridas lo permiten conforme a la maquina de estados y a ADR-005/ADR-007; un intento no permitido se rechaza con un mensaje claro y no genera ni registra documentos.
- RF-12. Tras una generacion exitosa, el requerimiento pasa a `GENERADO` de forma automatica conforme a la maquina de estados, conservando el vinculo entre la version y los documentos generados.
- RF-13. Los documentos generados se pueden recuperar/descargar y regenerar; una nueva generacion agrega un registro nuevo y no sobrescribe los documentos generados con anterioridad.
- RF-14. El paso 13 del wizard ofrece la accion de generar y descargar el documento cuando el estado lo permite; cuando no lo permite, la accion se muestra deshabilitada con el motivo visible.
- RF-15. Si la generacion o la descarga falla, la UI muestra un mensaje legible y el wizard conserva su estado, permitiendo reintentar.
- RF-16. La funcionalidad opera sin IA (`AI_PROVIDER=none`) y no incorpora dependencias nuevas no justificadas (regla 6 de `AGENTS.md`).
- RF-17. La plantilla derivada del machote se versiona; cada documento generado registra la version de plantilla usada y el machote original permanece inmutable como referencia de presentacion. La derivacion se realiza despues del spike tecnico prerrequisito.
- RF-18. El DOCX/PDF reserva el espacio del encabezado destinado a los logotipos institucionales; la incorporacion de los logotipos reales queda como deuda tecnica registrada y no bloquea la generacion.
- RF-19. El archivo descargado se nombra con la convencion `T#<folio>-v<version>.<ext>` (por ejemplo `T#1234-v3.docx`), donde `<ext>` corresponde al formato solicitado.

## Criterios de aceptacion

- CA-01. Dado un requerimiento en un estado que permite la generacion, cuando se solicita el DOCX, entonces se genera un archivo DOCX cuyo encabezado muestra el ticket (`T#` + folio) y la version documental, y cuya estructura de secciones coincide con la vista previa de la misma version.
- CA-02. Dada una misma version, cuando se generan DOCX y PDF, entonces ambos presentan las mismas secciones, textos, listas, tabla de control de versiones y bloque de firmas (equivalencia de contenido y estructura).
- CA-03. Dada una version con elementos activos e inactivos, cuando se genera el documento, entonces solo aparecen los elementos activos y en el orden definido.
- CA-04. Dada una coleccion sin elementos activos, cuando se genera el documento, entonces la seccion conserva su titulo y muestra "No aplica".
- CA-05. Dado `requisitos_futuros_aplica=false`, cuando se genera el documento, entonces la seccion muestra "No Aplica."; dado `true`, entonces incluye el texto y/o la lista capturada.
- CA-06. Dadas las fechas del requerimiento y textos con saltos de linea, cuando se genera el documento, entonces las fechas aparecen en `dd-mm-aaaa` y los saltos de linea se conservan sin romper el archivo.
- CA-07. Dado un requerimiento con varias versiones, cuando se genera el documento, entonces la tabla de control de versiones incluye todas las versiones ordenadas, con sus firmantes elaboro/reviso cuando existan.
- CA-08. Dada una version sin firmas registradas, cuando se genera el documento, entonces los roles aparecen vacios/"—"; dada una version con firmas, entonces se muestran nombre y cargo sin crear ni modificar firmas.
- CA-09. Cuando se genera un documento, entonces el sistema registra su formato, la version del requerimiento, la version de plantilla, la fecha/hora y el actor, y el binario generado queda recuperable.
- CA-10. Dado un intento de generar en un estado no permitido o sin las firmas requeridas, entonces la operacion se rechaza con un mensaje claro y no se registra ningun documento.
- CA-11. Dada una generacion exitosa, cuando el flujo aplica la transicion correspondiente, entonces el requerimiento queda en `GENERADO` conforme a la maquina de estados y conserva la relacion con los documentos generados.
- CA-12. Dados documentos generados con anterioridad, cuando se solicitan de nuevo o se regenera, entonces se puede recuperar el historico y la nueva generacion no sobrescribe los documentos previos.
- CA-13. Dado el paso 13 en un estado que no permite la generacion, cuando se muestra la accion, entonces aparece deshabilitada con el motivo visible; en un estado que si la permite, entonces la accion esta disponible.
- CA-14. Dado un fallo en la generacion o descarga, cuando el usuario la solicita, entonces la UI muestra el mensaje correspondiente y el wizard conserva su estado para reintentar.
- CA-15. Dado el arbol del repositorio, cuando se ejecutan `ruff check .`, `mypy --strict app`, `pytest` y las pruebas de generacion (incluida la verificacion de equivalencia DOCX/PDF), entonces no hay errores.
- CA-16. Dado un documento generado, cuando se descarga, entonces el nombre del archivo sigue la convencion `T#<folio>-v<version>.<ext>` acorde al formato solicitado.

## Reglas de negocio y validaciones

- El modelo estructurado en Oracle es la fuente de verdad; DOCX y PDF son representaciones generadas.
- Vista previa, DOCX y PDF se producen desde el mismo contenido y version; la generacion nunca consulta datos vivos externos a la version persistida.
- Solo se incluyen elementos activos, ordenados por su orden; los elementos sin contenido no generan viñeta.
- Seccion de coleccion vacia: se conserva el titulo y se imprime "No aplica".
- Requisitos futuros: `false` se representa como "No Aplica."; `true` admite texto y/o elementos activos.
- Numeracion del machote: Necesidad Actual = 1, Objetivos = 2, Consideraciones = 3, Beneficios = 4 (4.1/4.2), Diagramas Contextuales = 5, Usuarios y Permisos = 6, Restricciones = 7, Requisitos futuros = 8, Volumetria = 9, Riesgos = 10; control de versiones y firmas no se numeran.
- Fechas siempre en `dd-mm-aaaa`.
- Firmas: solo existen cuando fueron registradas en `APROBADO`/`GENERADO` sobre la version vigente (ADR-007); la generacion no las captura ni las altera.
- La version documental se captura una sola vez y alimenta encabezados y control de versiones.
- La descripcion del cambio no existe en el modelo: la celda se representa vacia/"—".
- La plantilla derivada se versiona; todo cambio de presentacion genera una nueva version de plantilla y cada documento registra la usada (ADR-004).
- El machote original no se modifica.
- Los documentos generados no se sobrescriben; se conserva todo el historico sin limite de retencion.
- El archivo descargado se nombra `T#<folio>-v<version>.<ext>` segun el formato solicitado.
- Los anexos e imagenes reales de "Diagramas Contextuales" se difieren a la spec de storage; en esta spec solo se consideran metadatos.
- La descripcion del cambio permanece como deuda del modelo y se representa vacia/"—" en la tabla de control de versiones.
- Autenticacion, roles y enforcement de la generacion/descarga se difieren a SPEC-008; esta spec no los restringe.
- Los binarios generados se almacenan en Oracle como BLOB, referenciados por el registro del documento; no se persisten en el sistema de archivos ni en un object store.
- La generacion es sincrona: la peticion de generacion devuelve el documento (o su referencia de descarga) al concluir.
- Tras una generacion exitosa, el requerimiento pasa automaticamente a `GENERADO` conforme a la maquina de estados.
- El encabezado reserva el espacio de los logotipos institucionales; incorporarlos es deuda tecnica y no condiciona la generacion.
- La generacion respeta las precondiciones de estado y firmas de la maquina de estados y de ADR-005/ADR-007.
- La aplicacion opera sin IA; no hay contenido generado automaticamente.

## Datos involucrados (a nivel funcional)

- Version congelada del requerimiento: numero de version, version documental, fecha de version, titulo, tipo de cambio, sistema; narrativa (necesidad actual, descripcion contextual, manejo de errores, usuarios y permisos, requisitos futuros); colecciones activas (objetivos, consideraciones, beneficios cualitativos/cuantitativos, restricciones, volumetria, riesgos, requisitos futuros); anexos como metadatos; firmas registradas.
- Documento generado: formato (DOCX o PDF), requerimiento y version asociados, version de plantilla utilizada, fecha/hora de generacion, actor, referencia al binario generado (BLOB en Oracle) y estado/validez.
- Plantilla documental: identificador de version de plantilla y su correspondencia con el machote institucional.
- Encabezado del documento: folio, ticket (`T#` + folio), version documental y fecha de version.

El contrato concreto de la operacion de generacion, descarga y consulta de documentos, asi como sus esquemas de entrada/salida, se definen en `plan.md`.

## Requisitos no funcionales aplicables

- Arquitectura hexagonal: las reglas de composicion del documento viven en dominio/aplicacion; el router solo valida entrada, invoca el caso de uso y serializa.
- El dominio es puro: sin imports de FastAPI, SQLAlchemy ni librerias de generacion DOCX/PDF.
- Reutilizacion obligatoria del contenido normalizado de la vista previa; no duplicar reglas de negocio en el renderizador.
- Consistencia entre vista previa, DOCX y PDF, verificable mediante pruebas.
- Trazabilidad y auditoria de las generaciones (auditoria de tablas conforme a `doc/development/convenciones.md`).
- Fuentes del machote disponibles para la conversion a PDF, de modo que no se sustituyan tipografias.
- Los binarios se almacenan en Oracle como BLOB; la generacion sincrona debe completar dentro del tiempo maximo y del tamano maximo por documento que se fijen en `plan.md`.
- El espacio de los logotipos queda reservado; su incorporacion es deuda tecnica y no bloquea la generacion.
- Sin secretos, rutas absolutas ni artefactos de ejecucion dentro de imagenes o repositorio.
- Tipado completo; `ruff check .`, `mypy --strict app` y `pytest` sin errores.
- La aplicacion funciona sin IA (`AI_PROVIDER=none`).
- Sin dependencias nuevas no justificadas.

## Preguntas abiertas

No hay preguntas abiertas pendientes.

## Decisiones resueltas

- Almacenamiento de binarios generados: BLOB en Oracle, gestionado por el adaptador de persistencia.
- Plantilla: spike tecnico previo a la derivacion/versionado de `templates/ers_plantilla_v1.docx`.
- Modo de generacion: sincrona en la peticion.
- Transicion de estado: automatica a `GENERADO` tras una generacion exitosa.
- Logotipos del encabezado: se reserva el espacio y su incorporacion queda como deuda tecnica.
- Anexos e imagenes de "Diagramas Contextuales": se difieren a la spec de storage.
- Nombre del archivo descargado: `T#<folio>-v<version>.<ext>`.
- Descripcion del cambio: se mantiene como deuda del modelo (celda vacia/"—").
- Retencion e historico: se conservan todos los documentos generados, sin limite.
- Roles de generacion/descarga: se difieren a SPEC-008.
