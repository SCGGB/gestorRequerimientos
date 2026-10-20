from abc import ABC, abstractmethod

from app.domain.auth.audit import AuditEntry


class AuditRecorderPort(ABC):
    @abstractmethod
    def record(self, entry: AuditEntry) -> None:
        pass
