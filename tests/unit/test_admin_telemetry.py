import asyncio
from dataclasses import replace

from PROJECT.admin import delivery, follow_up
from PROJECT.admin.delivery import deliver_pending_outbox
from PROJECT.admin.follow_up import DEFAULT_OUTBOX_MAX_RETRY_COUNT, InMemoryAdminRuntime, OutboxStatus
from PROJECT.telemetry.events import (
    ADMIN_FOLLOW_UP_CREATED,
    ADMIN_REPLY_CREATED,
    OUTBOX_MESSAGE_CREATED,
    OUTBOX_MESSAGE_FAILED,
    OUTBOX_MESSAGE_MANUAL_REVIEW,
    OUTBOX_MESSAGE_SENT,
)


class FakeBot:
    def __init__(self, *, should_fail: bool = False):
        self.should_fail = should_fail

    async def send_message(self, *, chat_id: int, text: str):
        if self.should_fail:
            raise RuntimeError("transport down")


def test_admin_runtime_logs_follow_up_and_reply_events(monkeypatch):
    captured_events: list[str] = []
    monkeypatch.setattr(follow_up, "log_event", lambda event, **fields: captured_events.append(event))
    runtime = InMemoryAdminRuntime()

    item = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    runtime.create_admin_reply(item.follow_up_id, "확인했습니다.")

    assert captured_events == [
        ADMIN_FOLLOW_UP_CREATED,
        ADMIN_REPLY_CREATED,
        OUTBOX_MESSAGE_CREATED,
    ]


def test_outbox_delivery_logs_sent_and_failed_events(monkeypatch):
    captured_events: list[str] = []
    monkeypatch.setattr(delivery, "log_event", lambda event, **fields: captured_events.append(event))
    sent_runtime = InMemoryAdminRuntime()
    failed_runtime = InMemoryAdminRuntime()
    sent_follow_up = sent_runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    failed_follow_up = failed_runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=21,
        user_id=11,
        current_step="main_menu",
    )
    sent_runtime.create_admin_reply(sent_follow_up.follow_up_id, "확인했습니다.")
    failed_runtime.create_admin_reply(failed_follow_up.follow_up_id, "확인했습니다.")

    asyncio.run(deliver_pending_outbox(FakeBot(), runtime=sent_runtime))
    asyncio.run(deliver_pending_outbox(FakeBot(should_fail=True), runtime=failed_runtime))

    assert captured_events == [OUTBOX_MESSAGE_SENT, OUTBOX_MESSAGE_FAILED]


def test_outbox_delivery_logs_manual_review_event(monkeypatch):
    captured_events: list[str] = []
    monkeypatch.setattr(delivery, "log_event", lambda event, **fields: captured_events.append(event))
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "확인했습니다.")
    for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT - 1):
        runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")
    retryable = runtime.list_outbox()[0]
    runtime._outbox[outbox_message.outbox_id] = replace(retryable, status=OutboxStatus.PENDING)

    asyncio.run(deliver_pending_outbox(FakeBot(should_fail=True), runtime=runtime))

    assert captured_events[-2:] == [OUTBOX_MESSAGE_FAILED, OUTBOX_MESSAGE_MANUAL_REVIEW]
