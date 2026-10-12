# SPEC-001 - Fundaciones del proyecto

- Estado: Aprobada
- Fecha: 2026-10-12
- Documentos aplicables: `AGENTS.md`, `doc/architecture/adr/001-backend-python-fastapi.md`, `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/003-autenticacion.md`, `doc/architecture/adr/006-almacenamiento-objetos-dev.md`, `doc/development/convenciones.md`, `.env.example`
- Depende de: ninguna

## Contexto y objetivo
Dejar un monorepo ejecutable con backend FastAPI hexagonal, frontend Vite + React + TypeScript + Tailwind y `docker compose` (backend, frontend, Oracle de desarrollo y un object store S3 de desarrollo RustFS) con Alembic, calidad (`ruff`/`mypy`/`pytest`) e integracion continua, como base para el resto de specs.

## Alcance

### Incluye
- Estructura hexagonal del backend: `backend/app/{domain,application,infrastructure,api}`.
- Aplicacion FastAPI con endpoint de salud y de version.
- Configuracion centralizada por variables de entorno (Pydantic Settings) segun `.env.example`.
- SQLAlchemy 2.x con `python-oracledb` (thin) y Alembic; migracion base sobre Oracle.
- Imagen Docker del backend con Python 3.12, LibreOffice headless y las fuentes del machote.
- Imagen Docker del frontend y build de produccion (Vite).
- `docker-compose.yml` con backend, frontend, Oracle (dev) y un object store S3 de desarrollo (RustFS, perfil opcional `objectstore`).
- Scaffold del frontend (Vite + React + TypeScript + Tailwind) con los tokens de `doc/ui/design/STITCH_DESIGN.md` y un layout base.
- Calidad: `ruff`, `mypy --strict`, `pytest` con Testcontainers y Playwright (configuracion base).
- Control de versiones (`git init`) y pipeline de CI en GitHub Actions.

### No incluye
- Modelo de dominio, entidades y tablas del requerimiento (va en SPEC-002).
- Endpoints de gestion de requerimientos y borradores (SPEC-003).
- Pantallas del wizard y sus estados (SPEC-004).
- Reglas de validacion de negocio del requerimiento (SPEC-005).
- Asistencia IA real (SPEC-006): en esta spec solo se fija `AI_PROVIDER=none`.
- Generacion DOCX/PDF y la plantilla `docxtpl` (SPEC-007).
- Autenticacion real con JWT, roles y auditoria funcional (SPEC-008).

## Requisitos funcionales
- RF-01. El backend expone `GET /health` y responde `200` con el estado de la aplicacion y de la conexion a la base de datos.
- RF-02. El backend expone `GET /version` con la version de la aplicacion.
- RF-03. La configuracion se carga exclusivamente desde variables de entorno; no hay secretos en el codigo ni en las imagenes.
- RF-04. Alembic aplica la migracion base contra Oracle y crea la tabla `SYS_AUDITORIA`.
- RF-05. `docker compose up` levanta backend, frontend y Oracle (dev) y el backend responde `GET /health`; con `docker compose --profile objectstore up` se levanta ademas el object store S3 de desarrollo (RustFS).
- RF-06. El frontend sirve una pagina base que usa los tokens de diseno institucional.
- RF-07. La CI ejecuta `ruff`, `mypy --strict` y `pytest` en cada push y pull request.

## Criterios de aceptacion
- CA-01. Dado el backend en ejecucion, cuando se invoca `GET /health`, entonces responde `200` con estado de aplicacion y base de datos en `ok`.
- CA-02. Dado el backend en ejecucion, cuando se invoca `GET /version`, entonces responde `200` con la version de la aplicacion.
- CA-03. Dado `docker compose up`, cuando los servicios terminan de iniciar, entonces `GET /health` responde `200` y la base de datos reporta `ok`; con `--profile objectstore`, el object store S3 de desarrollo (RustFS) queda `healthy`.
- CA-04. Dado un Oracle disponible, cuando se ejecuta `alembic upgrade head`, entonces la tabla `SYS_AUDITORIA` existe con sus columnas de auditoria.
- CA-05. Dado el arbol del repositorio, cuando se ejecuta `ruff check .`, entonces no hay errores.
- CA-06. Dado el arbol del repositorio, cuando se ejecuta `mypy --strict backend/app`, entonces no hay errores.
- CA-07. Dado un pull request, cuando corre la CI, entonces ejecuta lint, tipos y pruebas y falla si alguno no pasa.
- CA-08. Dado el frontend en desarrollo, cuando se abre en el navegador, entonces muestra el layout base con la tipografia y la paleta institucional.

## Reglas de negocio y validaciones
- Los nombres de tablas y columnas Oracle siguen `doc/development/convenciones.md` (mayusculas, tablas en singular con prefijo de modulo, PK `ID` identidad, columnas de auditoria).
- Las migraciones se aplican solo con Alembic; no se modifican la base ni los DDL manualmente.
- Las variables de entorno se documentan en `.env.example`; los valores reales y el wallet de Oracle quedan fuera de git y de las imagenes.
- El backend opera con `AI_PROVIDER=none` por defecto.

## Datos involucrados (a nivel funcional)
- Configuracion: `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`, `ORACLE_WALLET_DIR`, `STORAGE_BACKEND`, `AUTH_PROVIDER`, `JWT_SECRET`, `AI_PROVIDER`.
- Tabla base `SYS_AUDITORIA` (fundacional; su uso funcional se detalla en SPEC-008): `ID`, `ENTIDAD`, `ENTIDAD_ID`, `ACCION`, `ACTOR`, `DETALLE` (JSON), `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY`.

## Requisitos no funcionales aplicables
- Tipado completo con `ruff` y `mypy --strict` sin errores.
- La misma imagen de backend se usa en dev y prod; solo cambia la configuracion por entorno.
- `docker compose up` levanta el entorno completo de desarrollo.
- Guardado y conexion resilientes: `GET /health` diferencia el estado de la app del estado de la base de datos.

## Decisiones tomadas
- **Si:** SPEC-001 se limita a infraestructura y una migracion base; el modelo de dominio va en SPEC-002.
- **Si:** scaffold minimo del frontend ahora (layout y tokens); las pantallas reales van en SPEC-004.
- **Si:** la imagen del backend incluye LibreOffice headless y las fuentes del machote desde el inicio, para habilitar el spike DOCX/PDF sin rehacer la imagen.
- **Si:** `docker compose` en desarrollo incluye Oracle (`oracle-free`) y un object store S3 (RustFS) bajo el perfil `objectstore`; storage local por defecto y object store opcional.
- **Si:** `git init` y CI en GitHub Actions con lint, tipos y pruebas.
- **No:** firma electronica, OIDC y auditoria funcional en esta spec (dependen de SPEC-008).

## Riesgos identificados

| Riesgo | Mitigacion |
|---|---|
| El contenedor Oracle tarda en estar disponible y hace lento o inestable el desarrollo y la CI | Healthcheck y espera activa en compose; en CI usar imagen de Oracle compatible con Testcontainers y cachear capas |
| El tamano de la imagen por LibreOffice y fuentes | Multietapa y limpieza de paquetes; instalar solo lo necesario para la conversion headless |
| Testcontainers en Windows (Docker Desktop) | Documentar requisitos y usar el mismo mecanismo en CI Linux |
| Divergencia entre tokens de `STITCH_DESIGN.md` y el scaffold | Definir los tokens una sola vez en Tailwind y consumirlos desde ahi |

## Preguntas abiertas
- Version/tag exacta de la imagen Oracle de desarrollo (`oracle-free` u otra compatible).
- Conjunto exacto de fuentes a instalar en la imagen del backend.
- Proveedor de CI confirmado (se asume GitHub Actions; el repo aun no es git).

## Que **no** esta en esta spec
- Modelo de dominio y tablas del requerimiento.
- API de requerimientos, borradores y estados.
- Wizard y pantallas de captura.
- Validaciones de negocio, IA real y generacion DOCX/PDF.
- Autenticacion con JWT, roles y auditoria funcional.

Cada uno de estos temas, si se aborda, va en su propia spec.
