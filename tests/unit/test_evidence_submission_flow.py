import asyncio
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers import commands, messages
from PROJECT.evidence import EvidenceSubmissionService
from PROJECT.conversations.evidence_submission.states import STATE_EVIDENCE_WAITING_DOCUMENT, STATE_EVIDENCE_WAITING_LOCATION
from PROJECT.dispatch.session_dispatcher import current_state, evidence_submission_draft, reset_session
from PROJECT.fields.binding import FIELD_CODE_BINDING_SOURCE
from PROJECT.settings import SqliteSettings
from PROJECT.storage.evidence import EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT, SqliteEvidenceRepository
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


class FakeDocument:
    def __init__(
        self,
        *,
        file_id: str = "file_123",
        file_unique_id: str = "unique_123",
        file_name: str = "field.jpg",
        mime_type: str = "image/jpeg",
        file_size: int = 2048,
    ) -> None:
        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size


class FakeMessage:
    def __init__(self, text: str = "", *, location=None, document=None):
        self.text = text
        self.location = location
        self.document = document
        self.replies: list[tuple[str, object | None]] = []
        self.cleared = False
        self.message_id = 777

    async def reply_text(self, text: str, reply_markup=None):
        self.replies.append((text, reply_markup))

    async def edit_reply_markup(self, reply_markup=None):
        self.cleared = True


def _message_update(message: FakeMessage, *, user_id: int = 12345) -> SimpleNamespace:
    return SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=user_id, username="farmer_user"),
        effective_chat=SimpleNamespace(id=67890),
        callback_query=None,
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
    evidence_repository = SqliteEvidenceRepository(runtime.connection)
    evidence_service = EvidenceSubmissionService(evidence_repository, field_repository)
    bot_data = {
        "invitation_repository": invitation_repository,
        "onboarding_repository": onboarding_repository,
        "field_registry_repository": field_repository,
        "evidence_repository": evidence_repository,
        "evidence_submission_service": evidence_service,
    }
    return runtime, field_repository, evidence_repository, bot_data


def _bind_field(field_repository: SqliteFieldRegistryRepository):
    participant = field_repository.find_active_participant_context(provider_user_id="12345")
    assert participant is not None
    version = field_repository.create_registry_version(version_label="v1", project_id=participant.project_id)
    record = field_repository.import_field(
        field_registry_version_id=version.id,
        field_code="FIELD-001",
        display_name="논 1",
        polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
    )
    field_repository.publish_version(version.id)
    field_repository.create_binding(
        participant_id=participant.participant_id,
        project_id=participant.project_id,
        field_id=record.field.id,
        field_registry_version_id=version.id,
        binding_source_code=FIELD_CODE_BINDING_SOURCE,
        provider_user_id="12345",
        chat_id=67890,
        requested_field_code="FIELD-001",
    )


def test_evidence_command_starts_location_first_flow(tmp_path):
    runtime, field_repository, evidence_repository, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        _bind_field(field_repository)

        asyncio.run(commands.evidence_command(_message_update(message), context))

        assert current_state(context.user_data) == STATE_EVIDENCE_WAITING_LOCATION
        draft = evidence_submission_draft(context.user_data)
        assert draft is not None
        assert draft["session_id"].startswith("evidence_session_")
        assert draft["request_event_id"].startswith("evidence_request_")
        assert "현재 위치" in message.replies[-1][0]

        session = evidence_repository.get_submission_session(draft["session_id"])
        assert session is not None
        assert session.session_status_code == "waiting_location"
    finally:
        runtime.close()


def test_evidence_document_before_location_shows_location_fallback(tmp_path):
    runtime, field_repository, evidence_repository, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        _bind_field(field_repository)

        asyncio.run(commands.evidence_command(_message_update(message), context))
        document_message = FakeMessage(document=FakeDocument())
        asyncio.run(messages.document_message(_message_update(document_message), context))

        assert current_state(context.user_data) == STATE_EVIDENCE_WAITING_LOCATION
        assert "증빙 제출 단계를 처리하지 못했습니다" in document_message.replies[-1][0]
        draft = evidence_submission_draft(context.user_data)
        assert draft is not None
        assert evidence_repository.list_submissions_for_session(draft["session_id"]) == ()
    finally:
        runtime.close()


def test_evidence_location_and_document_flow_requests_document_retry_when_metadata_is_missing(tmp_path):
    runtime, field_repository, evidence_repository, bot_data = _approved_runtime(tmp_path)
    context = _context(bot_data)
    message = FakeMessage()

    try:
        _bind_field(field_repository)

        asyncio.run(commands.evidence_command(_message_update(message), context))

        location_message = FakeMessage(
            location=SimpleNamespace(latitude=37.05, longitude=127.05, horizontal_accuracy=8.0)
        )
        asyncio.run(messages.location_message(_message_update(location_message), context))

        assert current_state(context.user_data) == STATE_EVIDENCE_WAITING_DOCUMENT
        draft = evidence_submission_draft(context.user_data)
        assert draft is not None
        assert draft["accepted_location"] is True
        assert "document" in location_message.replies[-1][0]

        document_message = FakeMessage(document=FakeDocument())
        asyncio.run(messages.document_message(_message_update(document_message), context))

        assert current_state(context.user_data) == STATE_EVIDENCE_WAITING_DOCUMENT
        updated_draft = evidence_submission_draft(context.user_data)
        assert updated_draft is not None
        assert updated_draft["document_uploaded"] is True
        assert updated_draft["evidence_submission_id"].startswith("evidence_submission_")
        assert updated_draft["file_name"] == "field.jpg"
        assert "증빙을 다시 제출해 주세요" in document_message.replies[-1][0]
        assert "EXIF 정보가 없습니다" in document_message.replies[-1][0]

        session = evidence_repository.get_submission_session(updated_draft["session_id"])
        assert session is not None
        assert session.session_status_code == EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT
        submissions = evidence_repository.list_submissions_for_session(updated_draft["session_id"])
        assert len(submissions) == 1
        logs = evidence_repository.list_state_logs(submissions[0].id)
        assert logs[-1].to_state_code == "rejected"
    finally:
        runtime.close()
