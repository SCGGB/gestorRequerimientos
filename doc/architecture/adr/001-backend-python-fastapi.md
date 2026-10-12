# ADR-001 - Backend en Python + FastAPI
- Estado: Aceptada
## Contexto
Se desea aprender una tecnologia distinta de Java. El nucleo del MVP es la generacion DOCX/PDF fiel al machote, validacion estructurada e IA intercambiable.
## Decision
Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic; `docxtpl` para DOCX; LibreOffice headless para PDF; `python-oracledb` (thin) para Oracle.
## Consecuencias
Excelente soporte documental y de IA. Curva de aprendizaje en tipado dinamico y async; se mitiga con mypy estricto y ruff.
## Alternativas
NestJS (TypeScript), ASP.NET Core.
