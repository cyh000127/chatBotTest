from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from PROJECT.storage.invitations import utc_now_text

REMINDER_STATUS_PENDING = "pending"
REMINDER_STATUS_SENT = "sent"
REMINDER_STATUS_COMPLETED = "completed"
REMINDER_STATUS_CANCELLED = "cancelled"


@dataclass(frozen=True)
class ReminderDelivery:
    id: str
    project_id: str
    participant_id: str
    field_season_id: str | None
    seasonal_event_id: str | None
    input_resolution_session_id: str | None
    provider_user_id: str
    chat_id: int
    reminder_type_code: str
    reminder_status_code: str
    resume_token: str
    resume_target_code: str
    message_text: str
    due_at: str
    created_at: str
    updated_at: str
    sent_at: str | None
    completed_at: str | None


class SqliteReminderRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def create_reminder(
        self,
        *,
        project_id: str,
        participant_id: str,
        provider_user_id: str,
        chat_id: int,
        reminder_type_code: str,
        resume_target_code: str,
        message_text: str,
        due_at: str,
        field_season_id: str | None = None,
        seasonal_event_id: str | None = None,
        input_resolution_session_id: str | None = None,
        resume_token: str | None = None,
    ) -> ReminderDelivery:
        with self._lock:
            now = utc_now_text()
            reminder_id = f"reminder_{uuid4().hex}"
            token = resume_token or f"rt_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO reminder_deliveries (
                  id,
                  project_id,
                  participant_id,
                  field_season_id,
                  seasonal_event_id,
                  input_resolution_session_id,
                  provider_user_id,
                  chat_id,
                  reminder_type_code,
                  reminder_status_code,
                  resume_token,
                  resume_target_code,
                  message_text,
                  due_at,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reminder_id,
                    project_id,
                    participant_id,
                    field_season_id,
                    seasonal_event_id,
                    input_resolution_session_id,
                    provider_user_id,
                    chat_id,
                    reminder_type_code,
                    REMINDER_STATUS_PENDING,
                    token,
                    resume_target_code,
                    message_text,
                    due_at,
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_reminder(reminder_id)
            if created is None:
                raise RuntimeError("생성한 reminder를 다시 읽을 수 없습니다.")
            return created

    def get_reminder(self, reminder_id: str) -> ReminderDelivery | None:
        row = self._connection.execute(
            "SELECT * FROM reminder_deliveries WHERE id = ?",
            (reminder_id,),
        ).fetchone()
        if row is None:
            return None
        return ReminderDelivery(**dict(row))

    def get_by_resume_token(
        self,
        resume_token: str,
        *,
        provider_user_id: str | None = None,
    ) -> ReminderDelivery | None:
        if provider_user_id is None:
            row = self._connection.execute(
                """
                SELECT *
                FROM reminder_deliveries
                WHERE resume_token = ?
                LIMIT 1
                """,
                (resume_token,),
            ).fetchone()
        else:
            row = self._connection.execute(
                """
                SELECT *
                FROM reminder_deliveries
                WHERE resume_token = ?
                  AND provider_user_id = ?
                LIMIT 1
                """,
                (resume_token, provider_user_id),
            ).fetchone()
        if row is None:
            return None
        return ReminderDelivery(**dict(row))

    def list_reminders(self, *, status: str | None = None) -> tuple[ReminderDelivery, ...]:
        if status is None:
            rows = self._connection.execute(
                "SELECT * FROM reminder_deliveries ORDER BY created_at ASC"
            ).fetchall()
        else:
            rows = self._connection.execute(
                """
                SELECT *
                FROM reminder_deliveries
                WHERE reminder_status_code = ?
                ORDER BY created_at ASC
                """,
                (status,),
            ).fetchall()
        return tuple(ReminderDelivery(**dict(row)) for row in rows)

    def due_pending_reminders(self, *, limit: int = 20, now: datetime | None = None) -> tuple[ReminderDelivery, ...]:
        current = (now or datetime.now(UTC)).isoformat()
        rows = self._connection.execute(
            """
            SELECT *
            FROM reminder_deliveries
            WHERE reminder_status_code = ?
              AND due_at <= ?
            ORDER BY due_at ASC, created_at ASC
            LIMIT ?
            """,
            (REMINDER_STATUS_PENDING, current, limit),
        ).fetchall()
        return tuple(ReminderDelivery(**dict(row)) for row in rows)

    def mark_sent(self, reminder_id: str) -> ReminderDelivery | None:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE reminder_deliveries
                SET reminder_status_code = ?,
                    sent_at = COALESCE(sent_at, ?),
                    updated_at = ?
                WHERE id = ?
                  AND reminder_status_code = ?
                """,
                (
                    REMINDER_STATUS_SENT,
                    now,
                    now,
                    reminder_id,
                    REMINDER_STATUS_PENDING,
                ),
            )
            self._connection.commit()
        return self.get_reminder(reminder_id)

    def mark_completed(self, reminder_id: str) -> ReminderDelivery | None:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE reminder_deliveries
                SET reminder_status_code = ?,
                    completed_at = COALESCE(completed_at, ?),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    REMINDER_STATUS_COMPLETED,
                    now,
                    now,
                    reminder_id,
                ),
            )
            self._connection.commit()
        return self.get_reminder(reminder_id)

    def cancel(self, reminder_id: str) -> ReminderDelivery | None:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE reminder_deliveries
                SET reminder_status_code = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    REMINDER_STATUS_CANCELLED,
                    now,
                    reminder_id,
                ),
            )
            self._connection.commit()
        return self.get_reminder(reminder_id)
