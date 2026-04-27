import asyncio
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_USED
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import current_state, has_started, is_authenticated, reset_session


def _update(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=SimpleNamespace(text=text),
        effective_user=SimpleNamespace(id=10, username="local_user"),
        effective_chat=SimpleNamespace(id=20),
    )


def _callback_update(data: str) -> SimpleNamespace:
    message = SimpleNamespace(text="")
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=10, username="local_user"),
        effective_chat=SimpleNamespace(id=20),
        callback_query=SimpleNamespace(data=data),
    )


def _context(*, args=None) -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(args=args or [], user_data=user_data, bot_data={})


def test_local_start_without_sqlite_opens_main_menu(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.start_command(_update("/start"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert has_started(context.user_data) is True
    assert is_authenticated(context.user_data) is False
    assert "메인 메뉴" in sent[0]


def test_local_start_ignores_legacy_login_id_argument(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context(args=["sample-user"])

    asyncio.run(commands.start_command(_update("/start sample-user"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert has_started(context.user_data) is True
    assert is_authenticated(context.user_data) is False
    assert "메인 메뉴" in sent[0]


def test_local_text_before_start_is_blocked(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context = _context()

    asyncio.run(messages.text_message(_update("비료 입력"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert has_started(context.user_data) is False
    assert "start" in sent[0].lower()


def test_local_command_before_start_is_blocked(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.help_command(_update("/help"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert has_started(context.user_data) is False
    assert "start" in sent[0].lower()


def test_local_callback_before_start_is_blocked(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context = _context()

    asyncio.run(messages.button_callback(_callback_update("intent:agri.input.start"), context))

    assert current_state(context.user_data) == STATE_MAIN_MENU
    assert has_started(context.user_data) is False
    assert "start" in sent[0].lower()


def test_local_feature_after_start_is_allowed(monkeypatch):
    sent: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context = _context()

    asyncio.run(commands.start_command(_update("/start"), context))
    asyncio.run(commands.fertilizer_command(_update("/fertilizer"), context))

    assert has_started(context.user_data) is True
    assert current_state(context.user_data) == STATE_FERTILIZER_USED
    assert sent
