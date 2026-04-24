import pytest

from PROJECT.settings import SqliteSettings
from PROJECT.storage.invitations import INVITATION_STATUS_USED, SqliteInvitationRepository
from PROJECT.storage.onboarding import (
    ONBOARDING_STATUS_APPROVED,
    ONBOARDING_STATUS_PENDING_APPROVAL,
    ONBOARDING_STATUS_REJECTED,
    SqliteOnboardingRepository,
)
from PROJECT.storage.onboarding_admin import (
    ENROLLMENT_STATUS_ACTIVE,
    OnboardingApprovalError,
    OUTBOX_SOURCE_ONBOARDING_APPROVED,
    OUTBOX_SOURCE_ONBOARDING_REJECTED,
    OUTBOX_STATUS_PENDING,
    SqliteOnboardingAdminRepository,
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
    return (
        runtime,
        SqliteInvitationRepository(runtime.connection),
        SqliteOnboardingRepository(runtime.connection),
        SqliteOnboardingAdminRepository(runtime.connection),
    )


def create_pending_submission(tmp_path):
    runtime, invitation_repository, onboarding_repository, admin_repository = bootstrap_repositories(tmp_path)
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
    session = onboarding_repository.submit_pending_approval(session.id)
    return runtime, invitation, session, admin_repository


def test_onboarding_admin_repository_lists_pending_submissions(tmp_path):
    runtime, invitation, session, admin_repository = create_pending_submission(tmp_path)

    try:
        submissions = admin_repository.list_pending_submissions()

        assert len(submissions) == 1
        assert submissions[0].onboarding_session_id == session.id
        assert submissions[0].project_invitation_id == invitation.id
        assert submissions[0].name == "홍길동"
        assert submissions[0].phone_normalized == "+85512345678"
    finally:
        runtime.close()


def test_onboarding_admin_repository_approval_creates_participant_enrollment_and_outbox(tmp_path):
    runtime, invitation, session, admin_repository = create_pending_submission(tmp_path)

    try:
        result = admin_repository.approve_submission(session.id, message_text="승인되었습니다.")

        approved_session = result.session
        enrollment = runtime.connection.execute(
            "SELECT * FROM project_enrollments WHERE id = ?",
            (result.enrollment_id,),
        ).fetchone()
        contact = runtime.connection.execute(
            "SELECT * FROM participant_private_contacts WHERE id = ?",
            (result.contact_id,),
        ).fetchone()
        identity = runtime.connection.execute(
            "SELECT * FROM participant_identities WHERE id = ?",
            (result.identity_id,),
        ).fetchone()
        used_invitation = runtime.connection.execute(
            "SELECT * FROM project_invitations WHERE id = ?",
            (invitation.id,),
        ).fetchone()
        outbox = runtime.connection.execute(
            "SELECT * FROM outbox_messages WHERE id = ?",
            (result.outbox_id,),
        ).fetchone()

        assert approved_session.session_status_code == ONBOARDING_STATUS_APPROVED
        assert approved_session.result_participant_id == result.participant_id
        assert approved_session.result_enrollment_id == result.enrollment_id
        assert enrollment["enrollment_status_code"] == ENROLLMENT_STATUS_ACTIVE
        assert enrollment["participant_id"] == result.participant_id
        assert contact["normalized_value"] == "+85512345678"
        assert identity["provider_user_id"] == "12345"
        assert used_invitation["invite_status_code"] == INVITATION_STATUS_USED
        assert used_invitation["accepted_participant_id"] == result.participant_id
        assert outbox["chat_id"] == 67890
        assert outbox["message_text"] == "승인되었습니다."
        assert outbox["delivery_state_code"] == OUTBOX_STATUS_PENDING
        assert outbox["source_code"] == OUTBOX_SOURCE_ONBOARDING_APPROVED
    finally:
        runtime.close()


def test_onboarding_admin_repository_rejection_does_not_create_participant_or_enrollment(tmp_path):
    runtime, _, session, admin_repository = create_pending_submission(tmp_path)

    try:
        result = admin_repository.reject_submission(session.id, message_text="반려되었습니다.")
        participants = runtime.connection.execute("SELECT COUNT(*) FROM participants").fetchone()[0]
        enrollments = runtime.connection.execute("SELECT COUNT(*) FROM project_enrollments").fetchone()[0]
        outbox = runtime.connection.execute(
            "SELECT * FROM outbox_messages WHERE id = ?",
            (result.outbox_id,),
        ).fetchone()

        assert result.session.session_status_code == ONBOARDING_STATUS_REJECTED
        assert participants == 0
        assert enrollments == 0
        assert outbox["message_text"] == "반려되었습니다."
        assert outbox["source_code"] == OUTBOX_SOURCE_ONBOARDING_REJECTED
    finally:
        runtime.close()


def test_onboarding_admin_repository_rejects_duplicate_approval(tmp_path):
    runtime, _, session, admin_repository = create_pending_submission(tmp_path)

    try:
        admin_repository.approve_submission(session.id)

        with pytest.raises(OnboardingApprovalError):
            admin_repository.approve_submission(session.id)
    finally:
        runtime.close()


def test_onboarding_admin_repository_requires_pending_status(tmp_path):
    runtime, _, session, admin_repository = create_pending_submission(tmp_path)

    try:
        assert session.session_status_code == ONBOARDING_STATUS_PENDING_APPROVAL
        admin_repository.reject_submission(session.id)

        with pytest.raises(OnboardingApprovalError):
            admin_repository.reject_submission(session.id)
    finally:
        runtime.close()
