# ADR-002 - Arquitectura hexagonal y despliegue en Docker
- Estado: Aceptada
## Decision
Capas `domain`, `application`, `infrastructure`, `api`. Puertos para storage, IA, autenticacion y renderizado documental. Servicios en Docker Compose: frontend, backend (con LibreOffice), oracle (solo dev) y minio (solo dev). Misma imagen en dev y prod; cambia solo la configuracion por variables de entorno. Wallet de Autonomous DB montado como volumen/secret.
## Consecuencias
El dominio es independiente de Oracle, IA y Word, cumpliendo el criterio funcional central.
