from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import (
    ADMIN_FOLLOW_UP_CLOSED,
    ADMIN_FOLLOW_UP_CREATED,
    ADMIN_FOLLOW_UP_USER_MESSAGE_ADDED,
    ADMIN_REPLY_CREATED,
    OUTBOX_MESSAGE_CREATED,
    OUTBOX_MESSAGE_REQUEUED,
)


class FollowUpStatus(StrEnum):
    WAITING_ADMIN_REPLY = "waiting_admin_reply"
    OPEN = "open"
    CLOSED = "closed"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"


FOLLOW_UP_CLOSED_NOTICE = (
    "지원 이관이 완료되었습니다.\n"
    "필요하면 이 대화창에서 다시 도움을 요청할 수 있습니다.\n"
    "처음부터 다시 진행하려면 /start 를 입력해주세요."
)

DEFAULT_OUTBOX_RETRY_BACKOFF_SECONDS = 30
DEFAULT_OUTBOX_MAX_RETRY_COUNT = 5


@dataclass(frozen=True)
class CommandRequest:
    request_id: str
    canonical_intent: str
    chat_id: int
    user_id: int | None
    current_step: str | None
    locale: str
    payload: dict[str, object | None]
    created_at: datetime


@dataclass(frozen=True)
class FollowUpItem:
    follow_up_id: str
    command_request_id: str
    route_hint: str
    reason: str
    chat_id: int
    user_id: int | None
    status: FollowUpStatus
    current_step: str | None
    locale: str
    recent_messages_summary: str
    failure_count: int
    user_message: str
    created_at: datetime
    updated_at: datetime
    awaiting_admin_reply: bool = True
    admin_reply_count: int = 0
    closed: bool = False
    user_messages: tuple[str, ...] = field(default_factory=tuple)
    admin_messages: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OutboxMessage:
    outbox_id: str
    follow_up_id: str
    chat_id: int
    text: str
    status: OutboxStatus
    source: str
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None
    retry_count: int = 0


def _now() -> datetime:
    return datetime.now(UTC)


class InMemoryAdminRuntime:
    """Process-local admin follow-up queue and delivery outbox."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._command_requests: dict[str, CommandRequest] = {}
        self._follow_ups: dict[str, FollowUpItem] = {}
        self._outbox: dict[str, OutboxMessage] = {}

    def clear(self) -> None:
        with self._lock:
            self._command_requests.clear()
            self._follow_ups.clear()
            self._outbox.clear()

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
        now = _now()
        request = CommandRequest(
            request_id=f"cmd_{uuid4().hex}",
            canonical_intent=route_hint,
            chat_id=chat_id,
            user_id=user_id,
            current_step=current_step,
            locale=locale,
            payload={
                "reason": reason,
                "user_message": user_message,
                "failure_count": failure_count,
                "recent_messages_summary": recent_messages_summary,
                "source": source,
            },
            created_at=now,
        )
        follow_up = FollowUpItem(
            follow_up_id=f"followup_{uuid4().hex}",
            command_request_id=request.request_id,
            route_hint=route_hint,
            reason=reason,
            chat_id=chat_id,
            user_id=user_id,
            status=FollowUpStatus.WAITING_ADMIN_REPLY,
            current_step=current_step,
            locale=locale,
            recent_messages_summary=recent_messages_summary,
            failure_count=failure_count,
            user_message=user_message,
            created_at=now,
            updated_at=now,
            user_messages=(user_message,) if user_message else (),
        )
        with self._lock:
            self._command_requests[request.request_id] = request
            self._follow_ups[follow_up.follow_up_id] = follow_up
        log_event(
            ADMIN_FOLLOW_UP_CREATED,
            source=source,
            follow_up_id=follow_up.follow_up_id,
            command_request_id=request.request_id,
            route_hint=follow_up.route_hint,
            reason=follow_up.reason,
            state=follow_up.current_step,
            failure_count=follow_up.failure_count,
        )
        return follow_up

    def list_command_requests(self) -> list[CommandRequest]:
        with self._lock:
            return list(self._command_requests.values())

    def list_follow_ups(self, *, include_closed: bool = True) -> list[FollowUpItem]:
        with self._lock:
            follow_ups = list(self._follow_ups.values())
        if not include_closed:
            follow_ups = [item for item in follow_ups if item.status != FollowUpStatus.CLOSED]
        return sorted(follow_ups, key=lambda item: item.created_at)

    def get_follow_up(self, follow_up_id: str) -> FollowUpItem | None:
        with self._lock:
            return self._follow_ups.get(follow_up_id)

    def append_user_message(
        self,
        follow_up_id: str,
        user_message: str,
        *,
        source: str = "runtime",
    ) -> FollowUpItem | None:
        with self._lock:
            follow_up = self._follow_ups.get(follow_up_id)
            if follow_up is None or follow_up.closed:
                return None
            updated = replace(
                follow_up,
                status=FollowUpStatus.WAITING_ADMIN_REPLY,
                awaiting_admin_reply=True,
                user_messages=(*follow_up.user_messages, user_message),
                updated_at=_now(),
            )
            self._follow_ups[follow_up_id] = updated
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
            follow_up = self._follow_ups.get(follow_up_id)
            if follow_up is None or follow_up.closed:
                return None
            now = _now()
            updated = replace(
                follow_up,
                status=FollowUpStatus.OPEN,
                awaiting_admin_reply=False,
                admin_reply_count=follow_up.admin_reply_count + 1,
                admin_messages=(*follow_up.admin_messages, admin_message),
                updated_at=now,
            )
            outbox_message = OutboxMessage(
                outbox_id=f"outbox_{uuid4().hex}",
                follow_up_id=follow_up_id,
                chat_id=follow_up.chat_id,
                text=admin_message,
                status=OutboxStatus.PENDING,
                source=source,
                created_at=now,
                updated_at=now,
            )
            self._follow_ups[follow_up_id] = updated
            self._outbox[outbox_message.outbox_id] = outbox_message
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
                outbox_id=outbox_message.outbox_id,
                follow_up_id=follow_up_id,
                chat_id=outbox_message.chat_id,
                status=outbox_message.status.value,
            )
            return updated, outbox_message

    def close_follow_up(
        self,
        follow_up_id: str,
        *,
        source: str = "runtime",
        notify_user: bool = False,
        notice_text: str = FOLLOW_UP_CLOSED_NOTICE,
    ) -> FollowUpItem | None:
        with self._lock:
            follow_up = self._follow_ups.get(follow_up_id)
            if follow_up is None:
                return None
            if follow_up.closed:
                return follow_up
            now = _now()
            updated = replace(
                follow_up,
                status=FollowUpStatus.CLOSED,
                awaiting_admin_reply=False,
                closed=True,
                updated_at=now,
            )
            self._follow_ups[follow_up_id] = updated
            if notify_user:
                outbox_message = OutboxMessage(
                    outbox_id=f"outbox_{uuid4().hex}",
                    follow_up_id=follow_up_id,
                    chat_id=follow_up.chat_id,
                    text=notice_text,
                    status=OutboxStatus.PENDING,
                    source=source,
                    created_at=now,
                    updated_at=now,
                )
                self._outbox[outbox_message.outbox_id] = outbox_message
                log_event(
                    OUTBOX_MESSAGE_CREATED,
                    source=source,
                    outbox_id=outbox_message.outbox_id,
                    follow_up_id=follow_up_id,
                    chat_id=outbox_message.chat_id,
                    status=outbox_message.status.value,
                )
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
            messages = list(self._outbox.values())
        if status is not None:
            messages = [message for message in messages if message.status == status]
        return sorted(messages, key=lambda message: message.created_at)

    def claim_pending_outbox(self, *, limit: int = 10) -> list[OutboxMessage]:
        with self._lock:
            now = _now()
            pending = [
                message
                for message in sorted(self._outbox.values(), key=lambda item: item.created_at)
                if _outbox_claimable(message, now=now)
            ][:limit]
            claimed: list[OutboxMessage] = []
            for message in pending:
                updated = replace(message, status=OutboxStatus.SENDING, error_message=None, updated_at=now)
                self._outbox[message.outbox_id] = updated
                claimed.append(updated)
            return claimed

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
            message = self._outbox.get(outbox_id)
            if message is None or message.status != OutboxStatus.MANUAL_REVIEW:
                return None
            updated = replace(
                message,
                status=OutboxStatus.PENDING,
                error_message=None,
                retry_count=0,
                updated_at=_now(),
            )
            self._outbox[outbox_id] = updated
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
            message = self._outbox.get(outbox_id)
            if message is None:
                return None
            retry_count = message.retry_count + 1 if status == OutboxStatus.FAILED else message.retry_count
            resolved_status = status
            if status == OutboxStatus.FAILED and retry_count >= DEFAULT_OUTBOX_MAX_RETRY_COUNT:
                resolved_status = OutboxStatus.MANUAL_REVIEW
            updated = replace(
                message,
                status=resolved_status,
                error_message=error_message,
                updated_at=_now(),
                retry_count=retry_count,
            )
            self._outbox[outbox_id] = updated
            return updated


def _outbox_claimable(message: OutboxMessage, *, now: datetime) -> bool:
    if message.status == OutboxStatus.PENDING:
        return True
    if message.status != OutboxStatus.FAILED:
        return False
    if message.retry_count >= DEFAULT_OUTBOX_MAX_RETRY_COUNT:
        return False
    backoff_seconds = DEFAULT_OUTBOX_RETRY_BACKOFF_SECONDS * max(message.retry_count, 1)
    return message.updated_at + timedelta(seconds=backoff_seconds) <= now


admin_runtime = InMemoryAdminRuntime()
