import asyncio
from types import SimpleNamespace

from PROJECT.admin.follow_up import InMemoryAdminRuntime
from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.conversations.input_resolve.states import (
    STATE_INPUT_RESOLVE_CANDIDATES,
    STATE_INPUT_RESOLVE_DECISION,
    STATE_INPUT_RESOLVE_RAW_INPUT,
    STATE_INPUT_RESOLVE_TARGET,
)
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import current_state, input_resolution_draft, reset_session
from PROJECT.settings import SqliteSettings
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.input_resolution import SqliteInputResolutionRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.reminders import REMINDER_STATUS_COMPLETED, REMINDER_STATUS_PENDING, SqliteReminderRepository
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


def _context(bot_data: dict, *, args: list[str] | None = None) -> SimpleNamespace:
    user_data: dict = {}
    reset_session(user_data)
    return SimpleNamespace(args=args or [], user_data=user_data, bot_data=bot_data)


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
    input_resolution_repository = SqliteInputResolutionRepository(runtime.connection)
    reminder_repository = SqliteReminderRepository(runtime.connection)
    admin_runtime = InMemoryAdminRuntime()

    bot_data = {
        "invitation_repository": invitation_repository,
        "onboarding_repository": onboarding_repository,
        "field_registry_repository": field_repository,
        "input_resolution_repository": input_resolution_repository,
        "reminder_repository": reminder_repository,
        "admin_runtime": admin_runtime,
    }
    return runtime, field_repository, input_resolution_repository, reminder_repository, admin_runtime, bot_data


def _publish_field(field_repository: SqliteFieldRegistryRepository, *, code: str = "FIELD-001", name: str = "논 1"):
    version = field_repository.create_registry_version(version_label="v1")
    field_repository.import_field(
        field_registry_version_id=version.id,
        field_code=code,
        display_name=name,
        polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
    )
    field_repository.publish_version(version.id)


def test_input_resolution_flow_resolves_field_candidate(tmp_path):
    runtime, field_repository, resolution_repository, _, _, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        _publish_field(field_repository)

        asyncio.run(commands.input_resolve_command(_message_update(message), context))
        assert current_state(context.user_data) == STATE_INPUT_RESOLVE_TARGET
        draft = input_resolution_draft(context.user_data)
        assert draft is not None

        asyncio.run(messages.button_callback(_callback_update("inputresolve:target:field_code", message), context))
        assert current_state(context.user_data) == "input_resolve_method"

        asyncio.run(messages.button_callback(_callback_update("inputresolve:method:typed_text", message), context))
        assert current_state(context.user_data) == STATE_INPUT_RESOLVE_RAW_INPUT

        raw_input_message = FakeMessage(text="field-001")
        asyncio.run(messages.text_message(_message_update(raw_input_message), context))
        assert current_state(context.user_data) == STATE_INPUT_RESOLVE_CANDIDATES
        draft = input_resolution_draft(context.user_data)
        assert draft is not None
        assert draft["latest_candidates"][0]["label"] == "논 1 (FIELD-001)"

        candidate_id = draft["latest_candidates"][0]["candidate_id"]
        asyncio.run(messages.button_callback(_callback_update(f"inputresolve:candidate:{candidate_id}", raw_input_message), context))
        assert current_state(context.user_data) == STATE_INPUT_RESOLVE_DECISION

        asyncio.run(messages.button_callback(_callback_update("inputresolve:decision:resolved", raw_input_message), context))
        assert current_state(context.user_data) == STATE_MAIN_MENU

        stored_session = resolution_repository.get_session(draft["session_id"])
        assert stored_session is not None
        assert stored_session.session_status_code == "resolved"
        assert stored_session.resolved_value == {
            "binding_scope": "project_registry",
            "display_name": "논 1",
            "field_code": "FIELD-001",
            "field_id": stored_session.resolved_value["field_id"],
        }
    finally:
        runtime.close()


def test_input_resolution_retry_later_creates_reminder_and_resumes_from_start(tmp_path):
    runtime, field_repository, resolution_repository, reminder_repository, _, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        _publish_field(field_repository)

        asyncio.run(commands.input_resolve_command(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("inputresolve:target:field_name", message), context))
        asyncio.run(messages.button_callback(_callback_update("inputresolve:method:typed_text", message), context))

        raw_input_message = FakeMessage(text="없는 농지")
        asyncio.run(messages.text_message(_message_update(raw_input_message), context))
        assert current_state(context.user_data) == STATE_INPUT_RESOLVE_CANDIDATES

        draft = input_resolution_draft(context.user_data)
        assert draft is not None
        session_id = draft["session_id"]
        asyncio.run(messages.button_callback(_callback_update("inputresolve:retry_later", raw_input_message), context))

        assert current_state(context.user_data) == STATE_MAIN_MENU
        reminders = reminder_repository.list_reminders(status=REMINDER_STATUS_PENDING)
        assert len(reminders) == 1
        reminder = reminders[0]
        assert reminder.input_resolution_session_id == session_id
        assert reminder.resume_target_code == "input_resolve"
        assert reminder.resume_token in reminder.message_text

        resume_context = _context(bot_data, args=[reminder.resume_token])
        resume_message = FakeMessage()
        asyncio.run(commands.start_command(_message_update(resume_message), resume_context))

        assert current_state(resume_context.user_data) == STATE_INPUT_RESOLVE_RAW_INPUT
        resumed_draft = input_resolution_draft(resume_context.user_data)
        assert resumed_draft is not None
        assert resumed_draft["session_id"] == session_id

        updated_reminder = reminder_repository.get_reminder(reminder.id)
        assert updated_reminder is not None
        assert updated_reminder.reminder_status_code == REMINDER_STATUS_COMPLETED

        stored_session = resolution_repository.get_session(session_id)
        assert stored_session is not None
        assert stored_session.current_step_code == STATE_INPUT_RESOLVE_RAW_INPUT
    finally:
        runtime.close()


def test_input_resolution_manual_review_creates_follow_up(tmp_path):
    runtime, field_repository, resolution_repository, _, admin_runtime, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        _publish_field(field_repository)

        asyncio.run(commands.input_resolve_command(_message_update(message), context))
        asyncio.run(messages.button_callback(_callback_update("inputresolve:target:field_name", message), context))
        asyncio.run(messages.button_callback(_callback_update("inputresolve:method:typed_text", message), context))

        raw_input_message = FakeMessage(text="모르는 값")
        asyncio.run(messages.text_message(_message_update(raw_input_message), context))
        draft = input_resolution_draft(context.user_data)
        assert draft is not None
        session_id = draft["session_id"]

        asyncio.run(messages.button_callback(_callback_update("inputresolve:manual_review", raw_input_message), context))

        assert current_state(context.user_data) == STATE_MAIN_MENU
        stored_session = resolution_repository.get_session(session_id)
        assert stored_session is not None
        assert stored_session.session_status_code == "manual_review_required"

        follow_ups = admin_runtime.list_follow_ups(include_closed=True)
        assert len(follow_ups) == 1
        assert follow_ups[0].reason == "input_resolution_manual_review"
        assert "input_resolve target=field_name" in follow_ups[0].user_message
    finally:
        runtime.close()
