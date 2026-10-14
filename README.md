# Sistema de Especificacion de Requerimientos de Software

Desarrollo guiado por specs (SDD) con OpenCode.

## Inicio
1. Copia `templates/machote_requerimiento.docx` (el machote institucional).
2. `cp .env.example .env`
3. Abre el proyecto con OpenCode y usa: `/spec`, `/plan`, `/tasks`, `/implement`, `/verify`.

Lee `AGENTS.md` y `doc/README.md`.

## Pruebas del backend

Requiere Python 3.12 (versión objetivo del proyecto; en 3.15 `pyyaml` no tiene wheel).
Desde `backend/`:

- Unitarias (sin Docker): `python -m pytest`
- Integración (Docker + Testcontainers): `python -m pytest -m integration tests/integration`
- Lint/tipos: `ruff check .` y `mypy --strict app`

Si el host no tiene Python 3.12, ejecuta lint y pruebas dentro de un contenedor 3.12
(desde `backend/`, PowerShell):

```
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}:/app" -w /app -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal python:3.12-slim sh -c "pip install -q -e '.[dev]' && ruff check . && python -m pytest -m integration tests/integration -p no:cacheprovider -q"
```

El socket permite que Testcontainers levante el Oracle hermano y
`TESTCONTAINERS_HOST_OVERRIDE` permite alcanzarlo desde el contenedor de pruebas.
En Linux/macOS usa `-v "$(pwd):/app"`.
