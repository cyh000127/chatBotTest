from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Mapping
from uuid import uuid4


DEFAULT_ADMIN_ACTOR_TYPE = "admin"
RESULT_SUCCESS = "success"
RESULT_FAILURE = "failure"


@dataclass(frozen=True)
class AdminAuditEvent:
    id: str
    actor_type_code: str
    actor_id: str | None
    action_code: str
    target_type_code: str | None
    target_id: str | None
    result_code: str
    source_code: str
    request_path: str | None
    detail: dict[str, Any]
    occurred_at: str
    created_at: str


class SqliteAdminAuditRepository:
    """Append-only local admin audit repository.

    Audit details intentionally exclude message bodies, phone numbers, tokens, and other secrets.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def record_event(
        self,
        *,
        action_code: str,
        actor_type_code: str = DEFAULT_ADMIN_ACTOR_TYPE,
        actor_id: str | None = None,
        target_type_code: str | None = None,
        target_id: str | None = None,
        result_code: str = RESULT_SUCCESS,
        source_code: str,
        request_path: str | None = None,
        detail: Mapping[str, Any] | None = None,
        occurred_at: str | None = None,
    ) -> AdminAuditEvent:
        now = datetime.now(UTC).isoformat()
        event_id = f"admin_audit_{uuid4().hex}"
        detail_payload = _safe_detail(detail)
        occurred_at = occurred_at or now
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO admin_audit_events (
                  id,
                  actor_type_code,
                  actor_id,
                  action_code,
                  target_type_code,
                  target_id,
                  result_code,
                  source_code,
                  request_path,
                  detail_json,
                  occurred_at,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    actor_type_code,
                    actor_id,
                    action_code,
                    target_type_code,
                    target_id,
                    result_code,
                    source_code,
                    request_path,
                    json.dumps(detail_payload, ensure_ascii=False, sort_keys=True),
                    occurred_at,
                    now,
                ),
            )
            self._connection.commit()
        return AdminAuditEvent(
            id=event_id,
            actor_type_code=actor_type_code,
            actor_id=actor_id,
            action_code=action_code,
            target_type_code=target_type_code,
            target_id=target_id,
            result_code=result_code,
            source_code=source_code,
            request_path=request_path,
            detail=detail_payload,
            occurred_at=occurred_at,
            created_at=now,
        )

    def list_events(
        self,
        *,
        limit: int = 100,
        action_code: str | None = None,
        result_code: str | None = None,
    ) -> list[AdminAuditEvent]:
        safe_limit = max(1, min(limit, 500))
        filters: list[str] = []
        values: list[object] = []
        if action_code:
            filters.append("action_code = ?")
            values.append(action_code)
        if result_code:
            filters.append("result_code = ?")
            values.append(result_code)
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        with self._lock:
            rows = self._connection.execute(
                f"""
                SELECT *
                FROM admin_audit_events
                {where_clause}
                ORDER BY occurred_at DESC, id DESC
                LIMIT ?
                """,
                (*values, safe_limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def _row_to_event(self, row: sqlite3.Row) -> AdminAuditEvent:
        detail_json = str(row["detail_json"] or "{}")
        try:
            detail = json.loads(detail_json)
        except json.JSONDecodeError:
            detail = {}
        if not isinstance(detail, dict):
            detail = {}
        return AdminAuditEvent(
            id=str(row["id"]),
            actor_type_code=str(row["actor_type_code"]),
            actor_id=row["actor_id"],
            action_code=str(row["action_code"]),
            target_type_code=row["target_type_code"],
            target_id=row["target_id"],
            result_code=str(row["result_code"]),
            source_code=str(row["source_code"]),
            request_path=row["request_path"],
            detail=detail,
            occurred_at=str(row["occurred_at"]),
            created_at=str(row["created_at"]),
        )


def _safe_detail(detail: Mapping[str, Any] | None) -> dict[str, Any]:
    if not detail:
        return {}
    safe: dict[str, Any] = {}
    for key, value in detail.items():
        if isinstance(value, str | int | float | bool) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)
    return safe
