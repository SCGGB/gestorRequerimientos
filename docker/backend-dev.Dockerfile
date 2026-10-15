# syntax=docker/dockerfile:1
#
# Imagen de desarrollo para lint, tipos y pruebas (ruff, mypy, pytest).
# Se construye una sola vez y luego se reutiliza montando el codigo fuente,
# evitando reinstalar dependencias en cada verificacion.
#
#   docker build -f docker/backend-dev.Dockerfile -t gestor-req-dev .
#   docker run --rm -v "${PWD}:/app" -w /app gestor-req-dev \
#     sh -c "ruff check . && mypy --strict app && python -m pytest -q"
#
# (ejecutar desde backend/, por eso ${PWD} apunta a esa carpeta)

FROM python:3.12-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala las dependencias de runtime y dev desde pyproject; luego quita el
# paquete del proyecto para que el codigo montado en /app tenga prioridad.
WORKDIR /build
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
RUN pip install --upgrade pip \
    && pip install './backend[dev]' \
    && pip uninstall -y gestor-requerimientos-backend

WORKDIR /app
