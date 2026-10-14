from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Attachment:
    """Metadato de un anexo; el binario vive fuera de Oracle (StoragePort)."""

    name: str
    order: int
    storage_key: str
    mime_type: str | None = None
    caption: str | None = None
    active: bool = True
    version_id: int | None = None
    id: int | None = None
