# ADR-004 - Plantilla DOCX derivada del machote
- Estado: Aceptada
## Contexto
El machote institucional contiene un requerimiento de ejemplo, controles de contenido y defectos de formato; no es una plantilla utilizable (ver `doc/documents/mapeo-machote.md`).
## Decision
Conservar `templates/machote_requerimiento.docx` como referencia inmutable y mantener una plantilla derivada `templates/ers_plantilla_v1.docx` con etiquetas `docxtpl`. Toda modificacion de presentacion genera una nueva version de plantilla (`v2`, `v3`) y cada documento generado registra la version de plantilla usada.
## Consecuencias
Se puede regenerar cualquier version historica con su plantilla original. Mantener la plantilla requiere disciplina para que las etiquetas queden en un solo run de Word.
