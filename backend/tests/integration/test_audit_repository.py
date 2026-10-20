from __future__ import annotations

import json
from datetime import datetime

import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine

from app.domain.auth.audit import AuditAction, AuditEntry
from app.infrastructure.adapters.audit_repository import SqlAlchemyAuditRecorder

pytestmark = pytest.mark.integration


@pytest.fixture()
def recorder(migrated_engine: Engine) -> SqlAlchemyAuditRecorder:
    return SqlAlchemyAuditRecorder(migrated_engine)


def test_inserts_entry_with_actor_and_detail_json(
    recorder: SqlAlchemyAuditRecorder, migrated_engine: Engine
) -> None:
    entry = AuditEntry(
        entity="REQ_REQUERIMIENTO",
        entity_id=770001,
        action=AuditAction.STATE_TRANSITION,
        actor="luis.reviso",
        detail={
            "estado_anterior": "BORRADOR",
            "estado_actual": "EN_REVISION",
            "motivo": "Listo para revision",
        },
        created_at=datetime(2026, 10, 20, 12, 0, 0),
    )

    recorder.record(entry)

    with migrated_engine.connect() as connection:
        row = connection.execute(
            sa.text(
                "SELECT ACCION, ACTOR, DETALLE, CREATED_BY FROM SYS_AUDITORIA "
                "WHERE ENTIDAD = :entity AND ENTIDAD_ID = :entity_id"
            ),
            {"entity": "REQ_REQUERIMIENTO", "entity_id": 770001},
        ).one()

    assert row[0] == "STATE_TRANSITION"
    assert row[1] == "luis.reviso"
    assert row[3] == "luis.reviso"
    detail = json.loads(str(row[2]))
    assert detail["motivo"] == "Listo para revision"
    assert detail["estado_actual"] == "EN_REVISION"


def test_entry_without_entity_id_is_allowed(
    recorder: SqlAlchemyAuditRecorder, migrated_engine: Engine
) -> None:
    recorder.record(
        AuditEntry(
            entity="SYS_USUARIO",
            entity_id=None,
            action=AuditAction.LOGIN_FAILED,
            actor="fantasma",
            detail={"motivo": "usuario inexistente"},
        )
    )

    with migrated_engine.connect() as connection:
        row = connection.execute(
            sa.text(
                "SELECT COUNT(*) FROM SYS_AUDITORIA "
                "WHERE ENTIDAD = 'SYS_USUARIO' AND ENTIDAD_ID IS NULL "
                "AND ACCION = 'LOGIN_FAILED' AND ACTOR = 'fantasma'"
            )
        ).scalar_one()

    assert int(row) >= 1
