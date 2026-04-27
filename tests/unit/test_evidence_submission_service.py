import pytest
from PIL import Image, TiffImagePlugin

from PROJECT.evidence import (
    EVIDENCE_BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING,
    EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING,
    EVIDENCE_VALIDATION_OUTCOME_ACCEPTED,
    EVIDENCE_VALIDATION_OUTCOME_RETRY_DOCUMENT,
    EvidenceSubmissionService,
)
from PROJECT.fields.binding import FIELD_CODE_BINDING_SOURCE
from PROJECT.settings import SqliteSettings
from PROJECT.storage.evidence import (
    EVIDENCE_ARTIFACT_STATUS_SIGNALS_READY,
    EVIDENCE_REQUEST_STATUS_SATISFIED,
    EVIDENCE_SESSION_STATUS_COMPLETED,
    EVIDENCE_SESSION_STATUS_VALIDATING,
    EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT,
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


def _gps_dms(value: float):
    degrees = int(value)
    minutes_full = (value - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60 * 10000)
    return (
        TiffImagePlugin.IFDRational(degrees, 1),
        TiffImagePlugin.IFDRational(minutes, 1),
        TiffImagePlugin.IFDRational(seconds, 10000),
    )


def _write_exif_jpeg(path, *, latitude: float, longitude: float, captured_at: str) -> None:
    image = Image.new("RGB", (8, 8), color="green")
    exif = Image.Exif()
    exif[36867] = captured_at
    exif[34853] = {
        1: "N" if latitude >= 0 else "S",
        2: _gps_dms(abs(latitude)),
        3: "E" if longitude >= 0 else "W",
        4: _gps_dms(abs(longitude)),
    }
    image.save(path, exif=exif)


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


def test_evidence_service_extracts_signal_rows_from_submission_metadata(tmp_path):
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
        service.accept_location(
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
            uploaded_at="2026-04-27T00:10:00+00:00",
            payload={
                "exif": {
                    "gps_latitude": 37.5505,
                    "gps_longitude": 127.0105,
                    "captured_at": "2026-04-27T00:00:00+00:00",
                }
            },
        )

        assert submission.artifact_status_code == EVIDENCE_ARTIFACT_STATUS_SIGNALS_READY
        signals = {signal.signal_type_code: signal for signal in evidence_repository.list_validation_signals(submission.id)}

        assert signals["exif_present"].signal_status_code == "present"
        assert signals["gps_present"].signal_status_code == "present"
        assert signals["capture_time_present"].signal_status_code == "present"
        assert signals["capture_time"].text_value == "2026-04-27T00:00:00+00:00"
        assert signals["gps_latitude"].numeric_value == 37.5505
        assert signals["gps_longitude"].numeric_value == 127.0105
        assert signals["location_distance_meters"].signal_status_code == "computed"
        assert signals["location_distance_meters"].numeric_value is not None
        assert signals["upload_delay_seconds"].signal_status_code == "computed"
        assert signals["upload_delay_seconds"].numeric_value == 600.0
    finally:
        runtime.close()


def test_evidence_service_extracts_signal_rows_from_staged_artifact(tmp_path):
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
        service.accept_location(
            session.id,
            latitude=37.55,
            longitude=127.01,
            accuracy_meters=5.0,
        )
        artifact_path = tmp_path / "artifact-with-exif.jpg"
        _write_exif_jpeg(
            artifact_path,
            latitude=37.5505,
            longitude=127.0105,
            captured_at="2026:04:27 09:30:00",
        )
        submission = service.register_document_upload(
            session.id,
            provider_file_id="file_123",
            provider_file_unique_id="file_unique_123",
            provider_message_id="msg_123",
            file_name="field.jpg",
            mime_type="image/jpeg",
            file_size_bytes=artifact_path.stat().st_size,
            staged_artifact_uri=artifact_path.resolve().as_uri(),
            uploaded_at="2026-04-27T09:40:00+00:00",
            payload={},
        )

        signals = {signal.signal_type_code: signal for signal in evidence_repository.list_validation_signals(submission.id)}

        assert submission.staged_artifact_uri == artifact_path.resolve().as_uri()
        assert signals["exif_present"].signal_status_code == "present"
        assert signals["exif_present"].detail["source"] == "staged_artifact"
        assert signals["gps_present"].signal_status_code == "present"
        assert round(signals["gps_latitude"].numeric_value, 4) == 37.5505
        assert round(signals["gps_longitude"].numeric_value, 4) == 127.0105
        assert signals["capture_time"].text_value == "2026-04-27T09:30:00+00:00"
        assert signals["upload_delay_seconds"].numeric_value == 600.0
    finally:
        runtime.close()


def test_evidence_service_marks_missing_signal_rows_when_metadata_is_absent(tmp_path):
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
        service.accept_location(
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
            payload={},
        )

        signals = {signal.signal_type_code: signal for signal in evidence_repository.list_validation_signals(submission.id)}

        assert signals["exif_present"].signal_status_code == "missing"
        assert signals["gps_present"].signal_status_code == "missing"
        assert signals["capture_time_present"].signal_status_code == "missing"
        assert signals["capture_time"].signal_status_code == "missing"
        assert signals["gps_latitude"].signal_status_code == "missing"
        assert signals["gps_longitude"].signal_status_code == "missing"
        assert signals["location_distance_meters"].signal_status_code == "not_computed"
        assert signals["upload_delay_seconds"].signal_status_code == "not_computed"
    finally:
        runtime.close()


def test_evidence_service_evaluates_submission_as_accepted_when_required_signals_exist(tmp_path):
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
        service.accept_location(
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
            uploaded_at="2026-04-27T00:10:00+00:00",
            payload={
                "exif": {
                    "gps_latitude": 37.5501,
                    "gps_longitude": 127.0101,
                    "captured_at": "2026-04-27T00:00:00+00:00",
                }
            },
        )

        decision = service.evaluate_submission(submission.id)
        updated_submission = evidence_repository.get_submission(submission.id)
        updated_session = evidence_repository.get_submission_session(session.id)
        updated_request = evidence_repository.get_request_event(request_context.request_event.id)
        logs = evidence_repository.list_state_logs(submission.id)

        assert decision.outcome_code == EVIDENCE_VALIDATION_OUTCOME_ACCEPTED
        assert decision.reason_codes == ()
        assert updated_submission is not None
        assert updated_submission.artifact_status_code == "accepted"
        assert updated_session is not None
        assert updated_session.session_status_code == EVIDENCE_SESSION_STATUS_COMPLETED
        assert updated_request is not None
        assert updated_request.request_status_code == EVIDENCE_REQUEST_STATUS_SATISFIED
        assert logs[-1].to_state_code == "accepted"
    finally:
        runtime.close()


def test_evidence_service_evaluates_submission_as_retry_when_required_signals_are_missing(tmp_path):
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
        service.accept_location(
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
            payload={},
        )

        decision = service.evaluate_submission(submission.id)
        updated_submission = evidence_repository.get_submission(submission.id)
        updated_session = evidence_repository.get_submission_session(session.id)
        logs = evidence_repository.list_state_logs(submission.id)

        assert decision.outcome_code == EVIDENCE_VALIDATION_OUTCOME_RETRY_DOCUMENT
        assert "missing_exif" in decision.reason_codes
        assert "missing_gps" in decision.reason_codes
        assert "missing_capture_time" in decision.reason_codes
        assert updated_submission is not None
        assert updated_submission.artifact_status_code == "rejected"
        assert updated_session is not None
        assert updated_session.session_status_code == EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT
        assert logs[-1].to_state_code == "rejected"
    finally:
        runtime.close()


def test_evidence_service_requests_manual_review_when_location_distance_is_too_far(tmp_path):
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
        service.accept_location(
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
            uploaded_at="2026-04-27T00:10:00+00:00",
            payload={
                "exif": {
                    "gps_latitude": 35.101,
                    "gps_longitude": 129.021,
                    "captured_at": "2026-04-27T00:00:00+00:00",
                }
            },
        )

        decision = service.evaluate_submission(submission.id)
        assessment = service.assess_manual_review_requirement(submission.id, decision)

        assert decision.outcome_code == EVIDENCE_VALIDATION_OUTCOME_RETRY_DOCUMENT
        assert "location_distance_too_far" in decision.reason_codes
        assert assessment.required is True
        assert assessment.trigger_reason_code == "distance_conflict"
        assert assessment.rejected_submission_count == 1
    finally:
        runtime.close()


def test_evidence_service_escalates_retry_limit_to_manual_review(tmp_path):
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
        service.accept_location(
            session.id,
            latitude=37.55,
            longitude=127.01,
            accuracy_meters=5.0,
        )

        latest_submission = None
        latest_decision = None
        for suffix in ("1", "2"):
            latest_submission = service.register_document_upload(
                session.id,
                provider_file_id=f"file_{suffix}",
                provider_file_unique_id=f"file_unique_{suffix}",
                provider_message_id=f"msg_{suffix}",
                file_name=f"field_{suffix}.jpg",
                mime_type="image/jpeg",
                file_size_bytes=2048,
                payload={},
            )
            latest_decision = service.evaluate_submission(latest_submission.id)

        assert latest_submission is not None
        assert latest_decision is not None

        assessment = service.assess_manual_review_requirement(latest_submission.id, latest_decision)
        escalated = service.escalate_submission_manual_review(
            latest_submission.id,
            trigger_reason_code=assessment.trigger_reason_code or "retry_limit",
            detail={"reason_codes": list(latest_decision.reason_codes)},
        )
        updated_session = evidence_repository.get_submission_session(session.id)
        logs = evidence_repository.list_state_logs(latest_submission.id)

        assert assessment.required is True
        assert assessment.trigger_reason_code == "retry_limit"
        assert assessment.rejected_submission_count == 2
        assert escalated.artifact_status_code == "manual_review_required"
        assert updated_session is not None
        assert updated_session.session_status_code == "manual_review_required"
        assert logs[-1].to_state_code == "manual_review_required"
    finally:
        runtime.close()
