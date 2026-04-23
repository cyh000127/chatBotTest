import asyncio
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import reset_session, support_handoff


class _Message:
    def __init__(self, text: str):
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str, reply_markup=None):
        self.replies.append(text)


def _update(text: str) -> SimpleNamespace:
    message = _Message(text)
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=10),
        effective_chat=SimpleNamespace(id=20),
    )


def _context() -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(user_data=user_data, bot_data={})


def test_support_guidance_creates_support_handoff(monkeypatch):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.show_support_guidance(_update("/support"), context))

    handoff = support_handoff(context.user_data)
    assert handoff is not None
    assert handoff.route_hint == "support.escalate"
    assert handoff.reason == "explicit_support_request"
    assert handoff.current_step == STATE_MAIN_MENU
    assert handoff.user_messages == ("/support",)
    assert sent_messages


def test_explicit_support_request_text_creates_support_handoff(monkeypatch):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context = _context()

    asyncio.run(messages.text_message(_update("상담원 연결해주세요"), context))

    handoff = support_handoff(context.user_data)
    assert handoff is not None
    assert handoff.route_hint == "support.escalate"
    assert handoff.reason == "user_requested_human_support"
    assert handoff.current_step == STATE_MAIN_MENU
    assert handoff.user_messages == ("상담원 연결해주세요",)
    assert sent_messages
