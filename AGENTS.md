# AGENTS.md - Sistema de Especificacion de Requerimientos de Software

## Proposito
Aplicacion que estandariza el levantamiento de requerimientos y genera la ERS con la estructura del machote institucional (`templates/machote_requerimiento.docx`). Fuente de verdad funcional: `doc/product/01_SPEC_FUNCIONAL.md`.


## Reglas fundamentales

1. No inventar requerimientos.
2. No cambiar decisiones arquitectónicas sin documentarlo.
3. Las SPEC funcionales tienen prioridad sobre las referencias visuales.
4. Las screens de Stitch son referencia visual.
5. El código de Stitch NO es código fuente del proyecto.
6. No incorporar dependencias sin justificar su necesidad.
7. Consultar documentación actual mediante Context7 cuando se utilicen
   APIs o patrones de Python o las librerías principales.
8. La aplicación debe funcionar sin IA.
9. La IA es asistiva y nunca sustituye automáticamente contenido del usuario.
10. La Base de Datos es la fuente de verdad.
11. DOCX/PDF son representaciones generadas.
12. Mantener backend, frontend y persistencia desacoplados.
13. En caso de dudas o ambiguedad siempre preguntar

## Prioridad documental

En caso de contradicción:

1. SPEC funcional y reglas de negocio.
2. Arquitectura.
3. Modelo de datos.
4. SPEC técnica correspondiente.
5. SPEC UI/UX.
6. Screens Stitch.
7. Código Stitch.

Si existe una contradicción que no pueda resolverse con esta prioridad,
detener la implementación afectada y reportarla.

## Stack (decisiones en doc/architecture/adr)
- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic.
- BD: Oracle (Autonomous en nube, oracle-free en dev) con `python-oracledb` en modo thin.
- DOCX: `docxtpl`. PDF: LibreOffice headless convirtiendo el DOCX.
- Frontend: React + Vite + TypeScript + Tailwind. Maquetado inicial con Stitch (referencias en `doc/ui/`).
- Todo corre en Docker (`docker-compose.yml`, Dockerfiles en `docker/`).
- Pruebas: pytest, Testcontainers, Playwright (wizard).

## Flujo Spec-Driven Development (obligatorio)
1. `/spec <tema>`  -> crea `specs/SPEC-NNN-nombre/spec.md` (QUE y POR QUE, criterios de aceptacion).
2. `/plan <SPEC>`  -> `plan.md` (COMO: diseno tecnico, tablas, endpoints, componentes).
3. `/tasks <SPEC>` -> `tasks.md` (tareas atomicas, ordenadas, verificables).
4. `/implement <SPEC>` -> implementa tarea por tarea y marca avance.
5. `/verify <SPEC>` -> `verify.md` con evidencia contra los criterios de aceptacion.

Reglas:
- NO escribir codigo sin spec con estado `Aprobada` y plan existente.
- Si una spec contradice a `doc/`, se detiene el trabajo y se pregunta; no se decide en silencio.
- Cada spec declara que documentos de `doc/` le aplican.
- Cambios de arquitectura requieren un ADR nuevo en `doc/architecture/adr/`.

## Arquitectura (hexagonal)
`backend/app/{domain,application,infrastructure,api}`
- `domain`: entidades y reglas puras. Sin imports de FastAPI, SQLAlchemy ni librerias de IA/DOCX.
- `application`: casos de uso y puertos (`StoragePort`, `AiAssistantPort`, `AuthProvider`, `DocumentRenderer`).
- `infrastructure`: adaptadores (Oracle, storage, IA, docxtpl/LibreOffice, auth).
- `api`: routers y esquemas HTTP.

## Principios del producto (no negociables)
- El modelo estructurado en Oracle es la fuente de verdad; el machote solo define la presentacion.
- Vista previa, DOCX y PDF se generan del mismo contenido/version y deben ser consistentes.
- La aplicacion debe operar sin IA (`AI_PROVIDER=none`).
- Las colecciones (objetivos, consideraciones, beneficios, restricciones, riesgos) son elementos independientes con id, orden, contenido y estado, nunca un bloque de texto.
- Trazabilidad y auditoria de todo cambio.

## Convenciones
- Python: tipado completo, `ruff` y `mypy` sin errores, funciones pequenas, sin logica de negocio en routers.
- SQL Oracle: ver `doc/development/convenciones.md`. DDL solo via Alembic.
- Secretos y wallet fuera de imagenes y de git.
- Idioma: codigo en ingles, documentacion y mensajes de usuario en espanol.

## Definicion de hecho
Criterios de la spec cumplidos y evidenciados en `verify.md`, pruebas pasando, lint/tipos limpios, migracion Alembic incluida, documentacion en `doc/` actualizada.

## Reglas de código

- Usar código limpio, nombres, funciones, variables, etc. en ingles

## Comandos (desde `backend/`)

- Lint: `ruff check .`
- Tipos: `mypy --strict app`
- Unitarias (sin Docker): `python -m pytest`
- Integración (Docker + Testcontainers): `python -m pytest -m integration tests/integration`
- Si el host no tiene Python 3.12, correr lint y pruebas en un contenedor 3.12:

```
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}:/app" -w /app -e TESTCONTAINERS_HOST_OVERRIDE=host.docker.internal python:3.12-slim sh -c "pip install -q -e '.[dev]' && ruff check . && python -m pytest -m integration tests/integration -p no:cacheprovider -q"
```

## Spec Driven Development - Skills
- /spec usaremos esta habilidad para crear las especificaciones
- /spec-impl usaremos esta skill para hacer las implementaciones
- /verify verifica la spec contra sus criterios de aceptacion con el agente `reviewer`