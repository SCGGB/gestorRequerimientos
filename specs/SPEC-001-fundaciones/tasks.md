# Tareas - SPEC-001

> Ordenadas por dependencia. Cada tarea es atomica y verificable. Las migraciones se aplican solo con
> Alembic; no se escriben DDL a mano. No se implementan puertos de IA/DOCX/autenticacion en esta spec.

- [x] T-01 (CA-05, CA-06) Crear el esqueleto del monorepo (`backend/`, `frontend/`, `docker/`) y los archivos raiz: `.gitignore` (excluye `.env`, wallet y artefactos), README y `git init` si no existe.
- [x] T-02 (CA-05, CA-06) Backend: `backend/pyproject.toml` con dependencias (FastAPI, Pydantic v2, SQLAlchemy 2.x, alembic, python-oracledb) y configuracion de `ruff`, `mypy --strict` y `pytest`; paquetes `backend/app/{domain,application,infrastructure,api}`.
- [x] T-03 (CA-03, RF-03) Configuracion centralizada en `infrastructure/config.py` con `Settings(BaseSettings)` que lee `ORACLE_*`, `STORAGE_BACKEND`, `AUTH_PROVIDER`, `JWT_SECRET`, `AI_PROVIDER` (default `none`) y `APP_VERSION`; sin secretos en el repo; coherente con `.env.example`.
- [x] T-04 (CA-01, CA-06) Caso de uso `CheckHealthUseCase` y puerto `DatabaseHealthPort`; testeable con un fake del puerto (BD ok y BD caida). Ver `plan.md`.
- [x] T-05 (CA-01, RF-01) Adaptador `SqlAlchemyDatabaseHealthAdapter` con engine SQLAlchemy 2.x + `python-oracledb` thin que ejecuta `SELECT 1 FROM DUAL`; `engine`/session factory en `infrastructure`.
- [x] T-06 (CA-02, RF-02) Caso de uso `GetVersionUseCase` que expone `APP_VERSION` desde Settings.
- [x] T-07 (CA-01, CA-02, RF-01, RF-02) API FastAPI: `create_app()`, esquemas Pydantic v2 y routers `GET /health` (200, `{status, database}`) y `GET /version` (200, `{version}`), sin logica de negocio en routers.
- [x] T-08 (CA-04, RF-04) Configurar Alembic (`alembic.ini`, `env.py` leyendo Settings en modo thin) y la revision base `0001_base` que crea `SYS_AUDITORIA` con PK, indice por entidad, columnas de auditoria y `DETALLE` JSON (`CHECK (... IS JSON)`).
- [x] T-09 (CA-04) Test de integracion con Testcontainers Oracle: `alembic upgrade head` y verificacion de la existencia/columnas de `SYS_AUDITORIA` (incluye `downgrade`).
- [x] T-10 (CA-01, CA-02) Tests de API de `GET /health` y `GET /version` con el puerto de BD falso (sin Oracle real).
- [x] T-11 (CA-05, CA-06) Verificar tooling de calidad: `ruff check .` y `mypy --strict backend/app` sin errores.
- [x] T-12 (CA-03, RF-05) `docker/backend.Dockerfile` multietapa (`python:3.12-slim`) con LibreOffice headless y las fuentes del machote; sin secretos ni wallet en la imagen.
- [x] T-13 (CA-03, RF-05) `docker/frontend.Dockerfile` multietapa (build Vite + servido estatico) sin secretos.
- [x] T-14 (CA-03, RF-05) `docker-compose.yml` con `backend`, `frontend`, `oracle` (dev `oracle-free`) y object store S3 de desarrollo (RustFS) bajo el perfil `objectstore` (ADR-006); healthchecks, `depends_on: service_healthy` y espera activa a Oracle; config desde `.env`.
- [x] T-15 (CA-08, RF-06) Scaffold del frontend Vite + React + TS + Tailwind con los tokens de `STITCH_DESIGN.md` definidos una sola vez y el componente `AppLayout` (tipografia Inter y paleta institucional).
- [x] T-16 (CA-08) Pagina base que consulta `GET /version` (proxy Vite al backend en dev) y muestra version y estado de salud.
- [x] T-17 (CA-07, CA-08) Playwright: configuracion base y smoke test del layout base.
- [x] T-18 (CA-07, RF-07) Pipeline GitHub Actions en push y PR con jobs `lint` (`ruff check .`), `types` (`mypy --strict backend/app`) y `tests` (pytest + Oracle); falla si alguno no pasa.
