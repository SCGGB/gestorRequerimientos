# SPEC-009 - Cierre de sesion desde la interfaz

- Estado: Aprobada
- Fecha: 2026-10-21
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/architecture/adr/003-autenticacion.md`, `doc/development/convenciones.md`, `doc/technical/api.md`, `specs/SPEC-008-autenticacion-roles/spec.md`, `specs/SPEC-008-autenticacion-roles/verify.md`
- Depende de: SPEC-008-autenticacion-roles

## Contexto y objetivo

SPEC-008 entrego la autenticacion completa: login con token JWT de 8 horas, overlay de login que conserva la ruta, autorizacion por rol, auditoria con actor real y el endpoint `POST /auth/logout` (204) que registra la accion `LOGOUT` en `SYS_AUDITORIA`. Sin embargo, el frontend nunca invoca ese endpoint: la busqueda de `logout` en `frontend/src` solo devuelve `api/auth.ts` (cliente HTTP) y `auth/AuthContext.tsx` (contexto), sin ningun componente que lo dispare. En consecuencia, el usuario no puede terminar su sesion desde la aplicacion y el token permanece en `localStorage` hasta que expiran las 8 horas, incluso en equipos compartidos. Este hueco quedo registrado como DC-07 en `specs/SPEC-008-autenticacion-roles/verify.md` tras la prueba end-to-end con Docker.

El objetivo de esta spec es: ofrecer una accion explicita de cierre de sesion en la interfaz, que llame al endpoint de auditoria existente, limpie el estado local de sesion y devuelva al usuario al overlay de login sin perder el trabajo persistido, manteniendo el estado de sesion coherente entre las pestanas del mismo navegador.

## Alcance

### Incluye

- Control de cierre de sesion en el header de la aplicacion, disponible para todo usuario autenticado, junto a la identidad del usuario (nombre y roles).
- Invocacion de `POST /auth/logout` con el token vigente al activar el control, reutilizando el contrato ya publicado en `doc/technical/api.md` (204, auditoria `LOGOUT` con actor real).
- Limpieza del estado local de sesion: eliminacion del token en `localStorage`, descarte del perfil y los roles en memoria y retorno al estado anonimo, con reapeticion del overlay de login y conservacion de la vista montada.
- Comportamiento "best effort": si `POST /auth/logout` falla (red o error del servidor), la sesion local se cierra igualmente.
- Sincronizacion del estado de sesion entre las pestanas del mismo navegador ante cualquier cambio del token en `localStorage` (alta por login o baja por logout).
- Pruebas e2e del flujo de cierre de sesion en `frontend/e2e/auth.spec.ts` y evidencia contra el stack real de Docker.
- Nota en `doc/technical/api.md` sobre el caracter best effort del cierre iniciado desde la UI y actualizacion del registro DC-07 en `specs/SPEC-008-autenticacion-roles/verify.md`.

### No incluye

- Revocacion del token en el backend, denylist de tokens o cierre de todas las sesiones del usuario: la sesion sigue siendo stateless y la invalidacion efectiva es por expiracion (8 horas), conforme al contrato vigente de `doc/technical/api.md`.
- Refresh token, extension de la sesion o qualquer cambio en la politica de expiracion.
- Accion separada de "cambiar de usuario": tras cerrar sesion, el overlay de login ya permite entrar con otra cuenta.
- Listado de sesiones activas, dispositivos o "cerrar todas las sesiones".
- Dialogo de confirmacion antes de cerrar la sesion.
- Cierre automatico por inactividad.
- Aviso emergente (toast) cuando la sesion se cierra desde otra pestana: el overlay ya comunica el estado.
- Cambios en el backend: no hay modifications de API, dominio, casos de uso ni esquema de datos, y por tanto ninguna migracion Alembic.
- Cualquier contenido asistido por IA: la aplicacion sigue operando con `AI_PROVIDER=none`.

## Requisitos funcionales

- RF-01. El frontend ofrece un control "Cerrar sesion" en el header, visible para todo usuario autenticado y acompanado de su identidad (nombre y roles), de modo que el usuario sabe con que cuenta esta operando.
- RF-02. Al activar el control, el frontend invoca `POST /auth/logout` con el token vigente; el backend responde 204 y registra la accion `LOGOUT` en `SYS_AUDITORIA` con el actor real, conforme a RF-12 de SPEC-008. El contrato del endpoint no cambia.
- RF-03. Tras el cierre, el frontend elimina el token de `localStorage`, descarta el perfil y los roles en memoria y pasa al estado anonimo: reaparece el overlay de login, el acceso a la aplicacion queda bloqueado y la vista actual permanece montada, sin perder el borrador persistido en la base de datos.
- RF-04. El cierre de sesion no pide confirmacion y no produce cambios persistidos en los datos de negocio; el borrador persistido del asistente se conserva intacto.
- RF-05. Si `POST /auth/logout` falla, el frontend cierra igualmente la sesion local y muestra el overlay de login: un fallo de auditoria en el backend nunca deja al usuario con una sesion a medio cerrar.
- RF-06. El estado de sesion se sincroniza entre las pestanas del mismo navegador: ante cualquier cambio del token en `localStorage` (alta por login o baja por logout), las demas pestanas releen la sesion y quedan en el estado correspondiente, sin necesidad de recargar.
- RF-07. El token se sigue almacenando unicamente en `localStorage` (`gestor.auth.token`) y no se expone en la interfaz, en la consola ni en los logs del cliente.
- RF-08. El backend permanece sin cambios: `POST /auth/logout` mantiene su contrato (204, sin revocacion del token, auditoria `LOGOUT`) y la sesion sigue siendo stateless.
- RF-09. La aplicacion opera sin IA (`AI_PROVIDER=none`) y la spec no introduce dependencias nuevas.

## Criterios de aceptacion

- CA-01. Dado un usuario autenticado, cuando observa el header, entonces ve su nombre, sus roles y el control "Cerrar sesion".
- CA-02. Dado un usuario autenticado, cuando activa el control, entonces se envia `POST /auth/logout` con el token vigente, el backend responde 204 y queda registrada una accion `LOGOUT` en `SYS_AUDITORIA` con el actor real.
- CA-03. Dado un usuario autenticado, cuando activa el control, entonces el token desaparece de `localStorage`, reaparece el overlay de login y la vista subyacente permanece montada, con el borrador persistido intacto.
- CA-04. Dado un `POST /auth/logout` que falla, cuando el usuario activa el control, entonces la sesion local se cierra igualmente y se muestra el overlay de login, sin error bloqueante.
- CA-05. Dado un usuario autenticado en dos pestanas del mismo navegador, cuando cierra sesion en una, entonces la otra queda en estado anonimo, con el overlay de login visible, sin necesidad de recargar.
- CA-06. Dado un usuario autenticado en dos pestanas del mismo navegador, cuando inicia sesion en una de ellas, entonces las demas pestanas releen la sesion y quedan coherentes con el token vigente.
- CA-07. Dado un usuario autenticado, cuando usa la aplicacion, entonces toda peticion se emite con el token vigente y el token no aparece en la consola ni en los logs del cliente.
- CA-08. Dado el arbol del repositorio, cuando se ejecutan `npm run build` y `npm run test:e2e` en `frontend/`, entonces no hay errores y las pruebas del flujo de cierre de sesion pasan.
- CA-09. Verificacion contra el stack real de Docker: el control produce `POST /auth/logout` con respuesta 204 y una fila `LOGOUT` en `SYS_AUDITORIA` con el actor real, y el token desaparece del almacenamiento del navegador.

## Reglas de negocio y validaciones

- El cierre de sesion es siempre explicito y solicitado por el usuario; esta spec no introduce cierre automatico por inactividad.
- La sesion es stateless: cerrar la sesion en la interfaz no invalida el token en el servidor. El token sigue siendo tecnicamente valido hasta su expiracion (8 horas) y la invalidacion efectiva es por expiracion, conforme al contrato vigente de `doc/technical/api.md`.
- La limpieza local del token es prioritaria sobre la confirmacion del backend: el cierre local siempre se ejecuta (comportamiento best effort) y el fallo del backend no se convierte en un error bloqueante para el usuario.
- El cierre de sesion es idempotente desde la interfaz: activar el control mas de una vez no produce errores ni efectos adicionales.
- La sincronizacion entre pestanas se resuelve con el evento `storage` de `localStorage`, sin polling, sin WebSocket y sin estado adicional en el servidor.
- La auditoria distingue dos situaciones: el cierre explicito queda registrado como `LOGOUT` con actor real; la expiracion de sesion no genera fila en `SYS_AUDITORIA` porque ocurre en el cliente y el backend no participa. No se crean acciones de auditoria nuevas.
- El cierre de sesion no altera ningun dato de negocio: ni el requerimiento en edicion, ni su borrador persistido, ni las firmas, ni los documentos generados.
- El control de cierre de sesion vive en el header, que ya esta marcado con `data-print-hide`: no aparece en las impresiones ni en los documentos generados.
- El overlay de login que reaparece tras el cierre muestra los campos vacios y no recuerda la contrasena.
- El cierre de sesion esta disponible para todos los roles (`ELABORO`, `REVISO`, `AUTORIZO` y `ADMIN`); no es una operacion de `ADMIN` ni modifica el catalogo de usuarios.
- La aplicacion sigue funcionando sin IA (`AI_PROVIDER=none`) y sin dependencias nuevas.

## Datos involucrados (a nivel funcional)

Esta spec no introduce estructuras de datos nuevas ni modifica el esquema. Reutiliza:

- `localStorage["gestor.auth.token"]` (frontend): unico almacen del token; su presencia define el estado de sesion del navegador.
- `POST /auth/logout` y `GET /auth/sesion` (backend, sin cambios): el primero audita y responde 204; el segundo devuelve la identidad vigente que el frontend usa para re-sincronizar el estado tras un evento `storage`.
- `SYS_AUDITORIA` (tabla existente de SPEC-001): se escribe una accion `LOGOUT` con `ENTIDAD`, `ACTOR` real y `DETALLE` conforme a la convencion de `doc/development/convenciones.md`.
- Estado en memoria del `AuthContext`: `status` (`checking`, `anonymous`, `authenticated`) y `user` (usuario, nombre, roles).

## Requisitos no funcionales aplicables

- Cambio exclusivamente en el frontend: sin modifications en `backend/`, sin migraciones Alembic y sin cambios de contrato en la API.
- Sin dependencias nuevas ni cambios en `frontend/package.json`.
- Tipado completo: `tsc -b` sin errores y `npm run build` en verde.
- Accesibilidad: el control es un elemento `<button>` con nombre accesible "Cerrar sesion" y la identidad del usuario se muestra como texto legible.
- Consistencia visual con los tokens institucionales del header existente y con los componentes `Button`/`Badge` ya disponibles.
- Errores y mensajes al usuario en espanol, sin exponer el valor del token.
- La aplicacion funciona con `AI_PROVIDER=none`.
- Sin logica de negocio en los componentes: la orquestacion vive en `auth/AuthContext.tsx` y el header solo dispara la accion.

## Decisiones tomadas y descartadas

1. **Alcance del cierre**: solo frontend mas auditoria, sin revocacion del token en el backend. Descartada la revocacion (denylist o version de token) porque exige migracion, verificacion en cada peticion y cambia el contrato stateless ya publicado en `doc/technical/api.md`; el MVP con 8 horas de expiracion lo tolera y la revocacion queda para una spec posterior.
2. **Ubicacion del control**: header de la aplicacion. Descartada la barra lateral por su baja visibilidad dentro del asistente, y descartado el menu desplegable de usuario por el clic adicional y el estado de UI que introduce.
3. **Fallo del backend al cerrar**: la sesion local se cierra igualmente. Descartado mantener la sesion activa ante un error, porque deja al usuario atrapado en una sesion a medio cerrar y la auditoria no es mas importante que la salida del usuario.
4. **Identidad visible**: el header muestra nombre y roles del usuario autenticado, no solo el boton. Descartado el boton aislado porque el usuario no debe adivinar con que cuenta esta operando.
5. **"Cambiar de usuario"**: no se incluye como accion separada. Descartada por redundancia: tras cerrar sesion, el overlay de login ya permite autenticarse con otra cuenta.
6. **Auditoria**: se mantiene la accion `LOGOUT` existente; no se crean `LOGOUT_MANUAL` ni `SESION_EXPIRADA`. Descartadas porque exigirian un contrato nuevo (endpoint o parametro) para distinguir situaciones que la auditoria funcional no necesita diferenciar en el MVP.
7. **Sincronizacion entre pestanas**: ante cualquier cambio del token, no solo ante su eliminacion. Descartada la variante limitada al borrado porque el token se comparte por origen: un login en una pestana dejaria a las demas con un estado incoherente.
8. **Confirmacion**: no se pide confirmacion. Descartada porque el borrador esta persistido en la base de datos (autosave), por lo que cerrar sesion no pierde trabajo.
9. **Aviso emergente al cierre desde otra pestana**: no se incluye. Descartado por simplicidad: el overlay de login ya indica que la sesion no esta activa.
10. **Cierre automatico por inactividad**: fuera de alcance. Descartado porque no fue solicitado y exigiria definir el umbral de inactividad, con el riesgo de cerrar la sesion durante una lectura larga.
11. **Cierre de todas las sesiones del usuario**: fuera de alcance. Descartado porque depende de la revocacion en backend excluida en la decision 1.

## Riesgos identificados

- El token sigue siendo valido en el servidor hasta 8 horas despues de cerrar sesion en la interfaz: un token copiado podria seguir usandose. Mitigacion: comportamiento explicito y documentado en `doc/technical/api.md`; la revocacion queda como spec posterior.
- La sincronizacion entre pestanas depende del evento `storage`, que no se dispara en la propia pestana que origino el cambio. Mitigacion: el cierre local se aplica de forma explicita en el flujo del boton y no depende del evento; el evento solo sirve para las pestanas hermanas.
- `localStorage` es de alcance por origen: el cierre no afecta a otros navegadores ni a otros perfiles del sistema operativo. Mitigacion: cada sesion es independiente y el backend mantiene su propia auditoria.
- El evento `storage` puede llegar en un momento en que el token aun no es valido para `GET /auth/sesion` (por ejemplo, durante un login en curso en otra pestana). Mitigacion: ante un fallo de relectura de la sesion, la pestana cae a estado anonimo sin dejar credenciales a medias.

## Preguntas abiertas

Ninguna. Las 11 preguntas del borrador se resolvieron en la seccion "Decisiones tomadas y descartadas".
