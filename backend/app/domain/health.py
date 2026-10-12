from dataclasses import dataclass
from enum import StrEnum


class ApplicationStatus(StrEnum):
    OK = "ok"


class DatabaseStatus(StrEnum):
    OK = "ok"
    DOWN = "down"


@dataclass(frozen=True, slots=True)
class HealthReport:
    app: ApplicationStatus
    database: DatabaseStatus
