import asyncio

from PROJECT.admin.delivery import deliver_pending_outbox
from PROJECT.admin.follow_up import InMemoryAdminRuntime, OutboxStatus


class FakeBot:
    def __init__(self, *, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str):
        if self.should_fail:
            raise RuntimeError("transport down")
        self.sent_messages.append((chat_id, text))


def _runtime_with_pending_outbox() -> tuple[InMemoryAdminRuntime, str]:
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "사진을 다시 보내주세요.")
    return runtime, outbox_message.outbox_id


def test_deliver_pending_outbox_sends_message_and_marks_sent():
    runtime, outbox_id = _runtime_with_pending_outbox()
    bot = FakeBot()

    delivered = asyncio.run(deliver_pending_outbox(bot, runtime=runtime))

    assert delivered == 1
    assert bot.sent_messages == [(20, "사진을 다시 보내주세요.")]
    assert runtime.list_outbox()[0].outbox_id == outbox_id
    assert runtime.list_outbox()[0].status == OutboxStatus.SENT


def test_deliver_pending_outbox_marks_failed_when_send_fails():
    runtime, outbox_id = _runtime_with_pending_outbox()
    bot = FakeBot(should_fail=True)

    delivered = asyncio.run(deliver_pending_outbox(bot, runtime=runtime))

    assert delivered == 0
    assert runtime.list_outbox()[0].outbox_id == outbox_id
    assert runtime.list_outbox()[0].status == OutboxStatus.FAILED
