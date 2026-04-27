from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from threading import RLock
from uuid import uuid4

from PROJECT.admin.follow_up import (
    DEFAULT_OUTBOX_MAX_RETRY_COUNT,
    DEFAULT_OUTBOX_RETRY_BACKOFF_SECONDS,
    FOLLOW_UP_CLOSED_NOTICE,
    FollowUpItem,
    FollowUpStatus,
    OutboxMessage,
    OutboxStatus,
)
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import (
    ADMIN_FOLLOW_UP_CLOSED,
    ADMIN_FOLLOW_UP_CREATED,
    ADMIN_FOLLOW_UP_USER_MESSAGE_ADDED,
    ADMIN_REPLY_CREATED,
    OUTBOX_MESSAGE_CREATED,
    OUTBOX_MESSAGE_REQUEUED,
)


USER_MESSAGE_DIRECTION = "user"
ADMIN_MESSAGE_DIRECTION = "admin"
OUTBOX_SOURCE_CLOSE_NOTICE = "admin.follow_up.close_notice"


def _now() -> datetime:
    return datetime.now(UTC)


def _now_text() -> str:
    return _now().isoformat()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


class SqliteAdminRuntime:
    """SQLite-backed admin follow-up queue with the in-memory runtime contract."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def clear(self) -> None:
        with self._lock:
            self._connection.execute("DELETE FROM outbox_messages")
            self._connection.execute("DELETE FROM admin_follow_up_outcomes")
            self._connection.execute("DELETE FROM admin_follow_up_messages")
            self._connection.execute("DELETE FROM admin_follow_up_queue")
            self._connection.commit()

    def create_follow_up(
        self,
        *,
        route_hint: str,
        reason: str,
        chat_id: int,
        user_id: int | None,
        current_step: str | None,
        locale: str = "ko",
        user_message: str = "",
        failure_count: int = 0,
        recent_messages_summary: str = "",
        source: str = "support.escalate",
    ) -> FollowUpItem:
        now = _now_text()
        follow_up_id = f"followup_{uuid4().hex}"
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO admin_follow_up_queue (
                  id,
                  issue_type_code,
                  follow_up_status_code,
                  created_from_code,
                  route_hint,
                  reason,
                  current_step_code,
                  chat_id,
                  provider_user_id,
                  locale_code,
                  recent_messages_summary,
                  failure_count,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    follow_up_id,
                    reason,
                    FollowUpStatus.WAITING_ADMIN_REPLY.value,
                    source,
                    route_hint,
                    reason,
                    current_step,
                    chat_id,
                    str(user_id) if user_id is not None else None,
                    locale,
                    recent_messages_summary,
                    failure_count,
                    now,
                    now,
                ),
            )
            if user_message:
                self._insert_follow_up_message(
                    follow_up_id=follow_up_id,
                    direction_code=USER_MESSAGE_DIRECTION,
                    message_text=user_message,
                    actor_type="user",
                    actor_id=str(user_id) if user_id is not None else None,
                    created_at=now,
                )
            self._connection.commit()
        follow_up = self.get_follow_up(follow_up_id)
        if follow_up is None:
            raise RuntimeError("생성한 follow-up을 다시 읽을 수 없습니다.")
        log_event(
            ADMIN_FOLLOW_UP_CREATED,
            source=source,
            follow_up_id=follow_up.follow_up_id,
            command_request_id=follow_up.command_request_id,
            route_hint=follow_up.route_hint,
            reason=follow_up.reason,
            state=follow_up.current_step,
            failure_count=follow_up.failure_count,
        )
        return follow_up

    def list_command_requests(self) -> list:
        return []

    def list_follow_ups(
        self,
        *,
        include_closed: bool = True,
        status: FollowUpStatus | None = None,
        query: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
    ) -> list[FollowUpItem]:
        filters: list[str] = []
        values: list[object] = []
        if status is not None:
            filters.append("follow_up_status_code = ?")
            values.append(status.value)
        elif not include_closed:
            filters.append("follow_up_status_code != ?")
            values.append(FollowUpStatus.CLOSED.value)
        normalized_query = (query or "").strip().lower()
        if normalized_query:
            like = f"%{normalized_query}%"
            filters.append(
                """
                (
                  lower(id) LIKE ?
                  OR lower(route_hint) LIKE ?
                  OR lower(reason) LIKE ?
                  OR lower(COALESCE(current_step_code, '')) LIKE ?
                  OR lower(COALESCE(locale_code, '')) LIKE ?
                  OR CAST(chat_id AS TEXT) LIKE ?
                  OR COALESCE(provider_user_id, '') LIKE ?
                  OR lower(COALESCE(recent_messages_summary, '')) LIKE ?
                  OR EXISTS (
                    SELECT 1
                    FROM admin_follow_up_messages
                    WHERE admin_follow_up_messages.admin_follow_up_queue_id = admin_follow_up_queue.id
                      AND lower(message_text) LIKE ?
                  )
                )
                """
            )
            values.extend((like, like, like, like, like, like, like, like, like))
        if created_from:
            filters.append("substr(created_at, 1, 10) >= ?")
            values.append(created_from)
        if created_to:
            filters.append("substr(created_at, 1, 10) <= ?")
            values.append(created_to)
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        with self._lock:
            rows = self._connection.execute(
                f"""
                SELECT *
                FROM admin_follow_up_queue
                {where_clause}
                ORDER BY created_at ASC
                """,
                tuple(values),
            ).fetchall()
            return [self._row_to_follow_up(row) for row in rows]

    def get_follow_up(self, follow_up_id: str) -> FollowUpItem | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM admin_follow_up_queue WHERE id = ?",
                (follow_up_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_follow_up(row)

    def append_user_message(
        self,
        follow_up_id: str,
        user_message: str,
        *,
        source: str = "runtime",
    ) -> FollowUpItem | None:
        with self._lock:
            follow_up = self.get_follow_up(follow_up_id)
            if follow_up is None or follow_up.closed:
                return None
            now = _now_text()
            self._insert_follow_up_message(
                follow_up_id=follow_up_id,
                direction_code=USER_MESSAGE_DIRECTION,
                message_text=user_message,
                actor_type="user",
                actor_id=str(follow_up.user_id) if follow_up.user_id is not None else None,
                created_at=now,
            )
            self._connection.execute(
                """
                UPDATE admin_follow_up_queue
                SET follow_up_status_code = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (FollowUpStatus.WAITING_ADMIN_REPLY.value, now, follow_up_id),
            )
            self._connection.commit()
        updated = self.get_follow_up(follow_up_id)
        if updated is not None:
            log_event(
                ADMIN_FOLLOW_UP_USER_MESSAGE_ADDED,
                source=source,
                follow_up_id=follow_up_id,
                route_hint=updated.route_hint,
                state=updated.current_step,
                message_count=len(updated.user_messages),
            )
        return updated

    def create_admin_reply(
        self,
        follow_up_id: str,
        admin_message: str,
        *,
        source: str = "admin.follow_up.reply",
    ) -> tuple[FollowUpItem, OutboxMessage] | None:
        with self._lock:
            follow_up = self.get_follow_up(follow_up_id)
            if follow_up is None or follow_up.closed:
                return None
            now = _now_text()
            self._insert_follow_up_message(
                follow_up_id=follow_up_id,
                direction_code=ADMIN_MESSAGE_DIRECTION,
                message_text=admin_message,
                actor_type="admin",
                actor_id=None,
                created_at=now,
            )
            self._connection.execute(
                """
                UPDATE admin_follow_up_queue
                SET follow_up_status_code = ?,
                    first_action_at = COALESCE(first_action_at, ?),
                    updated_at = ?
                WHERE id = ?
                """,
                (FollowUpStatus.OPEN.value, now, now, follow_up_id),
            )
            outbox = self._insert_outbox_message(
                follow_up_id=follow_up_id,
                chat_id=follow_up.chat_id,
                message_text=admin_message,
                source=source,
                created_at=now,
            )
            self._connection.commit()
        updated = self.get_follow_up(follow_up_id)
        if updated is None:
            return None
        log_event(
            ADMIN_REPLY_CREATED,
            source=source,
            follow_up_id=follow_up_id,
            route_hint=updated.route_hint,
            state=updated.current_step,
            admin_reply_count=updated.admin_reply_count,
        )
        log_event(
            OUTBOX_MESSAGE_CREATED,
            source=source,
            outbox_id=outbox.outbox_id,
            follow_up_id=follow_up_id,
            chat_id=outbox.chat_id,
            status=outbox.status.value,
        )
        return updated, outbox

    def close_follow_up(
        self,
        follow_up_id: str,
        *,
        source: str = "runtime",
        notify_user: bool = False,
        notice_text: str = FOLLOW_UP_CLOSED_NOTICE,
    ) -> FollowUpItem | None:
        with self._lock:
            follow_up = self.get_follow_up(follow_up_id)
            if follow_up is None:
                return None
            if follow_up.closed:
                return follow_up
            now = _now_text()
            self._connection.execute(
                """
                UPDATE admin_follow_up_queue
                SET follow_up_status_code = ?,
                    closed_at = ?,
                    closure_reason_code = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (FollowUpStatus.CLOSED.value, now, source, now, follow_up_id),
            )
            self._connection.execute(
                """
                INSERT INTO admin_follow_up_outcomes (
                  id,
                  admin_follow_up_queue_id,
                  outcome_code,
                  note,
                  acted_at,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"followup_outcome_{uuid4().hex}", follow_up_id, FollowUpStatus.CLOSED.value, source, now, now),
            )
            if notify_user:
                self._insert_outbox_message(
                    follow_up_id=follow_up_id,
                    chat_id=follow_up.chat_id,
                    message_text=notice_text,
                    source=OUTBOX_SOURCE_CLOSE_NOTICE,
                    created_at=now,
                )
            self._connection.commit()
        updated = self.get_follow_up(follow_up_id)
        if updated is not None:
            log_event(
                ADMIN_FOLLOW_UP_CLOSED,
                source=source,
                follow_up_id=follow_up_id,
                route_hint=updated.route_hint,
                state=updated.current_step,
                user_message_count=len(updated.user_messages),
                admin_reply_count=updated.admin_reply_count,
            )
        return updated

    def list_outbox(self, *, status: OutboxStatus | None = None) -> list[OutboxMessage]:
        with self._lock:
            if status is None:
                rows = self._connection.execute(
                    "SELECT * FROM outbox_messages ORDER BY created_at ASC"
                ).fetchall()
            else:
                rows = self._connection.execute(
                    """
                    SELECT *
                    FROM outbox_messages
                    WHERE delivery_state_code = ?
                    ORDER BY created_at ASC
                    """,
                    (status.value,),
                ).fetchall()
            return [self._row_to_outbox(row) for row in rows]

    def claim_pending_outbox(self, *, limit: int = 10) -> list[OutboxMessage]:
        with self._lock:
            rows = self._claimable_outbox_rows(limit=limit)
            now = _now_text()
            for row in rows:
                self._connection.execute(
                    """
                    UPDATE outbox_messages
                    SET delivery_state_code = ?,
                        error_message = NULL,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (OutboxStatus.SENDING.value, now, row["id"]),
                )
            self._connection.commit()
            return [self._row_to_outbox({**dict(row), "delivery_state_code": OutboxStatus.SENDING.value, "updated_at": now}) for row in rows]

    def _claimable_outbox_rows(self, *, limit: int) -> list[sqlite3.Row]:
        pending_rows = self._connection.execute(
            """
            SELECT *
            FROM outbox_messages
            WHERE delivery_state_code = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (OutboxStatus.PENDING.value, limit),
        ).fetchall()
        if len(pending_rows) >= limit:
            return list(pending_rows)

        remaining = limit - len(pending_rows)
        failed_rows = self._connection.execute(
            """
            SELECT *
            FROM outbox_messages
            WHERE delivery_state_code = ?
              AND retry_count < ?
            ORDER BY created_at ASC
            """,
            (OutboxStatus.FAILED.value, DEFAULT_OUTBOX_MAX_RETRY_COUNT),
        ).fetchall()
        now = _now()
        eligible_failed_rows = [
            row
            for row in failed_rows
            if self._failed_outbox_retry_due(row, now=now)
        ][:remaining]
        return sorted(
            [*pending_rows, *eligible_failed_rows],
            key=lambda row: str(row["created_at"]),
        )

    def _failed_outbox_retry_due(self, row: sqlite3.Row, *, now: datetime) -> bool:
        retry_count = int(row["retry_count"] or 0)
        if retry_count >= DEFAULT_OUTBOX_MAX_RETRY_COUNT:
            return False
        updated_at = _parse_datetime(str(row["updated_at"]))
        backoff_seconds = DEFAULT_OUTBOX_RETRY_BACKOFF_SECONDS * max(retry_count, 1)
        return updated_at + timedelta(seconds=backoff_seconds) <= now

    def mark_outbox_sent(self, outbox_id: str) -> OutboxMessage | None:
        return self._replace_outbox_status(outbox_id, OutboxStatus.SENT, error_message=None)

    def mark_outbox_failed(self, outbox_id: str, error_message: str) -> OutboxMessage | None:
        return self._replace_outbox_status(outbox_id, OutboxStatus.FAILED, error_message=error_message)

    def requeue_manual_review_outbox(
        self,
        outbox_id: str,
        *,
        source: str = "admin.outbox.requeue",
    ) -> OutboxMessage | None:
        with self._lock:
            existing = self._connection.execute(
                "SELECT * FROM outbox_messages WHERE id = ?",
                (outbox_id,),
            ).fetchone()
            if existing is None or str(existing["delivery_state_code"]) != OutboxStatus.MANUAL_REVIEW.value:
                return None
            now = _now_text()
            self._connection.execute(
                """
                UPDATE outbox_messages
                SET delivery_state_code = ?,
                    retry_count = 0,
                    error_message = NULL,
                    updated_at = ?,
                    sent_at = NULL,
                    failed_at = NULL
                WHERE id = ?
                """,
                (
                    OutboxStatus.PENDING.value,
                    now,
                    outbox_id,
                ),
            )
            self._connection.commit()
            row = self._connection.execute(
                "SELECT * FROM outbox_messages WHERE id = ?",
                (outbox_id,),
            ).fetchone()
            updated = self._row_to_outbox(row)
            log_event(
                OUTBOX_MESSAGE_REQUEUED,
                source=source,
                outbox_id=outbox_id,
                follow_up_id=updated.follow_up_id,
                chat_id=updated.chat_id,
            )
            return updated

    def _replace_outbox_status(
        self,
        outbox_id: str,
        status: OutboxStatus,
        *,
        error_message: str | None,
    ) -> OutboxMessage | None:
        with self._lock:
            existing = self._connection.execute(
                "SELECT * FROM outbox_messages WHERE id = ?",
                (outbox_id,),
            ).fetchone()
            if existing is None:
                return None
            now = _now_text()
            retry_count = int(existing["retry_count"] or 0)
            resolved_status = status
            if status == OutboxStatus.FAILED:
                retry_count += 1
                if retry_count >= DEFAULT_OUTBOX_MAX_RETRY_COUNT:
                    resolved_status = OutboxStatus.MANUAL_REVIEW
            self._connection.execute(
                """
                UPDATE outbox_messages
                SET delivery_state_code = ?,
                    retry_count = ?,
                    error_message = ?,
                    updated_at = ?,
                    sent_at = CASE WHEN ? = ? THEN ? ELSE sent_at END,
                    failed_at = CASE WHEN ? IN (?, ?) THEN ? ELSE failed_at END
                WHERE id = ?
                """,
                (
                    resolved_status.value,
                    retry_count,
                    error_message,
                    now,
                    resolved_status.value,
                    OutboxStatus.SENT.value,
                    now,
                    resolved_status.value,
                    OutboxStatus.FAILED.value,
                    OutboxStatus.MANUAL_REVIEW.value,
                    now,
                    outbox_id,
                ),
            )
            self._connection.commit()
            row = self._connection.execute(
                "SELECT * FROM outbox_messages WHERE id = ?",
                (outbox_id,),
            ).fetchone()
            return self._row_to_outbox(row)

    def _row_to_follow_up(self, row: sqlite3.Row) -> FollowUpItem:
        messages = self._messages_for_follow_up(str(row["id"]))
        user_messages = tuple(message for direction, message in messages if direction == USER_MESSAGE_DIRECTION)
        admin_messages = tuple(message for direction, message in messages if direction == ADMIN_MESSAGE_DIRECTION)
        status = FollowUpStatus(str(row["follow_up_status_code"]))
        user_id = int(row["provider_user_id"]) if row["provider_user_id"] is not None else None
        created_at = _parse_datetime(str(row["created_at"]))
        updated_at = _parse_datetime(str(row["updated_at"]))
        return FollowUpItem(
            follow_up_id=str(row["id"]),
            command_request_id=f"cmd_{str(row['id']).removeprefix('followup_')}",
            route_hint=str(row["route_hint"]),
            reason=str(row["reason"]),
            chat_id=int(row["chat_id"]),
            user_id=user_id,
            status=status,
            current_step=row["current_step_code"],
            locale=str(row["locale_code"]),
            recent_messages_summary=str(row["recent_messages_summary"] or ""),
            failure_count=int(row["failure_count"]),
            user_message=user_messages[0] if user_messages else "",
            created_at=created_at,
            updated_at=updated_at,
            awaiting_admin_reply=status == FollowUpStatus.WAITING_ADMIN_REPLY,
            admin_reply_count=len(admin_messages),
            closed=status == FollowUpStatus.CLOSED,
            user_messages=user_messages,
            admin_messages=admin_messages,
        )

    def _messages_for_follow_up(self, follow_up_id: str) -> tuple[tuple[str, str], ...]:
        rows = self._connection.execute(
            """
            SELECT direction_code, message_text
            FROM admin_follow_up_messages
            WHERE admin_follow_up_queue_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (follow_up_id,),
        ).fetchall()
        return tuple((str(row["direction_code"]), str(row["message_text"])) for row in rows)

    def _insert_follow_up_message(
        self,
        *,
        follow_up_id: str,
        direction_code: str,
        message_text: str,
        actor_type: str,
        actor_id: str | None,
        created_at: str,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO admin_follow_up_messages (
              id,
              admin_follow_up_queue_id,
              direction_code,
              message_text,
              actor_type,
              actor_id,
              created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"followup_message_{uuid4().hex}",
                follow_up_id,
                direction_code,
                message_text,
                actor_type,
                actor_id,
                created_at,
            ),
        )

    def _insert_outbox_message(
        self,
        *,
        follow_up_id: str,
        chat_id: int,
        message_text: str,
        source: str,
        created_at: str,
    ) -> OutboxMessage:
        outbox_id = f"outbox_{uuid4().hex}"
        self._connection.execute(
            """
            INSERT INTO outbox_messages (
              id,
              admin_follow_up_queue_id,
              chat_id,
              message_text,
              delivery_state_code,
              source_code,
              created_at,
              updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                outbox_id,
                follow_up_id,
                chat_id,
                message_text,
                OutboxStatus.PENDING.value,
                source,
                created_at,
                created_at,
            ),
        )
        return OutboxMessage(
            outbox_id=outbox_id,
            follow_up_id=follow_up_id,
            chat_id=chat_id,
            text=message_text,
            status=OutboxStatus.PENDING,
            source=source,
            created_at=_parse_datetime(created_at),
            updated_at=_parse_datetime(created_at),
        )

    def _row_to_outbox(self, row) -> OutboxMessage:
        payload = dict(row)
        created_at = _parse_datetime(str(payload["created_at"]))
        updated_at = _parse_datetime(str(payload["updated_at"]))
        return OutboxMessage(
            outbox_id=str(payload["id"]),
            follow_up_id=str(payload.get("admin_follow_up_queue_id") or ""),
            chat_id=int(payload["chat_id"]),
            text=str(payload["message_text"]),
            status=OutboxStatus(str(payload["delivery_state_code"])),
            source=str(payload["source_code"]),
            created_at=created_at,
            updated_at=updated_at,
            error_message=payload.get("error_message"),
            retry_count=int(payload.get("retry_count") or 0),
        )
