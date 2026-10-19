# syntax=docker/dockerfile:1
#
# Imagen de integracion: extiende la imagen de desarrollo con LibreOffice y
# poppler-utils para verificar la conversion DOCX/PDF real (SPEC-007, CA-02).
#
#   docker build -f docker/backend-integration.Dockerfile -t gestor-req-integration .
#
# y desde backend/ (ruta absoluta; ${PWD} no expande bien en PowerShell):
#
#   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
#     -v "<ruta-absoluta>/backend:/app" -w /app \
#     -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal \
#     gestor-req-integration \
#     sh -c "python -m pytest -m integration tests/integration -p no:cacheprovider -q"

FROM python:3.12-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        poppler-utils \
        fonts-liberation \
        fonts-dejavu-core \
        fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY backend/pyproject.toml ./backend/pyproject.toml
COPY backend/app ./backend/app
RUN pip install --upgrade pip \
    && pip install './backend[dev]' \
    && pip uninstall -y gestor-requerimientos-backend

WORKDIR /app
