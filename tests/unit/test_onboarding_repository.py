import json

from PROJECT.settings import SqliteSettings
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import (
    ONBOARDING_EVENT_STARTED,
    ONBOARDING_STATUS_STARTED,
    ONBOARDING_STEP_LANGUAGE_SELECT,
    SqliteOnboardingRepository,
)
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def bootstrap_repositories(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    return runtime, SqliteInvitationRepository(runtime.connection), SqliteOnboardingRepository(runtime.connection)


def test_onboarding_repository_creates_session_from_invitation(tmp_path):
    runtime, invitation_repository, onboarding_repository = bootstrap_repositories(tmp_path)

    try:
        invitation = invitation_repository.create_invitation()
        session = onboarding_repository.create_or_resume_from_invitation(
            invitation=invitation,
            provider_user_id="12345",
            provider_handle="farmer_user",
            preferred_locale_code="ko",
        )
        events = runtime.connection.execute(
            "SELECT * FROM onboarding_session_events WHERE onboarding_session_id = ?",
            (session.id,),
        ).fetchall()

        assert session.id.startswith("onboarding_")
        assert session.provider_user_id == "12345"
        assert session.provider_handle == "farmer_user"
        assert session.project_invitation_id == invitation.id
        assert session.project_id == invitation.project_id
        assert session.session_status_code == ONBOARDING_STATUS_STARTED
        assert session.current_step_code == ONBOARDING_STEP_LANGUAGE_SELECT
        assert json.loads(session.draft_payload_json)["invite_code"] == invitation.invite_code
        assert len(events) == 1
        assert events[0]["event_type_code"] == ONBOARDING_EVENT_STARTED
    finally:
        runtime.close()


def test_onboarding_repository_resumes_existing_open_session(tmp_path):
    runtime, invitation_repository, onboarding_repository = bootstrap_repositories(tmp_path)

    try:
        invitation = invitation_repository.create_invitation()
        first = onboarding_repository.create_or_resume_from_invitation(
            invitation=invitation,
            provider_user_id="12345",
            provider_handle=None,
        )
        second = onboarding_repository.create_or_resume_from_invitation(
            invitation=invitation,
            provider_user_id="12345",
            provider_handle="updated_handle",
        )
        events = runtime.connection.execute(
            "SELECT * FROM onboarding_session_events WHERE onboarding_session_id = ?",
            (first.id,),
        ).fetchall()

        assert second.id == first.id
        assert second.provider_handle == "updated_handle"
        assert len(events) == 1
    finally:
        runtime.close()
