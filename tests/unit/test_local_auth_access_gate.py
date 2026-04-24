import asyncio
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_USED
from PROJECT.conversations.sample_menu.states import STATE_AUTH_LOGIN, STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import current_state, is_authenticated, reset_session


def _update(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=SimpleNamespace(text=text),
        effective_user=SimpleNamespace(id=10, username="local_user"),
        effective_chat=SimpleNamespace(id=20),
    )


def _context(*, args=None) -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(args=args or [], user_data=user_data, bot_data={})


def test_local_start_without_login_id_prompts_for_auth(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.start_command(_update("/start"), context))

    assert current_state(context.user_data) == STATE_AUTH_LOGIN
    assert is_authenticated(context.user_data) is False
    assert "아이디" in sent[0]


def test_local_text_before_start_is_blocked(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context = _context()

    asyncio.run(messages.text_message(_update("비료 입력"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert is_authenticated(context.user_data) is False
    assert "인증" in sent[0]


def test_local_start_with_login_id_authenticates_and_allows_feature(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context(args=["sample-user"])

    asyncio.run(commands.start_command(_update("/start sample-user"), context))
    asyncio.run(commands.fertilizer_command(_update("/fertilizer"), context))

    assert is_authenticated(context.user_data) is True
    assert current_state(context.user_data) == STATE_FERTILIZER_USED
    assert any("어서오세요" in message for message in sent)


def test_local_auth_failure_twice_requires_start_again(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.start_command(_update("/start"), context))
    asyncio.run(messages.text_message(_update("wrong-one"), context))
    asyncio.run(messages.text_message(_update("wrong-two"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert is_authenticated(context.user_data) is False
    assert "두 번 실패" in sent[-1]
