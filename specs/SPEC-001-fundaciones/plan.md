# Plan tecnico - SPEC-001

> Documentos aplicables: `AGENTS.md`, `doc/architecture/adr/001-backend-python-fastapi.md`,
> `doc/architecture/adr/002-arquitectura-hexagonal-y-docker.md`, `doc/architecture/adr/003-autenticacion.md`,
> `doc/development/convenciones.md`, `doc/ui/design/STITCH_DESIGN.md`, `.env.example`.
> Esta spec es de infraestructura: no incluye modelo de dominio, wizard, IA real, DOCX/PDF ni autenticacion funcional.

## Enfoque

Monorepo unico con `backend/`, `frontend/`, `docker/`, `specs/` y `doc/` (ya existente). El objetivo es un
esqueleto **ejecutable y verificable** que sirva de base:

1. Backend FastAPI con arquitectura hexagonal (`domain`, `application`, `infrastructure`, `api`). En esta
   spec `domain` y `application` son minimos (caso de uso de salud y version); se crean las carpetas y el
   cableado para que las specs siguientes solo anadan modulos.
2. Configuracion centralizada con Pydantic Settings (v2) leida exclusivamente de variables de entorno.
3. Persistencia Oracle via SQLAlchemy 2.x + `python-oracledb` modo thin, con Alembic y una migracion base
   que crea `SYS_AUDITORIA`.
4. `docker compose up` levanta backend, frontend, Oracle dev (`oracle-free`) y MinIO dev, con healthchecks.
5. Frontend Vite + React + TypeScript + Tailwind con los tokens de `STITCH_DESIGN.md` definidos una sola vez
   y un layout base.
6. Calidad (`ruff`, `mypy --strict`, `pytest`) y CI en GitHub Actions.

Principio rector: la **misma imagen** de backend se usa en dev y prod; solo cambia la configuracion por
entorno (`AI_PROVIDER=none` por defecto). Ningun secreto ni wallet entra en git ni en las imagenes.

## Modelo de datos Oracle (tablas, claves, indices) y migraciones Alembic

Unica tabla de esta spec (fundacional; su uso funcional llega en SPEC-008):

`SYS_AUDITORIA` (prefijo de modulo `SYS`, singular, MAYUSCULAS segun `doc/development/convenciones.md`):

| Columna | Tipo | Notas |
|---|---|---|
| `ID` | `NUMBER GENERATED ALWAYS AS IDENTITY` | PK |
| `ENTIDAD` | `VARCHAR2(100)` | NOT NULL; entidad afectada |
| `ENTIDAD_ID` | `NUMBER` | id de la fila afectada (puede ser NULL) |
| `ACCION` | `VARCHAR2(50)` | NOT NULL; accion auditada |
| `ACTOR` | `VARCHAR2(100)` | usuario/actor |
| `DETALLE` | JSON (`CLOB`/`VARCHAR2` con `CHECK (DETALLE IS JSON)`) | detalle dinamico |
| `CREATED_AT` | `TIMESTAMP` | auditoria |
| `CREATED_BY` | `VARCHAR2(100)` | auditoria |
| `UPDATED_AT` | `TIMESTAMP` | auditoria |
| `UPDATED_BY` | `VARCHAR2(100)` | auditoria |

- PK: `SYS_AUDITORIA_PK (ID)`.
- Indice auxiliar de consulta por entidad: `SYS_AUDITORIA_ENTIDAD_IX (ENTIDAD, ENTIDAD_ID)`.
- Migraciones **solo** via Alembic (nunca DDL manual). `alembic/env.py` construye la URL a partir de
  Pydantic Settings (`ORACLE_USER/PASSWORD/DSN`, `ORACLE_WALLET_DIR`), en modo thin.
- Revision base `0001_base`: `upgrade()` crea `SYS_AUDITORIA`; `downgrade()` la elimina (permite tests
  de ida y vuelta).

## Dominio y casos de uso

- `domain`: sin dependencias de FastAPI/SQLAlchemy/Oracle. En esta spec contiene como maximo el resultado
  puro de salud (`ApplicationStatus`) si se necesita; no hay entidades de negocio todavia.
- `application`:
  - Puerto `DatabaseHealthPort` con `check() -> DatabaseStatus`.
  - Caso de uso `CheckHealthUseCase` que compone el estado de la app (`ok`) con el del puerto de BD,
    devolviendo un `HealthReport { app: str, database: str }`. No lanza excepcion si la BD falla: marca
    `database` como `down`/`degraded` (RF "guardado y conexion resilientes").
  - Caso de uso `GetVersionUseCase` que devuelve la version de la aplicacion leida de Settings.

## Puertos y adaptadores afectados

- Puerto `DatabaseHealthPort` (application) → Adaptador `SqlAlchemyDatabaseHealthAdapter`
  (infrastructure) que ejecuta `SELECT 1 FROM DUAL` sobre un engine SQLAlchemy con `python-oracledb` thin.
- Configuracion: `infrastructure/config.py` con `Settings(BaseSettings)` (Pydantic v2), leyendo
  `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`, `ORACLE_WALLET_DIR`, `STORAGE_BACKEND`, `AUTH_PROVIDER`,
  `JWT_SECRET`, `AI_PROVIDER` (default `none`) y `APP_VERSION`. Sin valores reales en el repo.
- Se crean las carpetas/paquetes para los puertos futuros (`StoragePort`, `AiAssistantPort`,
  `AuthProvider`, `DocumentRenderer`) como marcadores vacios documentados, **sin implementacion** en esta
  spec (evita inventar comportamiento; llegan en SPEC-006/007/008).

## API (endpoints, contratos, errores)

- `GET /health` → `200` con `{ "status": "ok", "database": "ok" }`. Si la BD no responde, sigue `200` con
  `"database": "down"` (el estado de la app y el de la BD se informan por separado). Si la app no puede
  componer la respuesta, `503`.
- `GET /version` → `200` con `{ "version": "<APP_VERSION>" }`.
- Esquemas Pydantic v2 (`HealthResponse`, `VersionResponse`) en `api/schemas`.
- `main.py` con `create_app()` (factory) que registra los routers. Sin logica de negocio en routers: solo
  invocan los casos de uso.

## Frontend (pantallas, componentes, estado)

- Scaffold Vite + React + TypeScript + Tailwind.
- Tokens de `doc/ui/design/STITCH_DESIGN.md` definidos **una sola vez** en `tailwind.config`/CSS
  (paleta institucional, tipografia Inter, radios, espaciado). Se consume desde ahi; no se duplican.
- Componente `AppLayout` con cabecera institucional (logo/titulo) y area de contenido; tipografia Inter y
  paleta `#0f4c81`/`#f8fafc` como base (CA-08).
- Pagina base que consulta `GET /version` (proxy Vite hacia el backend en dev) y muestra la version y un
  indicador de salud; es solo scaffolding, las pantallas reales van en SPEC-004.
- Estado: sin gestor global en esta spec (solo estado local del componente).

## Docker / configuracion

- `docker/backend.Dockerfile` multietapa (`python:3.12-slim`): instala dependencias, y en la etapa final
  LibreOffice headless + fuentes necesarias para la conversion. Sin secretos ni wallet en la imagen.
- `docker/frontend.Dockerfile` multietapa: build Vite (Node) + servido estatico (nginx).
- `docker-compose.yml` servicios base: `backend`, `frontend`, `oracle` (dev, `oracle-free`). Object store
  S3 de desarrollo (RustFS, `rustfs/rustfs:1.0.0`) bajo el perfil `objectstore` (ADR-006).
  Healthchecks y `depends_on: condition: service_healthy`; espera activa a Oracle. Variables desde
  `.env` (plantilla `.env.example`). Wallet de Autonomous DB como volumen/secret (nunca en la imagen).
- `.gitignore` excluye `.env`, wallet y artefactos; `git init` (ya inicializado) y README raiz.

## Estrategia de pruebas

- **Unitarias** (`pytest`): `CheckHealthUseCase` con un fake de `DatabaseHealthPort` (BD ok y BD caida) y
  `GetVersionUseCase`.
- **Integracion** (`pytest` + Testcontainers): levanta Oracle, ejecuta `alembic upgrade head` y verifica
  que `SYS_AUDITORIA` existe con sus columnas. En Windows/Docker Desktop se documentan requisitos; en CI
  se usa el mismo mecanismo sobre Linux.
- **API**: tests de `GET /health` y `GET /version` con el puerto de BD falso (sin Oracle real).
- **E2E** (`Playwright`): configuracion base y smoke test del layout base (CA-08).
- **CI** (GitHub Actions) en push y PR: job `lint` (`ruff check .`), job `types` (`mypy --strict
  backend/app`), job `tests` (pytest con Oracle). Falla si cualquiera no pasa.

## Riesgos y decisiones (ADRs relacionados)

- ADR-001 (Python + FastAPI), ADR-002 (hexagonal + Docker), ADR-003 (autenticacion: en esta spec solo se
  fija `AUTH_PROVIDER=local_jwt` como default; no hay JWT funcional).
- **Preguntas abiertas** (heredadas de la spec, no se deciden en silencio):
  - Version/tag exacta de la imagen Oracle de desarrollo (`oracle-free` u otra compatible).
  - Conjunto exacto de fuentes a instalar en la imagen del backend (las del machote).
  - Proveedor de CI asumido GitHub Actions (el repo no era git al escribir la spec).
- Riesgo: el contenedor Oracle tarda en estar disponible → mitigacion: healthcheck + espera activa en
  compose y en CI.
- Riesgo: tamano de la imagen por LibreOffice/fuentes → mitigacion: multietapa y limpieza.
- Riesgo: divergencia de tokens entre `STITCH_DESIGN.md` y el scaffold → mitigacion: definir los tokens
  una sola vez en Tailwind.
