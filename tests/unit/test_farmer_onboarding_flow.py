import asyncio
import json
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.onboarding.states import (
    STATE_ONBOARDING_CONFIRM,
    STATE_ONBOARDING_PENDING_APPROVAL,
    STATE_ONBOARDING_PHONE,
)
from PROJECT.dispatch.session_dispatcher import current_state, get_session, reset_session
from PROJECT.settings import SqliteSettings
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import ONBOARDING_STATUS_PENDING_APPROVAL, SqliteOnboardingRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


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


def _repositories(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    invitation_repository = SqliteInvitationRepository(runtime.connection)
    onboarding_repository = SqliteOnboardingRepository(runtime.connection)
    return runtime, invitation_repository, onboarding_repository


def test_farmer_onboarding_happy_path_reaches_pending_approval(tmp_path):
    runtime, invitation_repository, onboarding_repository = _repositories(tmp_path)
    message = FakeMessage()

    try:
        invitation = invitation_repository.create_invitation()
        context = _context(
            args=[invitation.invite_code],
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.start_command(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("language:en", message), context))
        message.text = "Sample Farmer"
        asyncio.run(messages.text_message(_message_update(message), context))
        message.text = "+855 12 345 678"
        asyncio.run(messages.text_message(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("onboarding:confirm", message), context))

        session = onboarding_repository.get_by_id(get_session(context.user_data)["onboarding_session_id"])
        assert session is not None
        draft = json.loads(session.draft_payload_json)
        assert session.session_status_code == ONBOARDING_STATUS_PENDING_APPROVAL
        assert session.current_step_code == STATE_ONBOARDING_PENDING_APPROVAL
        assert draft["name"] == "Sample Farmer"
        assert draft["phone_normalized"] == "+85512345678"
        assert draft["preferred_locale"] == "en"
        assert runtime.connection.execute("SELECT COUNT(*) FROM participants").fetchone()[0] == 0
        assert runtime.connection.execute("SELECT COUNT(*) FROM project_enrollments").fetchone()[0] == 0
    finally:
        runtime.close()


def test_farmer_onboarding_rejects_unsupported_phone_country_code(tmp_path):
    runtime, invitation_repository, onboarding_repository = _repositories(tmp_path)
    message = FakeMessage()

    try:
        invitation = invitation_repository.create_invitation()
        context = _context(
            args=[invitation.invite_code],
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.start_command(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("language:ko", message), context))
        message.text = "홍길동"
        asyncio.run(messages.text_message(_message_update(message), context))
        message.text = "+82 10 1234 5678"
        asyncio.run(messages.text_message(_message_update(message), context))

        session = onboarding_repository.get_by_id(get_session(context.user_data)["onboarding_session_id"])
        assert session is not None
        draft = json.loads(session.draft_payload_json)
        assert current_state(context.user_data) == STATE_ONBOARDING_PHONE
        assert session.current_step_code == STATE_ONBOARDING_PHONE
        assert "phone_normalized" not in draft
        assert "다시 입력" in message.replies[-1][0]
    finally:
        runtime.close()


def test_start_with_existing_invitation_resumes_latest_onboarding_step(tmp_path):
    runtime, invitation_repository, onboarding_repository = _repositories(tmp_path)
    first_message = FakeMessage()
    second_message = FakeMessage()

    try:
        invitation = invitation_repository.create_invitation()
        bot_data = {
            "invitation_repository": invitation_repository,
            "onboarding_repository": onboarding_repository,
        }
        first_context = _context(args=[invitation.invite_code], bot_data=bot_data)

        asyncio.run(commands.start_command(_message_update(first_message), first_context))
        asyncio.run(messages.button_callback(_callback_update("language:ko", first_message), first_context))
        first_message.text = "홍길동"
        asyncio.run(messages.text_message(_message_update(first_message), first_context))

        second_context = _context(args=[invitation.invite_code], bot_data=bot_data)
        asyncio.run(commands.start_command(_message_update(second_message), second_context))

        assert current_state(second_context.user_data) == STATE_ONBOARDING_PHONE
        assert "전화번호" in second_message.replies[-1][0]
        assert get_session(second_context.user_data)["onboarding_session_id"] == get_session(first_context.user_data)["onboarding_session_id"]
    finally:
        runtime.close()


def test_onboarding_confirm_edit_returns_to_selected_field(tmp_path):
    runtime, invitation_repository, onboarding_repository = _repositories(tmp_path)
    message = FakeMessage()

    try:
        invitation = invitation_repository.create_invitation()
        context = _context(
            args=[invitation.invite_code],
            bot_data={
                "invitation_repository": invitation_repository,
                "onboarding_repository": onboarding_repository,
            },
        )

        asyncio.run(commands.start_command(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("language:ko", message), context))
        message.text = "홍길동"
        asyncio.run(messages.text_message(_message_update(message), context))
        message.text = "+880 17 1234 5678"
        asyncio.run(messages.text_message(_message_update(message), context))
        assert current_state(context.user_data) == STATE_ONBOARDING_CONFIRM

        asyncio.run(messages.button_callback(_callback_update("onboarding:edit:name", message), context))

        session = onboarding_repository.get_by_id(get_session(context.user_data)["onboarding_session_id"])
        assert session is not None
        assert current_state(context.user_data) == "name_input"
        assert session.current_step_code == "name_input"
    finally:
        runtime.close()
