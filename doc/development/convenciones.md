# Convenciones de desarrollo

## Python
- Python 3.12, tipado completo, `ruff` + `mypy --strict` en CI.
- Sin logica de negocio en routers; casos de uso en `application`.

## SQL Oracle
- Nombres en MAYUSCULAS con guion bajo: tablas en singular con prefijo de modulo (ej. `REQ_REQUERIMIENTO`).
- PK: `ID` tipo `NUMBER GENERATED ALWAYS AS IDENTITY`; FK `<TABLA>_ID`.
- Auditoria en toda tabla: `CREATED_AT`, `CREATED_BY`, `UPDATED_AT`, `UPDATED_BY`.
- Colecciones ordenadas: columnas `ORDEN` (NUMBER) y `ACTIVO` (CHAR(1) con CHECK 'S'/'N').
- Campos dinamicos por tipo de cambio: columna JSON con `CHECK (... IS JSON)`.
- DDL solo con Alembic; nunca cambios manuales en BD.

## Docker
- Imagenes sin secretos; configuracion por `.env` (ver `.env.example`).
- `docker compose up` debe levantar el entorno completo de desarrollo.

## Git
- Una rama por spec: `spec/SPEC-NNN-nombre`. Commits con prefijo `SPEC-NNN:`.
