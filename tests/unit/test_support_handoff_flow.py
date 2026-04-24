import asyncio
from types import SimpleNamespace

from PROJECT.admin.follow_up import admin_runtime
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import active_follow_up_id, authenticate_session, reset_session, support_handoff
from PROJECT.settings import SqliteSettings
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime, open_sqlite_connection


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
    admin_runtime.clear()
    user_data: dict = {}
    reset_session(user_data)
    authenticate_session(user_data, login_id="sample-user", user_name="테스트 사용자")
    return SimpleNamespace(user_data=user_data, bot_data={})


def _sqlite_context(tmp_path) -> tuple[SimpleNamespace, object]:
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    user_data: dict = {}
    reset_session(user_data)
    authenticate_session(user_data, login_id="sample-user", user_name="테스트 사용자")
    context = SimpleNamespace(
        user_data=user_data,
        bot_data={"admin_runtime": SqliteAdminRuntime(sqlite_runtime.connection)},
    )
    return context, sqlite_runtime


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
    assert active_follow_up_id(context.user_data) == handoff.handoff_id
    assert admin_runtime.get_follow_up(handoff.handoff_id).user_messages == ("/support",)
    assert sent_messages


def test_support_guidance_uses_sqlite_admin_runtime(monkeypatch, tmp_path):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(commands, "send_text", fake_send_text)
    context, sqlite_runtime = _sqlite_context(tmp_path)

    try:
        asyncio.run(commands.show_support_guidance(_update("/support"), context))

        handoff = support_handoff(context.user_data)
        assert handoff is not None
        assert active_follow_up_id(context.user_data) == handoff.handoff_id

        loaded = context.bot_data["admin_runtime"].get_follow_up(handoff.handoff_id)
        assert loaded is not None
        assert loaded.route_hint == "support.escalate"
        assert loaded.user_messages == ("/support",)
        assert sent_messages
    finally:
        sqlite_runtime.close()


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
    assert active_follow_up_id(context.user_data) == handoff.handoff_id
    assert admin_runtime.get_follow_up(handoff.handoff_id).user_messages == ("상담원 연결해주세요",)
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
    assert admin_runtime.get_follow_up(handoff.handoff_id).user_messages == ("상담원 연결해주세요", "추가로 사진 업로드도 안 됩니다")
    assert any("추가 내용" in text for text in sent_messages)


def test_active_support_handoff_records_followup_message_in_sqlite(monkeypatch, tmp_path):
    sent_messages: list[str] = []

    async def fake_send_text(update, text, keyboard_layout=None):
        sent_messages.append(text)

    monkeypatch.setattr(messages, "send_text", fake_send_text)
    context, sqlite_runtime = _sqlite_context(tmp_path)
    database_path = sqlite_runtime.settings.database_path

    try:
        asyncio.run(messages.text_message(_update("상담원 연결해주세요"), context))
        asyncio.run(messages.text_message(_update("추가로 사진 업로드도 안 됩니다"), context))

        handoff = support_handoff(context.user_data)
        assert handoff is not None
        assert sent_messages
    finally:
        sqlite_runtime.close()

    reopened = open_sqlite_connection(SqliteSettings(database_path=database_path))
    try:
        loaded = SqliteAdminRuntime(reopened).get_follow_up(handoff.handoff_id)
        assert loaded is not None
        assert loaded.user_messages == ("상담원 연결해주세요", "추가로 사진 업로드도 안 됩니다")
    finally:
        reopened.close()


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
    assert active_follow_up_id(context.user_data) is None
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
    assert any("지원 이관이 종료" in text for text in sent_messages)
