import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient

from PROJECT.admin.delivery import deliver_pending_outbox
from PROJECT.admin.follow_up import OutboxStatus, admin_runtime
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.channels.telegram.handlers import commands
from PROJECT.dispatch.session_dispatcher import active_follow_up_id, reset_session


class FakeMessage:
    def __init__(self, text: str):
        self.text = text

    async def reply_text(self, text: str, reply_markup=None):
        return None


class FakeBot:
    def __init__(self):
        self.sent_messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str):
        self.sent_messages.append((chat_id, text))


def _update(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=FakeMessage(text),
        effective_user=SimpleNamespace(id=10),
        effective_chat=SimpleNamespace(id=20),
    )


def _context() -> SimpleNamespace:
    admin_runtime.clear()
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(user_data=user_data, bot_data={})


def test_support_command_to_admin_api_reply_to_telegram_delivery(monkeypatch):
    async def fake_send_text(update, text, keyboard_layout=None):
        return None

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.show_support_guidance(_update("/support"), context))
    follow_up_id = active_follow_up_id(context.user_data)
    client = TestClient(create_admin_api_app(admin_runtime))
    reply_response = client.post(
        f"/admin/follow-ups/{follow_up_id}/reply",
        json={"message": "운영자 확인 결과, 사진을 다시 보내주세요."},
    )
    bot = FakeBot()
    delivered = asyncio.run(deliver_pending_outbox(bot, runtime=admin_runtime))

    assert reply_response.status_code == 200
    assert reply_response.json()["outbox_message"]["status"] == OutboxStatus.PENDING.value
    assert delivered == 1
    assert bot.sent_messages == [(20, "운영자 확인 결과, 사진을 다시 보내주세요.")]
    assert admin_runtime.list_outbox()[0].status == OutboxStatus.SENT
