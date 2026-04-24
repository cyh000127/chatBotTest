import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient

from PROJECT.admin.delivery import deliver_pending_outbox
from PROJECT.admin.follow_up import OutboxStatus
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.channels.telegram.app import create_application
from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_USED
from PROJECT.dispatch.session_dispatcher import active_follow_up_id, authenticate_session, current_state, get_session, reset_session
from PROJECT.policy import LocalAiGate
from PROJECT.settings import Settings, SqliteSettings
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime, open_sqlite_connection


class FakeMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.replies: list[tuple[str, object | None]] = []
        self.cleared = False

    async def reply_text(self, text: str, reply_markup=None):
        self.replies.append((text, reply_markup))

    async def edit_reply_markup(self, reply_markup=None):
        self.cleared = True


class FakeCallbackQuery:
    def __init__(self, data: str, message: FakeMessage):
        self.data = data
        self.message = message
        self.answered = False

    async def answer(self):
        self.answered = True


class FakeBot:
    def __init__(self):
        self.sent_messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str):
        self.sent_messages.append((chat_id, text))


def _message_update(message: FakeMessage, *, user_id: int = 12345) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=user_id, username="farmer_user"),
        effective_chat=SimpleNamespace(id=67890),
        callback_query=None,
    )


def _callback_update(data: str, message: FakeMessage, *, user_id: int = 12345) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=user_id, username="farmer_user"),
        effective_chat=SimpleNamespace(id=67890),
        callback_query=FakeCallbackQuery(data, message),
    )


def _context(*, args=None, bot_data=None) -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(args=args or [], user_data=user_data, bot_data=bot_data or {})


def _bootstrap(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    return sqlite_runtime


def _bot_data(connection) -> dict:
    return {
        "admin_runtime": SqliteAdminRuntime(connection),
        "invitation_repository": SqliteInvitationRepository(connection),
        "onboarding_repository": SqliteOnboardingRepository(connection),
    }


def test_sqlite_invitation_onboarding_approval_survives_restart_and_unlocks_feature(tmp_path):
    sqlite_runtime = _bootstrap(tmp_path)
    message = FakeMessage()
    try:
        bot_data = _bot_data(sqlite_runtime.connection)
        client = TestClient(
            create_admin_api_app(
                bot_data["admin_runtime"],
                invitation_repository=bot_data["invitation_repository"],
                onboarding_admin_repository=SqliteOnboardingAdminRepository(sqlite_runtime.connection),
            )
        )
        invitation = client.post("/admin/invitations", json={}).json()["invitation"]
        context = _context(args=[invitation["invite_code"]], bot_data=bot_data)

        asyncio.run(commands.start_command(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("language:ko", message), context))
        message.text = "홍길동"
        asyncio.run(messages.text_message(_message_update(message), context))
        message.text = "+855 12 345 678"
        asyncio.run(messages.text_message(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("onboarding:confirm", message), context))

        onboarding_session_id = get_session(context.user_data)["onboarding_session_id"]
        approval = client.post(f"/admin/onboarding/submissions/{onboarding_session_id}/approve", json={})

        assert approval.status_code == 200
    finally:
        sqlite_runtime.close()

    reopened = open_sqlite_connection(SqliteSettings(database_path=str(tmp_path / "runtime.sqlite3")))
    try:
        restored_bot_data = _bot_data(reopened)
        restored_context = _context(bot_data=restored_bot_data)
        restored_message = FakeMessage("/fertilizer")

        asyncio.run(commands.fertilizer_command(_message_update(restored_message), restored_context))

        assert current_state(restored_context.user_data) == STATE_FERTILIZER_USED
    finally:
        reopened.close()


def test_sqlite_support_handoff_admin_reply_delivery_survives_restart(tmp_path):
    sqlite_runtime = _bootstrap(tmp_path)
    message = FakeMessage("/support")
    try:
        bot_data = {"admin_runtime": SqliteAdminRuntime(sqlite_runtime.connection)}
        context = _context(bot_data=bot_data)
        authenticate_session(context.user_data, login_id="sample-user", user_name="테스트 사용자")

        asyncio.run(commands.support_command(_message_update(message), context))

        follow_up_id = active_follow_up_id(context.user_data)
        assert follow_up_id is not None
    finally:
        sqlite_runtime.close()

    reopened = open_sqlite_connection(SqliteSettings(database_path=str(tmp_path / "runtime.sqlite3")))
    try:
        runtime = SqliteAdminRuntime(reopened)
        client = TestClient(create_admin_api_app(runtime))
        reply = client.post(
            f"/admin/follow-ups/{follow_up_id}/reply",
            json={"message": "운영자 확인 결과, 다시 입력해주세요."},
        )
        bot = FakeBot()
        delivered = asyncio.run(deliver_pending_outbox(bot, runtime=runtime))

        assert reply.status_code == 200
        assert reply.json()["outbox_message"]["status"] == OutboxStatus.PENDING.value
        assert delivered == 1
        assert bot.sent_messages == [(67890, "운영자 확인 결과, 다시 입력해주세요.")]
        assert runtime.list_outbox()[0].status == OutboxStatus.SENT
    finally:
        reopened.close()


def test_sqlite_runtime_stays_rules_only_without_model_credentials(tmp_path):
    sqlite_runtime = _bootstrap(tmp_path)
    try:
        settings = Settings(
            bot_token="test-token",
            local_ai_gate=LocalAiGate.RECOVERY_ASSIST_ONLY,
        )
        application = create_application(settings, sqlite_runtime=sqlite_runtime)

        assert settings.llm_runtime_mode == "rules_only_disabled"
        assert settings.llm_recovery_runtime_enabled is False
        assert settings.llm_edit_intent_runtime_enabled is False
        assert application.bot_data["gemini_recovery_classifier"] is None
        assert application.bot_data["gemini_edit_intent_resolver"] is None
        assert isinstance(application.bot_data["admin_runtime"], SqliteAdminRuntime)
    finally:
        sqlite_runtime.close()
