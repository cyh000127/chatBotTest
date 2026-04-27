import pytest

from PROJECT.evidence import (
    EVIDENCE_BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING,
    EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING,
    EvidenceSubmissionService,
)
from PROJECT.fields.binding import FIELD_CODE_BINDING_SOURCE
from PROJECT.settings import SqliteSettings
from PROJECT.storage.evidence import (
    EVIDENCE_SESSION_STATUS_VALIDATING,
    SqliteEvidenceRepository,
)
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def _runtime(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    return runtime


def _approve_participant(runtime, *, provider_user_id: str, name: str = "홍길동", chat_id: int = 67890):
    invitation_repository = SqliteInvitationRepository(runtime.connection)
    onboarding_repository = SqliteOnboardingRepository(runtime.connection)
    invitation = invitation_repository.create_invitation()
    session = onboarding_repository.create_or_resume_from_invitation(
        invitation=invitation,
        provider_user_id=provider_user_id,
        provider_handle=f"user_{provider_user_id}",
        preferred_locale_code="ko",
        chat_id=chat_id,
    )
    session = onboarding_repository.update_locale(session.id, "ko")
    session = onboarding_repository.update_name(session.id, name)
    session = onboarding_repository.update_phone(
        session.id,
        phone_raw="+855 12 345 678",
        phone_normalized=f"+855{provider_user_id[-4:]}1234",
    )
    session = onboarding_repository.submit_pending_approval(session.id)
    SqliteOnboardingAdminRepository(runtime.connection).approve_submission(session.id)
    return session


def _bind_field(repository, *, provider_user_id: str, field_code: str, display_name: str, polygon):
    participant = repository.find_active_participant_context(provider_user_id=provider_user_id)
    assert participant is not None
    version = repository.latest_published_version(project_id=participant.project_id)
    if version is None:
        version = repository.create_registry_version(version_label="v1", project_id=participant.project_id)
    record = repository.import_field(
        field_registry_version_id=version.id,
        field_code=field_code,
        display_name=display_name,
        polygon=polygon,
    )
    repository.publish_version(version.id)
    return repository.create_binding(
        participant_id=participant.participant_id,
        project_id=participant.project_id,
        field_id=record.field.id,
        field_registry_version_id=version.id,
        binding_source_code=FIELD_CODE_BINDING_SOURCE,
        provider_user_id=provider_user_id,
        chat_id=67890,
        requested_field_code=field_code,
    )


def test_evidence_repository_creates_submission_signal_and_state_log(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        field_repository = SqliteFieldRegistryRepository(runtime.connection)
        evidence_repository = SqliteEvidenceRepository(runtime.connection)
        participant = field_repository.find_active_participant_context(provider_user_id="1001")
        assert participant is not None

        request_event = evidence_repository.create_request_event(
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            request_type_code="field_photo",
            payload={"source": "test"},
        )
        session = evidence_repository.create_submission_session(
            evidence_request_event_id=request_event.id,
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            provider_user_id="1001",
            chat_id=67890,
        )
        session = evidence_repository.accept_location(
            session.id,
            latitude=37.55,
            longitude=127.01,
            accuracy_meters=8.5,
        )
        submission = evidence_repository.create_submission(
            evidence_submission_session_id=session.id,
            evidence_request_event_id=request_event.id,
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            provider_file_id="file_123",
            provider_file_unique_id="file_unique_123",
            file_name="field.jpg",
            mime_type="image/jpeg",
            payload={"capture_mode": "document"},
        )
        signal = evidence_repository.create_validation_signal(
            evidence_submission_id=submission.id,
            signal_type_code="exif_present",
            signal_status_code="present",
            detail={"source": "extractor"},
        )
        state = evidence_repository.append_state_log(
            evidence_submission_id=submission.id,
            to_state_code="uploaded",
            reason_code="document_received",
        )

        assert request_event.payload["source"] == "test"
        assert session.accepted_location_latitude == 37.55
        assert evidence_repository.list_submissions_for_session(session.id)[0].id == submission.id
        assert evidence_repository.list_validation_signals(submission.id)[0].id == signal.id
        assert evidence_repository.list_state_logs(submission.id)[0].id == state.id
    finally:
        runtime.close()


def test_evidence_service_uses_single_active_binding_for_request_context(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        field_repository = SqliteFieldRegistryRepository(runtime.connection)
        evidence_repository = SqliteEvidenceRepository(runtime.connection)
        service = EvidenceSubmissionService(evidence_repository, field_repository)
        binding = _bind_field(
            field_repository,
            provider_user_id="1001",
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )

        result = service.create_request(
            provider_user_id="1001",
            request_type_code="field_photo",
            request_reason_code="scheduled_check",
        )

        assert result.binding_resolution_code == EVIDENCE_BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING
        assert result.field_id == binding.field.id
        assert result.field_binding_id == binding.binding.id
        assert result.request_event.payload["binding_resolution_code"] == EVIDENCE_BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING
    finally:
        runtime.close()


def test_evidence_service_preserves_unresolved_request_without_binding(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        field_repository = SqliteFieldRegistryRepository(runtime.connection)
        evidence_repository = SqliteEvidenceRepository(runtime.connection)
        service = EvidenceSubmissionService(evidence_repository, field_repository)

        result = service.create_request(
            provider_user_id="1001",
            request_type_code="field_photo",
        )

        assert result.binding_resolution_code == EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING
        assert result.field_id is None
        assert result.request_event.payload["binding_resolution_code"] == EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING
    finally:
        runtime.close()


def test_evidence_service_requires_location_before_document_upload(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        field_repository = SqliteFieldRegistryRepository(runtime.connection)
        evidence_repository = SqliteEvidenceRepository(runtime.connection)
        service = EvidenceSubmissionService(evidence_repository, field_repository)

        request_context = service.create_request(
            provider_user_id="1001",
            request_type_code="field_photo",
        )
        session = service.start_submission_session(
            provider_user_id="1001",
            chat_id=67890,
            request_event_id=request_context.request_event.id,
        )

        with pytest.raises(ValueError):
            service.register_document_upload(
                session.id,
                provider_file_id="file_123",
                provider_file_unique_id="file_unique_123",
            )

        session = service.accept_location(
            session.id,
            latitude=37.55,
            longitude=127.01,
            accuracy_meters=5.0,
        )
        submission = service.register_document_upload(
            session.id,
            provider_file_id="file_123",
            provider_file_unique_id="file_unique_123",
            provider_message_id="msg_123",
            file_name="field.jpg",
            mime_type="image/jpeg",
            file_size_bytes=2048,
        )
        updated_session = evidence_repository.get_submission_session(session.id)
        logs = evidence_repository.list_state_logs(submission.id)

        assert updated_session is not None
        assert updated_session.session_status_code == EVIDENCE_SESSION_STATUS_VALIDATING
        assert submission.payload["accepted_location_latitude"] == 37.55
        assert logs[0].to_state_code == "uploaded"
    finally:
        runtime.close()
