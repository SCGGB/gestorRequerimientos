from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from app.application.errors import AttachmentNotFoundError
from app.application.ports.audit_repository import AuditRecorderPort
from app.application.ports.auth import Principal
from app.application.ports.requirement_repository import RequirementRepository
from app.application.use_cases.requirement._common import (
    load_editable_working_version,
    save_version,
)
from app.domain.auth.audit import AuditAction, AuditEntry
from app.domain.requirement.attachment import Attachment
from app.domain.requirement.version import RequirementVersion

_AUDIT_ACTION = AuditAction.ATTACHMENT_UPDATE


def _find(version: RequirementVersion, attachment_id: int) -> Attachment | None:
    for attachment in version.attachments:
        if attachment.id == attachment_id:
            return attachment
    return None


class _AttachmentUseCase:
    """Base con repositorio y auditoria compartidos por las operaciones de anexos."""

    def __init__(self, repository: RequirementRepository, audit: AuditRecorderPort) -> None:
        self._repository = repository
        self._audit = audit

    def _record(
        self,
        version: RequirementVersion,
        operation: str,
        actor: str,
        attachment_id: int | None = None,
    ) -> None:
        detail: dict[str, object] = {"operacion": operation}
        if attachment_id is not None:
            detail["anexo_id"] = attachment_id
        self._audit.record(
            AuditEntry(
                entity="REQ_VERSION",
                entity_id=version.id,
                action=_AUDIT_ACTION,
                actor=actor,
                detail=detail,
            )
        )


class AddAttachment(_AttachmentUseCase):
    """Registra el metadato de un anexo en la version de trabajo."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        *,
        principal: Principal,
        name: str,
        storage_key: str,
        mime_type: str | None = None,
        caption: str | None = None,
    ) -> Attachment:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        next_order = max((item.order for item in version.attachments), default=0) + 1
        attachment = Attachment(
            name=name,
            order=next_order,
            storage_key=storage_key,
            mime_type=mime_type,
            caption=caption,
        )
        updated = replace(version, attachments=(*version.attachments, attachment))
        saved = save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, "alta", principal.user_id)
        return saved.attachments[-1]


class UpdateAttachment(_AttachmentUseCase):
    """Actualiza el metadato de un anexo de la version de trabajo."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        attachment_id: int,
        *,
        principal: Principal,
        name: str | None = None,
        storage_key: str | None = None,
        mime_type: str | None = None,
        caption: str | None = None,
    ) -> Attachment:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        attachment = _find(version, attachment_id)
        if attachment is None:
            raise AttachmentNotFoundError()

        changes: dict[str, Any] = {}
        if name is not None:
            changes["name"] = name
        if storage_key is not None:
            changes["storage_key"] = storage_key
        if mime_type is not None:
            changes["mime_type"] = mime_type
        if caption is not None:
            changes["caption"] = caption
        updated_attachment = replace(attachment, **changes)
        updated = replace(
            version,
            attachments=tuple(
                updated_attachment if item is attachment else item
                for item in version.attachments
            ),
        )
        saved = save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, "edicion", principal.user_id, attachment_id)
        reloaded = _find(saved, attachment_id)
        if reloaded is None:
            raise AttachmentNotFoundError()
        return reloaded


class DeleteAttachment(_AttachmentUseCase):
    """Baja logica de un anexo de la version de trabajo (soft-delete)."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        attachment_id: int,
        *,
        principal: Principal,
    ) -> None:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        attachment = _find(version, attachment_id)
        if attachment is None:
            raise AttachmentNotFoundError()
        updated = replace(
            version,
            attachments=tuple(
                replace(item, active=False) if item is attachment else item
                for item in version.attachments
            ),
        )
        save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, "baja", principal.user_id, attachment_id)


class ReorderAttachments(_AttachmentUseCase):
    """Reordena los anexos de la version de trabajo segun la lista de ids."""

    def execute(
        self,
        requirement_id: int,
        version_id: int,
        ordered_ids: Sequence[int],
        *,
        principal: Principal,
    ) -> Sequence[Attachment]:
        requirement, version = load_editable_working_version(
            self._repository, requirement_id, version_id
        )
        for attachment_id in ordered_ids:
            if _find(version, attachment_id) is None:
                raise AttachmentNotFoundError()

        by_id = {item.id: item for item in version.attachments if item.id is not None}
        leading: list[Attachment] = []
        seen: set[int] = set()
        for attachment_id in ordered_ids:
            item = by_id.get(attachment_id)
            if item is not None and attachment_id not in seen:
                leading.append(item)
                seen.add(attachment_id)
        active_rest = [
            item for item in version.attachments if item.active and item.id not in seen
        ]
        inactive = [item for item in version.attachments if not item.active]
        sequence = (*leading, *active_rest, *inactive)
        renumbered = tuple(
            replace(item, order=order) for order, item in enumerate(sequence, start=1)
        )
        updated = replace(version, attachments=renumbered)
        saved = save_version(
            self._repository, requirement, version, updated, actor=principal.user_id
        )
        self._record(version, "reorden", principal.user_id)
        return saved.attachments
