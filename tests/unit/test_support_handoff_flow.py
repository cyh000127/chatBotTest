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


def test_active_support_handoff_records_followup_message(monkeypatch):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context = _context()

    asyncio.run(messages.text_message(_update("상담원 연결해주세요"), context))
    asyncio.run(messages.text_message(_update("추가로 사진 업로드도 안 됩니다"), context))

    handoff = support_handoff(context.user_data)
    assert handoff is not None
    assert handoff.user_messages == ("상담원 연결해주세요", "추가로 사진 업로드도 안 됩니다")
    assert any("추가 내용" in text for text in sent_messages)


def test_admin_reply_is_recorded_and_relayed_in_same_chat(monkeypatch):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.show_support_guidance(_update("/support"), context))
    relayed = asyncio.run(
        commands.relay_support_admin_reply(
            _update("admin"),
            context,
            admin_message="확인했습니다. 사진을 다시 보내주세요.",
        )
    )

    handoff = support_handoff(context.user_data)
    assert relayed is True
    assert handoff is not None
    assert handoff.admin_reply_count == 1
    assert handoff.awaiting_admin_reply is False
    assert handoff.admin_messages == ("확인했습니다. 사진을 다시 보내주세요.",)
    assert any("운영자 답변" in text for text in sent_messages)


def test_active_support_handoff_safe_exit_restarts_session(monkeypatch):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context = _context()

    asyncio.run(messages.text_message(_update("상담원 연결해주세요"), context))
    asyncio.run(messages.text_message(_update("처음부터"), context))

    assert support_handoff(context.user_data) is None
    assert any("메인 메뉴" in text for text in sent_messages)


def test_admin_can_close_support_handoff(monkeypatch):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.show_support_guidance(_update("/support"), context))
    closed = asyncio.run(commands.close_support_handoff_from_admin(_update("admin"), context))

    handoff = support_handoff(context.user_data)
    assert closed is True
    assert handoff is not None
    assert handoff.closed is True
    assert any("지원 이관을 종료" in text for text in sent_messages)
