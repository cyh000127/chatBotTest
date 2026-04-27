import asyncio
from datetime import UTC, datetime, timedelta

from PROJECT.reminders.delivery import deliver_due_reminders
from PROJECT.settings import SqliteSettings
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.reminders import REMINDER_STATUS_SENT, SqliteReminderRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


class FakeBot:
    def __init__(self):
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str):
        self.messages.append((chat_id, text))


def test_deliver_due_reminders_marks_message_sent(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    repository = SqliteReminderRepository(runtime.connection)
    invitation_repository = SqliteInvitationRepository(runtime.connection)
    onboarding_repository = SqliteOnboardingRepository(runtime.connection)
    field_repository = SqliteFieldRegistryRepository(runtime.connection)

    try:
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
        participant = field_repository.find_active_participant_context(provider_user_id="12345")
        assert participant is not None

        reminder = repository.create_reminder(
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            provider_user_id="12345",
            chat_id=67890,
            resume_target_code="input_resolve",
            reminder_type_code="input_resolution_retry_later",
            due_at=(datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
            message_text="/start rt_test",
            resume_token="rt_test",
        )

        bot = FakeBot()
        delivered = asyncio.run(deliver_due_reminders(bot, repository))

        assert delivered == 1
        assert bot.messages == [(67890, "/start rt_test")]
        updated = repository.get_reminder(reminder.id)
        assert updated is not None
        assert updated.reminder_status_code == REMINDER_STATUS_SENT
    finally:
        runtime.close()
