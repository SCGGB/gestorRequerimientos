# ADR-006 - Object store S3 de desarrollo (RustFS) y perfil de Compose
- Estado: Aceptada
- Fecha: 2026-10-12
## Contexto
El entorno de desarrollo definido en ADR-002 usaba el servicio `minio` con la imagen `minio/minio`. MinIO ceso su desarrollo (25-abr-2026) y su imagen ya no esta publicada en Docker Hub ni en Quay (`quay.io/minio/minio`); `bitnami/minio` tampoco esta disponible. `docker compose up` aborta al intentar descargar `minio/minio`. El proyecto aun no consume el object store: `storage_backend` es `local` por defecto y el `StoragePort` es solo un puerto marcador en SPEC-001 (su adaptador y variables llegan en una spec posterior).
## Decision
- Usar **RustFS** (`rustfs/rustfs`, Apache-2.0, S3-compatible y compatible con las rutas de salud de MinIO) como object store S3 de desarrollo, con version fijada (`rustfs/rustfs:1.0.0`). S3 en el puerto `9000` y consola en `9001`.
- El servicio se declara bajo el **perfil de Compose `objectstore`**, de modo que `docker compose up` levanta solo `oracle`, `backend` y `frontend`; el object store se levanta con `docker compose --profile objectstore up`.
- Renombrar el valor `minio` de `STORAGE_BACKEND` a `s3` (`local | s3 | oci`), reflejando que el backend es S3-compatible y no un producto concreto.
- Este ADR **enmienda** el listado de servicios de ADR-002 (sustituye `minio` por el object store S3 RustFS); ADR-002 no se reescribe.
## Consecuencias
`docker compose up` deja de depender de una imagen retirada y arranca el entorno base con Oracle, backend y frontend. El object store de desarrollo queda disponible de forma opt-in. La aplicacion permanece desacoplada: al no existir todavia adaptador de storage, el unico impacto es la configuracion (`STORAGE_BACKEND`).
## Alternativas consideradas
- **`coollabsio/minio`** (rebuild comunitario de MinIO): drop-in exacto (mismos puertos, env y healthcheck), pero MinIO sigue sin mantenimiento y depende de un solo mantenedor con etiquetas escasas.
- **SeaweedFS** (`chrislusf/seaweedfs`): mantenido y firmado con cosign, pero multi-componente y con puerto S3 distinto (8333); sobredimensionado para desarrollo.
- **Sin object store** en esta spec: se descarta porque la spec incluye el servicio de desarrollo; se prefiere dejarlo disponible de forma opt-in.
