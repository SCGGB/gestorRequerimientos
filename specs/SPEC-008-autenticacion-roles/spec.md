# SPEC-008 - Autenticacion, roles y autorizacion

- Estado: Aprobada
- Fecha: 2026-10-20
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/003-autenticacion.md`, `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/007-firmas-segun-estado.md`, `doc/development/convenciones.md`, `doc/technical/api.md`
- Depende de: SPEC-001-fundaciones, SPEC-002-modelo-dominio-requerimiento, SPEC-003-api-requerimientos, SPEC-005-validacion-integral-y-maquina-de-estados, SPEC-007-generacion-docx-pdf

## Contexto y objetivo

Las specs anteriores dejaron el flujo completo funcionando pero sin identidad real: los endpoints de negocio no exigen autenticacion ni rol (SPEC-003 dejo el punto de extension `AuthProvider` sin enforcement), los campos de actor (`CREATED_BY`/`UPDATED_BY`, `GENERADO_BY`) se llenan con `SYSTEM` (SPEC-002 y SPEC-007), la tabla fundacional `SYS_AUDITORIA` existe pero no tiene uso funcional (SPEC-001), y SPEC-007 difirio explicitamente los roles de generacion/descarga de documentos a esta spec.

La especificacion funcional exige "autorizacion por roles" como requisito no funcional, y ADR-005 establece que las transiciones de estado son manuales y "las ejecuta un usuario con el rol autorizado". ADR-003 ya decidio el enfoque: puerto `AuthProvider`, autenticacion local con usuarios administrados por la aplicacion y tokens JWT firmados en el MVP, con roles ELABORO, REVISO, AUTORIZO y ADMIN, dejando el adaptador OIDC para una fase posterior sin cambiar el dominio.

El objetivo de esta spec es: autenticar al usuario, aplicar autorizacion por rol sobre los endpoints de negocio (incluidas transiciones, firmas y generacion/descarga de documentos), sustituir el actor placeholder `SYSTEM` por el usuario autenticado, activar el registro de auditoria en `SYS_AUDITORIA`, y bloquear el acceso del frontend sin sesion valida; sin que la aplicacion dependa de IA y sin alterar la politica de firmas ni la maquina de estados ya definidas.

## Alcance

### Incluye

- Autenticacion local de usuarios administrados por la aplicacion, conforme a ADR-003, tras el puerto `AuthProvider`; sesion/token JWT (8 horas, sin refresh) que el frontend adjunta a cada peticion.
- Identidad autenticada (usuario y conjunto de roles) disponible para los casos de uso, sustituyendo al stub `Principal` de SPEC-003; permisos por union de los roles del usuario.
- Autorizacion por rol sobre todos los endpoints de `/api/v1` (lectura y escritura): rechazo `401` sin sesion valida y `403` sin el permiso requerido, con error estructurado y sin efectos persistidos; solo `/health` y `/version` permanecen publicos.
- Matriz de autorizacion rol-accion, definida en esta spec (ver Reglas de negocio), aplicada a endpoints, transiciones de estado (ADR-005), captura de firmas (sin alterar ADR-007) y generacion/descarga de documentos (responsabilidad diferida por SPEC-007).
- Gestion de usuarios (alta, baja, edicion de credenciales y roles asignados) exclusivamente por `ADMIN`, por API y por pantalla propia; el `ADMIN` no puede desactivarse a si mismo; bloqueo automatico tras 5 intentos fallidos de login con reinicio manual por `ADMIN`.
- Semilla del primer usuario `ADMIN` en la migracion Alembic base, con credenciales provenientes de variables de entorno (fuera de imagenes y de git).
- Sustitucion del actor placeholder `SYSTEM` por el usuario autenticado en los campos de auditoria existentes (`CREATED_BY`/`UPDATED_BY` y `GENERADO_BY`).
- Registro de auditoria funcional en `SYS_AUDITORIA` (tabla creada en SPEC-001) con entidad, identificador, accion, actor, detalle (JSON, incluido el `motivo` de la transicion) y marcas de tiempo; retencion indefinida en MVP.
- Ajuste del contrato de `/transicionar`: se elimina `actor_id` del body (el actor es siempre la identidad autenticada) y `motivo` pasa a quedar registrado en `SYS_AUDITORIA`.
- Frontend: pantalla de login (overlay que conserva la ruta), envio de credenciales, manejo de `401`/`403`, pantalla de gestion de usuarios y conservacion del borrador persistido ante expiracion de sesion.
- Pantallas de login y gestion de usuarios disenadas en esta spec con los tokens institucionales existentes (no hay referencia Stitch en `doc/ui/`).
- Configuracion por variables de entorno ya previstas en SPEC-001 (`AUTH_PROVIDER`, `JWT_SECRET`) mas las de credenciales de la semilla `ADMIN`.
- Pruebas backend (dominio/aplicacion/API) de autenticacion, autorizacion y auditoria, y verificacion de calidad (`ruff`, `mypy --strict`, `pytest`).
- Documentacion del contrato funcional en `doc/technical/api.md`.

### No incluye

- Adaptador OIDC institucional (OCI IAM, Keycloak, AD/LDAP): fase posterior segun ADR-003; esta spec solo exige que el dominio no cambie al sustituirlo.
- Firma electronica o flujo automatico de aprobacion (ADR-005).
- Historial de transiciones como tabla o pantalla: el `motivo` y el actor de `/transicionar` se cubren registrandolos en `SYS_AUDITORIA`, pero no se crea una vista de historial de estados (queda pendiente de una spec futura si se requiere).
- Restablecimiento de contrasena por correo u otros canales (no existe infraestructura de correo); el unico restablecimiento es manual por `ADMIN` via API.
- Cambios a la maquina de estados, a la validacion integral (SPEC-005) ni a la politica de firmas ADR-007.
- Catalogo y gestion de cargos por rol (ya existente y editable en el requerimiento; ADR-005).
- Referencia visual Stitch para login/gestion de usuarios: no existe en `doc/ui/`; estas pantallas no toman base de Stitch.
- Purgado, exportacion o consulta de `SYS_AUDITORIA` (retencion indefinida en MVP; la auditoria es de solo escritura desde el flujo normal).
- Contenido asistido por IA: la aplicacion sigue operando con `AI_PROVIDER=none`.

## Requisitos funcionales

- RF-01. El sistema autentica usuarios locales administrados por la aplicacion conforme a ADR-003, a traves del puerto `AuthProvider`; la autenticacion esta disponible sin ningun servicio de IA.
- RF-02. El sistema reconoce los roles del MVP: `ELABORO`, `REVISO`, `AUTORIZO` y `ADMIN` (ADR-003); un usuario puede ostentar varios roles simultaneamente y su permiso es la union de los permisos de todos ellos.
- RF-03. Todo endpoint bajo `/api/v1` (lectura y escritura) exige una sesion valida; sin token valido o con token expirado responde `401` con error estructurado y no ejecuta la operacion. `/health` y `/version` permanecen publicos.
- RF-04. La matriz de autorizacion por rol y accion/endpoint (definida en esta spec) rige toda operacion; un usuario autenticado sin el permiso requerido recibe `403` con error estructurado y la operacion no produce ningun efecto persistido.
- RF-05. Las transiciones de estado se ejecutan unicamente mediante usuarios autenticados con el rol que asigna la matriz segun ADR-005; un usuario sin ese rol obtiene `403` y el estado del requerimiento no cambia.
- RF-06. La captura de firmas se sujeta a la matriz: cada rol registra unicamente la firma que le corresponde (`ELABORO` firma Elaboro, `REVISO` firma Reviso, `AUTORIZO` firma Autorizo) y `ADMIN` no registra firmas; sin alterar la politica ADR-007: solo en estados `APROBADO`/`GENERADO` y sobre la version vigente.
- RF-07. Generar documentos exige el rol `AUTORIZO` o `ADMIN` (responsabilidad que SPEC-007 difirio a esta spec); descargarlos puede cualquier usuario autenticado; el resto del comportamiento de SPEC-007 no cambia.
- RF-08. Solo el rol `ADMIN` da de alta, da de baja y edita usuarios (credenciales y roles asignados), por API y por pantalla; `ADMIN` no puede desactivarse a si mismo; un usuario dado de baja o desactivado no puede iniciar sesion ni operar.
- RF-09. El sistema bloquea el inicio de sesion tras 5 intentos fallidos consecutivos; el reinicio lo ejecuta `ADMIN` al editar al usuario; las contrasenas se almacenan cifradas, nunca en claro.
- RF-10. El sistema siembra el usuario `ADMIN` inicial en la migracion Alembic, con credenciales provenientes de variables de entorno; la aplicacion nunca queda sin un medio de acceso inicial.
- RF-11. El sistema registra el usuario autenticado como actor en las operaciones que hoy usan el placeholder `SYSTEM`: `CREATED_BY`/`UPDATED_BY` de las tablas de negocio y `GENERADO_BY` de los documentos generados.
- RF-12. El sistema registra en `SYS_AUDITORIA` las acciones relevantes: login (exitoso, fallido y bloqueo), logout, alta/baja/edicion de usuarios, creacion y edicion de requerimiento y versiones, transiciones de estado (con su `motivo` en `DETALLE`), firmas, y generacion/descarga de documentos; con entidad, identificador de entidad, accion, actor, detalle (JSON) y marcas de tiempo.
- RF-13. La sesion tiene expiracion de 8 horas y sin refresh token; al expirar, el sistema exige re-autenticacion mediante un overlay de login que conserva la ruta, y la expiracion no altera ni pierde el borrador persistido en la base de datos.
- RF-14. El frontend bloquea el acceso a la aplicacion sin sesion valida, ofrece el login, envia las credenciales, adjunta el token a las peticiones y, ante `401` o `403`, muestra un mensaje legible y dirige al usuario (login o mensaje de acceso denegado) sin perder el trabajo persistido.
- RF-15. La aplicacion opera sin IA (`AI_PROVIDER=none`) y la autenticacion no incorpora dependencias nuevas sin justificar (regla 6 de `AGENTS.md`).
- RF-16. Los secretos necesarios (clave de firma del token, credenciales iniciales del `ADMIN`) se configuran por variables de entorno conforme a SPEC-001 y `.env.example`; no se persisten en imagenes ni en el repositorio.
- RF-17. El cuerpo de `POST /requerimientos/{id}/transicionar` elimina `actor_id`; el actor registrado es siempre la identidad autenticada, y el `motivo` opcional queda persistido en `SYS_AUDITORIA`.
- RF-18. El dominio permanece independiente del proveedor de identidad: la sustitucion futura por OIDC (ADR-003) no requiere cambiar las reglas de negocio ni los casos de uso.

## Criterios de aceptacion

- CA-01. Dado un usuario existente y activo con credenciales correctas, cuando se autentica, entonces el sistema concede una sesion valida (8 horas) y la identidad devuelta incluye el usuario y su conjunto de roles.
- CA-02. Dado un usuario inexistente o con credenciales incorrectas, cuando se intenta autenticar, entonces el sistema rechaza el intento con un mensaje claro que no revela si el usuario existe.
- CA-03. Dada una peticion a cualquier endpoint de `/api/v1` (lectura o escritura) sin token, o con token invalido o expirado, cuando se procesa, entonces responde `401` con error estructurado y la operacion no se ejecuta.
- CA-04. Dado un usuario autenticado sin el permiso que exige la accion solicitada segun la matriz, cuando invoca la operacion, entonces responde `403` con error estructurado y no hay ningun cambio persistido.
- CA-05. Dado un requerimiento en un estado transitable, cuando un usuario con el rol que asigna la matriz solicita la transicion, entonces se aplica conforme a SPEC-005; dado un usuario sin ese rol, entonces se rechaza con `403` y el estado no cambia.
- CA-06. Dado un requerimiento en `APROBADO`/`GENERADO`, cuando un usuario intenta registrar una firma que no corresponde a su rol (o `ADMIN` intenta firmar), entonces se rechaza con `403` y la firma no se persiste; cuando el rol correspondiente la registra, entonces se persiste conservando la politica ADR-007.
- CA-07. Dado un requerimiento en estado que permite la generacion, cuando un usuario sin rol `AUTORIZO` ni `ADMIN` solicita generar documentos, entonces se rechaza con `403` sin generar nada; con ese rol, entonces la operacion funciona conforme a SPEC-007; descargar puede cualquier usuario autenticado.
- CA-08. Dado un usuario `ADMIN` autenticado, cuando abre la pantalla de gestion de usuarios y da de alta un usuario con roles asignados, entonces el nuevo usuario puede iniciar sesion y opera con la union de esos roles; cuando da de baja o desactiva a un usuario, entonces este no puede iniciar sesion; cuando intenta desactivarse a si mismo, entonces el sistema lo rechaza.
- CA-09. Dado un usuario con 5 intentos fallidos consecutivos, cuando intenta iniciar sesion de nuevo, entonces el sistema lo rechaza por bloqueo; cuando `ADMIN` edita al usuario, entonces el contador se reinicia y puede volver a intentarlo.
- CA-10. Dada la migracion Alembic aplicada, cuando se arranca la aplicacion por primera vez, entonces existe el usuario `ADMIN` inicial y puede iniciar sesion con las credenciales de las variables de entorno.
- CA-11. Dada una operacion exitosa de creacion, edicion, transicion, firma o generacion de documentos, cuando se consulta el registro afectado y `SYS_AUDITORIA`, entonces el actor registrado es el usuario autenticado y no `SYSTEM`; en una transicion, `DETALLE` incluye el `motivo`.
- CA-12. Dado un usuario con sesion expirada, cuando vuelve a realizar una operacion, entonces recibe `401` y el frontend muestra el overlay de login conservando la ruta; tras re-autenticarse, el borrador persistido se conserva intacto y la interfaz se restaura desde la base de datos.
- CA-13. Dado un endpoint publico (`/health`, `/version`), cuando se invoca sin token, entonces responde `200`.
- CA-14. Dado un usuario con dos roles con permisos distintos, cuando invoca una operacion permitida para cualquiera de los dos, entonces se le concede (union de permisos).
- CA-15. Dada la aplicacion ejecutandose con `AI_PROVIDER=none`, cuando se ejecutan las operaciones de autenticacion, autorizacion y auditoria, entonces funcionan sin ningun servicio de IA.
- CA-16. Dado el arbol del repositorio, cuando se ejecutan `ruff check .`, `mypy --strict app` y `pytest` (incluidas las pruebas de autenticacion, autorizacion y auditoria), entonces no hay errores.

## Reglas de negocio y validaciones

- Roles del MVP, fijos: `ELABORO`, `REVISO`, `AUTORIZO`, `ADMIN` (ADR-003). Un usuario puede tener varios roles; el permiso es la union de los de todos sus roles.
- Matriz de autorizacion (aprobada como decision de esta spec; `ADMIN` hereda todos los permisos salvo la excepcion de firmas):

| Accion | ELABORO | REVISO | AUTORIZO | ADMIN |
|---|---|---|---|---|
| Lectura (listado, detalle, vista previa, catalogos) | Si | Si | Si | Si |
| Crear/editar requerimiento y versiones | Si | No | No | Si |
| Transicion `BORRADOR -> EN_REVISION` | Si | No | No | Si |
| Transicion `EN_REVISION -> VALIDADO` | No | Si | No | Si |
| Transicion `VALIDADO -> APROBADO` | No | No | Si | Si |
| Transicion `APROBADO -> GENERADO` (genera documentos) | No | No | Si | Si |
| Transicion `-> CANCELADO` | No | No | Si | Si |
| Firma Elaboro | Si | No | No | No |
| Firma Reviso | No | Si | No | No |
| Firma Autorizo | No | No | Si | No |
| Generar documentos | No | No | Si | Si |
| Descargar documentos | Si | Si | Si | Si |
| Gestion de usuarios (alta/baja/edicion) | No | No | No | Si |

- Las transiciones de estado siguen siendo manuales; la autorizacion por rol solo controla quien puede ejecutarlas, no automatiza ni altera la maquina de estados (ADR-005, SPEC-005).
- Las firmas conservan la politica ADR-007: solo en `APROBADO`/`GENERADO` y sobre la version vigente; la autorizacion agrega el control de rol (cada rol solo registra la suya; `ADMIN` no firma) sin cambiar cuando ni sobre que se firma. Las firmas siguen siendo registros de texto, sin firma electronica.
- Generacion de documentos: solo `AUTORIZO`/`ADMIN`; descarga: cualquier usuario autenticado.
- Gestion de usuarios: solo `ADMIN`; no puede desactivarse a si mismo; el alta define los roles y el estado activo.
- Politica de credenciales: contrasena minimo 8 caracteres; sin expiracion; bloqueo tras 5 intentos fallidos consecutivos; reinicio manual por `ADMIN`; restablecimiento unicamente por `ADMIN` via API (no hay correo). Contrasenas cifradas, nunca en claro.
- Sesion: JWT de 8 horas, sin refresh token; invalidacion por expiracion (la BD es la fuente de verdad y el token no transporta datos de negocio).
- Bootstrap: el usuario `ADMIN` inicial se siembra en la migracion Alembic con credenciales de variables de entorno.
- El usuario autenticado sustituye al placeholder `SYSTEM` en `CREATED_BY`/`UPDATED_BY` y `GENERADO_BY`; los registros historicos previos no se migran.
- Toda accion relevante queda auditada en `SYS_AUDITORIA` con el actor real y retencion indefinida; en las transiciones, el `motivo` se persiste en `DETALLE` (JSON); la auditoria es de solo escritura desde el flujo normal (su consulta no forma parte de esta spec).
- `/transicionar` ya no acepta `actor_id`: el actor es siempre la identidad autenticada (cambio de contrato documentado frente a SPEC-005).
- El proveedor de identidad del MVP es local y administrado por la aplicacion; el adaptador se sustituira por OIDC en fase posterior sin cambiar el dominio (ADR-003, RF-18).
- Secretos y credenciales se manejan fuera de imagenes y de git, por variables de entorno (SPEC-001, `AGENTS.md`).
- Un error de autorizacion (`403`) o de sesion (`401`) nunca debe dejar efectos parciales persistidos.
- La aplicacion sigue funcionando sin IA (`AI_PROVIDER=none`).

## Datos involucrados (a nivel funcional)

- Usuario: identificador, nombre visible, credenciales (almacenadas cifradas), conjunto de roles asignados, estado activo/inactivo, contador de intentos fallidos de acceso y marcas de auditoria.
- Rol: catalogo fijo del MVP (`ELABORO`, `REVISO`, `AUTORIZO`, `ADMIN`).
- Sesion/token: identidad del usuario, sus roles y expiracion (8 horas); sin datos de negocio.
- Auditoria (tabla existente `SYS_AUDITORIA` de SPEC-001): `ENTIDAD`, `ENTIDAD_ID`, `ACCION`, `ACTOR`, `DETALLE` (JSON; incluye el `motivo` de transiciones y el detalle de eventos de autenticacion), `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY`.
- Campos de actor existentes que dejan de ser `SYSTEM`: `CREATED_BY`/`UPDATED_BY` de tablas de negocio y `GENERADO_BY` de `REQ_DOCUMENTO`.
- Matriz de autorizacion rol-accion: definida en esta spec (Reglas de negocio); el mapeo concreto a endpoints y su codificacion viven en `plan.md`.

El contrato concreto de los endpoints de autenticacion (`/auth/login`, `/auth/logout`) y de gestion de usuarios, y el mapeo de la matriz a endpoints, se definen en `plan.md`.

## Requisitos no funcionales aplicables

- Arquitectura hexagonal: las reglas de autorizacion viven en dominio/aplicacion; el proveedor de identidad es un adaptador detras de `AuthProvider`, y el router solo valida entrada, invoca y serializa.
- El dominio es puro: sin imports de FastAPI, SQLAlchemy ni librerias de JWT/u OIDC.
- Secretos fuera de imagenes y de git; configuracion por variables de entorno ya previstas (`AUTH_PROVIDER`, `JWT_SECRET`) y las nuevas de la semilla `ADMIN`.
- La aplicacion funciona sin IA (`AI_PROVIDER=none`).
- Errores estructurados en espanol con el envelope de errores de `doc/technical/api.md`.
- Auditoria conforme a `doc/development/convenciones.md` sobre la tabla fundacional `SYS_AUDITORIA`.
- Sustitucion del proveedor de identidad por OIDC en fase posterior sin cambios de dominio (ADR-003).
- Tipado completo; `ruff check .`, `mypy --strict app` y `pytest` sin errores.
- Sin dependencias nuevas no justificadas (el cifrado de contrasenas y la emision de JWT deben justificarse en `plan.md`, preferentemente con la stdlib).

## Decisiones tomadas y descartadas

1. **Matriz de autorizacion**: reparto de transiciones por etapa (ELABORO inicia, REVISO valida, AUTORIZO aprueba/genera/cancela) con `ADMIN` heredando todo. Descartadas: matriz laxa (cualquier rol transiciona) por debilitar la trazabilidad, y matriz restrictiva (sin `ADMIN` en transiciones) porque `ADMIN` debe poder operar.
2. **Multi-rol**: si, varios roles por usuario con permiso por union. Descartado el rol unico por no encajar con el stub `Principal` de SPEC-003 y limitar perfiles reales.
3. **Firmas por rol**: cada rol registra solo la suya y `ADMIN` no firma (gestiona, no valida). Descartado que `ADMIN` firme las tres (permitiria que una sola persona completara todas las firmas) y la matriz flexible sin atar rol a firma (romperia la coherencia con el catalogo de cargos por rol de ADR-005).
4. **Gestion de usuarios**: solo `ADMIN`, por API y pantalla en esta spec, sin autodesactivacion (evita al `ADMIN` quedarse sin salida). Descartada la autodesactivacion por el riesgo de bloqueo.
5. **Bootstrap del `ADMIN` inicial**: semilla en migracion Alembic con credenciales de variables de entorno. Descartados el script manual (operacion olvidable) y el primer arranque automatico (logica de negocio en el arranque).
6. **Politica de credenciales**: minima (8 caracteres, sin expiracion) mas bloqueo tras 5 intentos y restablecimiento por `ADMIN`. Descartada la expiracion a 90 dias por sumar friccion sin infraestructura de aviso.
7. **Token**: 8 horas sin refresh, con overlay de login que conserva la ruta y restaura el borrador desde la BD al re-autenticar. Descartado el refresh token de 15 minutos por complejidad innecesaria en MVP con borradores persistidos.
8. **`actor_id` de `/transicionar`**: se elimina del body; el actor es siempre la identidad autenticada. Descartado conservarlo como override por abrir la puerta a suplantacion de actor. Cambio de contrato respecto a SPEC-005 documentado aqui (RF-17).
9. **Permisos de lectura**: todo `/api/v1` protegido, solo `/health` y `/version` publicos. Descartada la lectura abierta por exponer datos de requerimientos sin identidad.
10. **Alcance de `SYS_AUDITORIA`**: lista completa de acciones, retencion indefinida, y la deuda `motivo`/`actor_id` de SPEC-005 se cubre aqui (`motivo` en `DETALLE`, `actor_id` eliminado). Descartado el alcance minimo y aplazar la deuda a una spec futura.
11. **Pantallas**: login y gestion de usuarios se disenan en esta spec con tokens institucionales (no existe referencia Stitch). Descartado aplazar la pantalla de gestion por dejar una funcionalidad `ADMIN` inoperante.
12. **Riesgo de contrato**: eliminar `actor_id` y añadir enforcement rompe consumidores existentes del frontend; se mitiga ajustando frontend y `doc/technical/api.md` en la misma spec.
13. **Riesgo de secretos**: la semilla `ADMIN` introduce credenciales en variables de entorno; se mitiga manteniendolas fuera de imagenes y de git (SPEC-001, `AGENTS.md`) y avisando en `.env.example`.

## Preguntas abiertas

Ninguna. Las 11 preguntas del borrador se resolvieron en la seccion "Decisiones tomadas y descartadas".
