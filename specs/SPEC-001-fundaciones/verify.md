# Verificacion - SPEC-001 (Fundaciones del proyecto)

- Spec: `spec.md` (estado: Aprobada)
- Fecha de verificacion: 2026-10-12
- Rama: `spec/SPEC-001-fundaciones`
- Entorno de evidencia: Windows + Docker Desktop 29.8.2; Python 3.12.15 (contenedor `python:3.12-slim`, paridad con CI); Node v24.21 / npm 11.19.

## Resumen

| Resultado | Cantidad | Criterios |
|---|---|---|
| Cumple | 7 | CA-01, CA-02, CA-03, CA-04, CA-05, CA-06, CA-08 |
| Parcial | 1 | CA-07 |
| No cumple | 0 | - |

**Veredicto: la spec queda cumplida en el entorno local.** H-01 y H-02 corregidos y verificados end-to-end. Unica salvedad: CA-07 queda **Parcial** porque no hay `git remote` y la CI nunca se ha ejecutado en GitHub (evidencia solo por inspeccion).

## Matriz de criterios de aceptacion

| Criterio | Resultado | Evidencia |
|---|---|---|
| CA-01 | Cumple | `GET /health` responde `200` con `{status, database}`; en `docker compose` (oracle `healthy` + backend) devuelve `body={"status":"ok","database":"ok"}` tras corregir H-01. Contrato y resiliencia cubiertos por `tests/api/test_health.py` y `tests/application/test_check_health.py`. |
| CA-02 | Cumple | `GET /version` -> `200`, `body={"version":"0.1.0"}` (compose, `http://localhost:8000/version`). Test `tests/api/test_version.py::test_version_returns_configured_version` en verde. |
| CA-03 | Cumple | `docker compose up` levanta `oracle`, `backend`, `frontend` (ambos `healthy`) y `GET /health` -> `{"status":"ok","database":"ok"}`. Con `docker compose --profile objectstore up` se suma `rustfs` (`healthy`) y `GET http://localhost:9000/minio/health/ready` -> `200` (`ready:true`, storage/iam/lock `connected`). Ver H-02 y ADR-006. |
| CA-04 | Cumple | `pytest tests/integration -m integration` (Testcontainers `gvenzl/oracle-free:slim`): `4 passed in 10.47s` (`test_upgrade_creates_sys_auditoria`, `test_downgrade_drops_sys_auditoria`, `test_build_database_url_targets_service_not_sid`, `test_engine_built_from_ezeconnect_dsn_connects`). Revision `0001_base` crea `SYS_AUDITORIA` con PK, indice `SYS_AUDITORIA_ENTIDAD_IX`, columnas de auditoria y `CHECK (DETALLE IS JSON)`. |
| CA-05 | Cumple | `ruff check .` (raiz del repo, como CI) -> `All checks passed!` en `python:3.12-slim`. |
| CA-06 | Cumple | `mypy --strict backend/app` (raiz del repo, como CI) -> `Success: no issues found in 23 source files`. |
| CA-07 | Parcial | `.github/workflows/ci.yml` define jobs `lint` (`ruff check .`), `types` (`mypy --strict backend/app`) y `tests` (`pytest -m "integration or not integration"`) disparados en push (`branches: ["**"]`) y `pull_request`; por defecto fallan si el paso falla. **No hay `git remote`**, la CI nunca se ha ejecutado en GitHub: cumplimiento verificado por inspeccion, sin evidencia de ejecucion. |
| CA-08 | Cumple | `npm run build` (tsc -b + vite build) OK; Playwright `e2e/layout.spec.ts` -> `1 passed (15.4s)` verificando tipografia Inter, fondo `rgb(248, 250, 252)` y badge `rgb(15, 76, 129)`. Tokens definidos una sola vez en `frontend/src/index.css` (`@theme`). |

### Comandos ejecutados (evidencia reproducible)

```powershell
# Calidad + pruebas unitarias/API (Python 3.12, paridad CI)
docker run --rm -v "<repo>:/src" -w /src python:3.12-slim bash -lc "pip install -q -e './backend[dev]'; ruff check .; mypy --strict backend/app; cd backend && python -m pytest -v"
# -> All checks passed! | Success: no issues found in 23 source files | 13 passed, 4 deselected

# Integracion Oracle (Testcontainers, socket del daemon del host)
docker run --rm -v "<repo>:/src" -v "//var/run/docker.sock:/var/run/docker.sock" -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal -w /src/backend python:3.12-slim bash -lc "pip install -q -e '.[dev]'; python -m pytest tests/integration -v -m integration"
# -> 4 passed in 10.47s

# Frontend
npm run build          # tsc -b && vite build -> ok
npx playwright install chromium; npm run test:e2e   # -> 1 passed

# Compose
docker compose config --quiet        # -> valido
docker compose config --services     # -> oracle, backend, frontend (rustfs solo con --profile objectstore)
docker compose build                 # backend image ok
docker compose up -d                 # -> oracle+backend+frontend; GET /health -> {"status":"ok","database":"ok"}
docker compose --profile objectstore up -d          # -> rustfs healthy
# GET http://localhost:9000/minio/health/ready -> 200 {"ready":true,...}
```

## Requisitos funcionales (trazabilidad)

| RF | Estado | Evidencia |
|---|---|---|
| RF-01 | Cumple | `GET /health` -> `200` con BD `ok` (ver CA-01). |
| RF-02 | Cumple | `GET /version` -> `{"version":"0.1.0"}`. |
| RF-03 | Cumple | `Settings` usa `SecretStr`; `.gitignore`/`.dockerignore` excluyen `.env`/`wallet/`; `.env` no esta trackeado (`git ls-files` vacio); imagen del backend sin `cwallet.sso` ni `.env` (`docker run ... find / -name cwallet.sso` sin resultados). |
| RF-04 | Cumple | Ver CA-04. |
| RF-05 | Cumple | Ver CA-03. |
| RF-06 | Cumple | Ver CA-08. |
| RF-07 | Parcial | Ver CA-07. |

## Hallazgos

### H-01 (CORREGIDO) - DSN Oracle interpretado como SID; la app nunca conectaba a la BD
`build_database_url` construia `oracle+oracledb://user:pass@host:port/SERVICE`, y SQLAlchemy 2.1.4 interpreta el segmento posterior a `:port/` como **SID**, no como service name:

```
oracledb.exceptions.OperationalError: DPY-6003: SID "FREEPDB1" is not registered with the listener ... (Similar to ORA-12505)
```

Evidencia de contraste (contenedor `backend`): `oracle+oracledb://...@oracle:1521/FREEPDB1` -> `FAIL`; `...@oracle:1521/?service_name=FREEPDB1` -> `OK -> 1`; `oracledb.connect(dsn='oracle:1521/FREEPDB1')` -> `connected`.

**Correccion aplicada** (`backend/app/infrastructure/database.py`): `_split_oracle_dsn` divide el DSN EZConnect (`host[:port][/servicio]`) y `build_database_url` emite `?service_name=<servicio>` (con `quote_plus`). Pruebas agregadas:

- Unitarias `backend/tests/infrastructure/test_database.py` (4 casos: con/sin puerto, sin servicio, escapado de credenciales).
- Integracion `backend/tests/integration/test_database_engine.py` construye el engine con `create_db_engine(build_database_url(settings))` desde un DSN EZConnect real y ejecuta `SELECT 1 FROM DUAL` (fallaria con el codigo anterior). Se movio el contenedor Oracle a un fixture `session` compartido (`tests/integration/conftest.py`).

Verificacion end-to-end: `docker compose up -d oracle backend` -> ambos `healthy` y `GET /health` -> `{"status":"ok","database":"ok"}`. CA-01/RF-01 pasan a **Cumple**.

### H-02 (RESUELTO) - Imagen MinIO inexistente; reemplazada por RustFS bajo perfil
El servicio usaba `minio/minio:latest`, retirado de Docker Hub (MinIO ceso su desarrollo el 25-abr-2026; su imagen tampoco existe en Quay). `docker compose up` abortaba con `pull access denied for minio/minio`.

**Decision (ADR-006)**: reemplazar por **RustFS** (`rustfs/rustfs:1.0.0`, Apache-2.0, S3-compatible, con rutas de salud compatibles con MinIO), declarado bajo el **perfil de Compose `objectstore`**; renombrar `STORAGE_BACKEND` `minio` → `s3`. Verificacion: `docker compose up -d` levanta solo `oracle+backend+frontend` y `/health` = `ok/ok`; `docker compose --profile objectstore up -d` deja `rustfs` `healthy` con `/minio/health/ready` -> `200`. CA-03/RF-05 pasan a **Cumple**.

### H-03 (menor) - CI sin evidencia de ejecucion
Sin `git remote`, el pipeline nunca corrio en GitHub. CA-07 queda verificado solo por inspeccion.

### H-04 (menor) - Desalineacion de toolchain local
El Python global del entorno es 3.15 y no hay venv del proyecto, por lo que `ruff`/`mypy`/`pytest` no estan disponibles fuera de contenedor. Toda la evidencia se reprodujo en `python:3.12-slim` (paridad con el stack objetivo). No bloquea, pero conviene documentar el flujo de desarrollo.

## Deuda tecnica registrada

1. ~~Corregir `build_database_url` para emitir `?service_name=<svc>`~~ -> **resuelto** (H-01) con pruebas unitarias e integracion.
2. ~~Reemplazar/parametrizar `minio/minio:latest`~~ -> **resuelto** (H-02, ADR-006): RustFS `1.0.0` bajo perfil `objectstore` y `STORAGE_BACKEND` `minio`->`s3`.
3. Versionar/fijar el tag exacto de la imagen Oracle de desarrollo (pregunta abierta de la spec) y el conjunto exacto de fuentes del machote en la imagen del backend.
4. Ejecutar la CI en un remoto para obtener evidencia de CA-07 (y anadir `git remote`).
5. Documentar en `doc/development/` el flujo de entorno local (python 3.12 + venv) para reproducir `ruff`/`mypy`/`pytest`.
6. Configurar endpoint/region/path-style S3 para la app cuando se implemente el `StoragePort` (spec posterior; aqui solo infraestructura).

## Pendientes

- CA-07: ejecucion real de la CI (H-03). No afecta a los criterios verificables en local.
