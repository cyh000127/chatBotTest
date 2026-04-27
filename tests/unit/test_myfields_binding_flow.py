import asyncio
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.field_binding.states import (
    STATE_FIELD_BINDING_CODE,
    STATE_FIELD_BINDING_CONFIRM,
    STATE_FIELD_BINDING_LOCATION,
    STATE_FIELD_BINDING_METHOD,
    STATE_MYFIELDS_SUMMARY,
)
from PROJECT.dispatch.session_dispatcher import current_state, field_binding_draft, reset_session
from PROJECT.fields.binding import FieldBindingService
from PROJECT.settings import SqliteSettings
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


class FakeMessage:
    def __init__(self, text: str = "", *, location=None):
        self.text = text
        self.location = location
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


def _context(bot_data: dict) -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(args=[], user_data=user_data, bot_data=bot_data)


def _approved_runtime(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    invitation_repository = SqliteInvitationRepository(runtime.connection)
    onboarding_repository = SqliteOnboardingRepository(runtime.connection)
    invitation = invitation_repository.create_invitation()
    session = onboarding_repository.create_or_resume_from_invitation(
        invitation=invitation,
        provider_user_id="12345",
        provider_handle="farmer_user",
        preferred_locale_code="ko",
        chat_id=67890,
    )
    session = onboarding_repository.update_locale(session.id, "ko")
    session = onboarding_repository.update_name(session.id, "홍길동")
    session = onboarding_repository.update_phone(
        session.id,
        phone_raw="+855 12 345 678",
        phone_normalized="+85512345678",
    )
    onboarding_repository.submit_pending_approval(session.id)
    SqliteOnboardingAdminRepository(runtime.connection).approve_submission(session.id)
    field_repository = SqliteFieldRegistryRepository(runtime.connection)
    field_service = FieldBindingService(field_repository)
    bot_data = {
        "invitation_repository": invitation_repository,
        "onboarding_repository": onboarding_repository,
        "field_registry_repository": field_repository,
        "field_binding_service": field_service,
    }
    return runtime, field_repository, bot_data


def test_myfields_location_binding_flow_registers_field_and_updates_summary(tmp_path):
    runtime, field_repository, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        version = field_repository.create_registry_version(version_label="v1")
        field_repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        field_repository.publish_version(version.id)

        asyncio.run(commands.myfields_command(_message_update(message), context))
        assert current_state(context.user_data) == STATE_MYFIELDS_SUMMARY
        assert "등록된 농지가 없습니다" in message.replies[-1][0]

        asyncio.run(messages.button_callback(_callback_update("fieldbind:start", message), context))
        assert current_state(context.user_data) == STATE_FIELD_BINDING_METHOD

        asyncio.run(messages.button_callback(_callback_update("fieldbind:method:location", message), context))
        assert current_state(context.user_data) == STATE_FIELD_BINDING_LOCATION

        location_message = FakeMessage(location=SimpleNamespace(latitude=37.05, longitude=127.05, horizontal_accuracy=8.0))
        asyncio.run(messages.location_message(_message_update(location_message), context))

        assert current_state(context.user_data) == STATE_FIELD_BINDING_CONFIRM
        assert "FIELD-001" in location_message.replies[-1][0]

        asyncio.run(messages.button_callback(_callback_update("fieldbind:confirm", location_message), context))

        assert current_state(context.user_data) == STATE_MYFIELDS_SUMMARY
        assert "농지가 등록되었습니다" in location_message.replies[-1][0]
        assert "논 1 (FIELD-001)" in location_message.replies[-1][0]
    finally:
        runtime.close()


def test_myfields_location_fallback_to_field_code_flow(tmp_path):
    runtime, field_repository, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        version = field_repository.create_registry_version(version_label="v1")
        field_repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        field_repository.publish_version(version.id)

        asyncio.run(commands.myfields_command(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("fieldbind:start", message), context))
        asyncio.run(messages.button_callback(_callback_update("fieldbind:method:location", message), context))

        location_message = FakeMessage(location=SimpleNamespace(latitude=35.0, longitude=128.0, horizontal_accuracy=8.0))
        asyncio.run(messages.location_message(_message_update(location_message), context))

        assert current_state(context.user_data) == STATE_FIELD_BINDING_CODE
        assert "후보를 찾지 못했습니다" in location_message.replies[-1][0]

        code_message = FakeMessage(text="field-001")
        asyncio.run(messages.text_message(_message_update(code_message), context))

        assert current_state(context.user_data) == STATE_FIELD_BINDING_CONFIRM
        draft = field_binding_draft(context.user_data)
        assert draft is not None
        assert draft["requested_field_code"] == "FIELD-001"
        assert "FIELD-001" in code_message.replies[-1][0]
    finally:
        runtime.close()
