# SPEC-002 - Modelo de dominio y persistencia del requerimiento

- Estado: Approved
- Fecha: 2026-10-13
- Documentos aplicables: `AGENTS.md`, `doc/product/01_SPEC_FUNCIONAL.md`, `doc/documents/mapeo-machote.md`, `doc/development/convenciones.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/004-plantilla-docxtpl-derivada.md`, `doc/architecture/adr/005-firmas-estados.md`, `doc/architecture/adr/006-almacenamiento-objetos-dev.md`
- Depende de: SPEC-001

## Contexto y objetivo
Definir el modelo de dominio del requerimiento (contenedor, versiones, colecciones, firmas y anexos), las tablas Oracle que lo persisten y los puertos/adaptadores de repositorio, de modo que el modelo estructurado sea la fuente de verdad y las specs posteriores solo lo consuman.

## Alcance

### Incluye
- Entidades, objetos de valor, enumeraciones e invariantes de dominio del requerimiento (capa `domain`, sin dependencias de FastAPI, SQLAlchemy, DOCX ni IA).
- Modelo de versionado: contenedor `REQ_REQUERIMIENTO` + versiones congeladas `REQ_VERSION`.
- Colecciones ordenadas por versión: objetivos, consideraciones, beneficios (cualitativos/cuantitativos), restricciones, volumetría, riesgos y requisitos futuros.
- Firmas por versión (Elaboró, Revisó) y firma de Autorizó en la versión vigente.
- Anexos (metadato) con referencia al object storage vía `StoragePort`; el binario no se guarda en Oracle.
- Catálogos configurables con datos semilla: tipo de cambio y cargos por rol.
- Campos dinámicos adicionales por tipo de cambio (columna JSON con `CHECK (... IS JSON)`).
- Migración Alembic que crea el esquema y siembra los catálogos; `downgrade()` reversible.
- Puertos de repositorio (capa `application`) y adaptadores SQLAlchemy con mappers de/para el dominio (capa `infrastructure`).
- Pruebas de dominio, de repositorio y de integración (Testcontainers/Oracle).

### No incluye
- Casos de uso de negocio y endpoints HTTP (SPEC-003).
- Pantallas del wizard y estados de UI (SPEC-004).
- Reglas de validación de negocio de campos y transiciones ejecutables (SPEC-005).
- Asistencia IA real (SPEC-006): solo se reserva la columna JSON y la marca `IA_HABILITADA` no se implementa aquí.
- Generación DOCX/PDF y etiquetado de plantilla (SPEC-007).
- Autenticación JWT, tabla de usuarios/roles, auditoría funcional sobre `SYS_AUDITORIA` (SPEC-008).
- Firma electrónica y flujo de aprobación automático (ADR-005).

## Requisitos funcionales
- RF-01. El dominio modela `Requerimiento` como contenedor estable (folio, estado, puntero a versión vigente) y `VersionRequerimiento` como contenido congelable.
- RF-02. Un requerimiento tiene folio único; el ticket mostrado se compone como `T#` + folio.
- RF-03. Cada versión de un requerimiento tiene número secuencial (1..N) y versión documental; existe como máximo una versión de trabajo (no congelada) por requerimiento, que es la vigente mientras el estado es `BORRADOR`.
- RF-04. Al congelar una versión se aplica copy-on-write: la siguiente versión de trabajo copia únicamente los elementos con `ACTIVO='S'`, preservando `ORDEN`.
- RF-05. Las colecciones (objetivos, consideraciones, beneficios, restricciones, volumetría, riesgos, requisitos futuros) se almacenan como elementos independientes con identificador, orden, contenido y estado activo/eliminado; nunca como un bloque de texto.
- RF-06. Los beneficios distinguen cualitativos y cuantitativos en una misma colección mediante un discriminador de tipo.
- RF-07. La versión admite campos dinámicos adicionales según el tipo de cambio, almacenados en una columna JSON.
- RF-08. Las firmas Elaboró y Revisó se registran por versión; Autorizó se registra únicamente en la versión vigente.
- RF-09. El catálogo de tipo de cambio y el catálogo de cargos por rol se persisten con datos semilla; el cargo de cada firma proviene del catálogo con valor editable en el requerimiento.
- RF-10. Los anexos se registran como metadato (nombre, tipo, orden, leyenda) más una clave de objeto; el contenido se resuelve vía `StoragePort`.
- RF-11. La migración Alembic `0002_modelo_requerimiento` crea las tablas, restricciones, claves foráneas e índices, y siembra los catálogos; `downgrade()` las elimina.
- RF-12. Los puertos de repositorio permiten crear, leer, actualizar y listar el agregado y sus catálogos, y no exponen tipos de SQLAlchemy al dominio.

## Criterios de aceptacion
- CA-01. Dado un Oracle disponible, cuando se ejecuta `alembic upgrade head`, entonces existen `REQ_REQUERIMIENTO`, `REQ_VERSION`, las colecciones, `REQ_ANEXO`, `REQ_FIRMA`, `REQ_TIPO_CAMBIO` y `REQ_CARGO` con sus columnas de auditoría; `downgrade()` las elimina sin residuos.
- CA-02. Dado el esquema migrado, cuando se consultan los catálogos, entonces existen los seis tipos de cambio (nueva funcionalidad, corrección, reporte, integración, base de datos, mejora técnica) y los cargos por rol con su valor predeterminado.
- CA-03. Dado un repositorio de requerimientos, cuando se guarda y se recupera un requerimiento con su versión, colecciones, firmas y anexos, entonces los datos coinciden con lo persistido (ida y vuelta).
- CA-04. Dado un folio existente, cuando se intenta crear otro requerimiento con el mismo folio, entonces el repositorio rechaza la operación por violación de unicidad.
- CA-05. Dada una versión con elementos activos e inactivos, cuando se congela y se crea la siguiente versión de trabajo, entonces la nueva versión contiene solo los elementos activos y conserva su orden.
- CA-06. Dado el dominio, cuando se solicita una transición de estado no permitida, entonces el dominio la rechaza.
- CA-07. Dada una versión no vigente, cuando se intenta registrar Autorizó sobre ella, entonces el dominio lo rechaza.
- CA-08. Dado un valor de campos dinámicos inválido, cuando se persiste, entonces la restricción `IS JSON` lo rechaza.
- CA-09. Dado el árbol del repositorio, cuando se ejecutan `ruff check .`, `mypy --strict backend/app` y `pytest`, entonces no hay errores.

## Reglas de negocio y validaciones
- Nombres Oracle en MAYÚSCULAS, tablas en singular con prefijo de módulo `REQ`, PK `ID` identidad (convenciones.md).
- Auditoría obligatoria en toda tabla: `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY`.
- Colecciones ordenadas: `ORDEN` (NUMBER) y `ACTIVO` (CHAR(1) con CHECK `'S'`/`'N'`).
- Estados: cadena principal `BORRADOR -> EN_REVISION -> VALIDADO -> APROBADO -> GENERADO`; retrocesos permitidos `EN_REVISION -> BORRADOR` y `VALIDADO -> EN_REVISION`; `CANCELADO` permitido desde cualquier estado no terminal; `GENERADO` y `CANCELADO` son terminales. El estado vive en el contenedor.
- Firmas: Elaboró/Revisó por versión; Autorizó solo en la versión vigente; cargo desde catálogo con valor por defecto editable.
- Como máximo una versión no congelada por requerimiento.
- El dominio no importa FastAPI, SQLAlchemy, `docxtpl` ni librerías de IA.
- DDL solo mediante Alembic; no se modifica la base manualmente.
- Los binarios de anexos no se guardan en Oracle.

## Datos involucrados (a nivel funcional)

Contenedor:
- `REQ_REQUERIMIENTO`: `ID`, `FOLIO` (único), `ESTADO`, `VERSION_ACTUAL_ID`, auditoría.

Versión:
- `REQ_VERSION`: `ID`, `REQUERIMIENTO_ID`, `NUMERO_VERSION`, `VERSION_DOCUMENTO`, `FECHA_VERSION`, `TITULO`, `TIPO_CAMBIO_ID`, `SISTEMA`, `NECESIDAD_ACTUAL`, `CONTEXTO_DESCRIPCION`, `CONTEXTO_MANEJO_ERRORES`, `USUARIOS_PERMISOS`, `REQUISITOS_FUTUROS_APLICA`, `REQUISITOS_FUTUROS_TEXTO`, `CAMPOS_DINAMICOS` (JSON), `CONGELADA`, auditoría.

Colecciones (id, versión, orden, contenido, activo):
- `REQ_OBJETIVO`, `REQ_CONSIDERACION`, `REQ_RESTRICCION`, `REQ_VOLUMETRIA`, `REQ_RIESGO`, `REQ_REQUISITO_FUTURO`.
- `REQ_BENEFICIO`: igual, más `TIPO` (`CUALITATIVO`/`CUANTITATIVO`).

Anexos, firmas y catálogos:
- `REQ_ANEXO`: `ID`, `VERSION_ID`, `ORDEN`, `NOMBRE`, `TIPO_MIME`, `STORAGE_KEY`, `LEYENDA`, `ACTIVO`, auditoría.
- `REQ_FIRMA`: `ID`, `VERSION_ID`, `ROL` (`ELABORO`/`REVISO`/`AUTORIZO`), `NOMBRE`, `CARGO`, `CARGO_ID`, auditoría.
- `REQ_TIPO_CAMBIO`: `ID`, `CODIGO`, `NOMBRE`, `ACTIVO`, auditoría.
- `REQ_CARGO`: `ID`, `ROL`, `NOMBRE`, `PREDETERMINADO`, `ACTIVO`, auditoría.

## Requisitos no funcionales aplicables
- Tipado completo con `ruff` y `mypy --strict` sin errores.
- Separación hexagonal estricta: dominio puro, puertos en `application`, SQLAlchemy solo en `infrastructure`.
- Migración Alembic reversible y ejecutable contra `oracle-free` (dev) y Oracle en CI.
- Pruebas de integración con Testcontainers/Oracle; pruebas de dominio sin base de datos.

## Decisiones tomadas
- **Sí:** el contenedor guarda solo identidad estable (folio), estado y puntero a versión vigente; todo el contenido vive por versión.
- **Sí:** versionado por contenedor + versión congelada; copy-on-write al congelar.
- **Sí:** el estado del ciclo de vida vive en el requerimiento; las firmas se registran por versión.
- **Sí:** catálogos de tipo de cambio y cargos con datos semilla en la migración.
- **Sí:** `Sistema` como texto libre (no catálogo).
- **Sí:** anexos como metadato + `StoragePort`; binario fuera de Oracle.
- **Sí:** requisitos futuros como bandera `aplica` + texto + colección.
- **Sí:** beneficios en una sola tabla con discriminador de tipo.
- **Sí:** `FOLIO` numérico (`NUMBER(19)`), único; el ticket mostrado es `T#` + folio (P-03 del mapeo del machote).
- **Sí:** `CAMPOS_DINAMICOS` como `CLOB` (SQLAlchemy `Text`) con `CHECK (CAMPOS_DINAMICOS IS JSON)`, coherente con `SYS_AUDITORIA.DETALLE` de SPEC-001.
- **Sí:** las columnas de auditoría `CREATED_AT`/`UPDATED_AT` se llenan con fecha/hora del sistema y `CREATED_BY`/`UPDATED_BY` con el actor de sistema `SYSTEM` hasta que SPEC-008 provea el actor real.
- **No:** usuarios/roles, JWT y auditoría funcional (SPEC-008).
- **No:** casos de uso de negocio y endpoints (SPEC-003).
- **No:** validaciones de negocio ejecutables y generación DOCX/PDF (SPEC-005/007).

## Riesgos identificados

| Riesgo | Mitigacion |
|---|---|
| El contenedor Oracle en CI/dev es lento o inestable para Testcontainers | Healthcheck y espera activa; reutilizar el mecanismo de SPEC-001 |
| Columna JSON/`IS JSON` con diferencias entre versiones de Oracle | Verificar en `oracle-free` la variante de columna (CLOB/VARCHAR2) con `CHECK (... IS JSON)` |
| El copy-on-write introduce bugs de orden o de elementos inactivos | Prueba dedicada de congelado y comparación de conjuntos activos/orden |
| Concurrencia al crear versiones o editar la versión de trabajo | Control de una sola versión no congelada por requerimiento; definir bloqueo optimista en el plan |
| Divergencia entre nombres de dominio y columnas | Mappers explícitos y pruebas de ida y vuelta |

## Preguntas resueltas (2026-10-13)
- **FOLIO:** numérico (`NUMBER(19,0)`), único; el prefijo `T#` es fijo y solo de presentación.
- **Columna JSON:** `CAMPOS_DINAMICOS` como `CLOB` con `CHECK (CAMPOS_DINAMICOS IS JSON)`; mismo criterio que `SYS_AUDITORIA.DETALLE` (SPEC-001).
- **Auditoría:** `CREATED_AT`/`UPDATED_AT` con fecha/hora del sistema y `CREATED_BY`/`UPDATED_BY` = `SYSTEM` en los adaptadores de repositorio hasta SPEC-008.

## Que **no** esta en esta spec
- Casos de uso y API de requerimientos y borradores.
- Wizard, pantallas y estados de UI.
- Validaciones de negocio y transiciones ejecutables.
- IA, generación DOCX/PDF y firma electrónica.
- Usuarios, roles, JWT y auditoría funcional.

Cada uno de estos temas, si se aborda, va en su propia spec.
