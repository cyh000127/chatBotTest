from PROJECT.fields.binding import FieldBindingService, FIELD_CODE_BINDING_SOURCE, LOCATION_BINDING_SOURCE
from PROJECT.settings import SqliteSettings
from PROJECT.storage.fields import (
    FIELD_BINDING_EXCEPTION_FIELD_ALREADY_BOUND,
    FIELD_BINDING_EXCEPTION_FIELD_CODE_NOT_FOUND,
    FIELD_BINDING_EXCEPTION_LOCATION_MULTIPLE_CANDIDATES,
    FIELD_BINDING_EXCEPTION_LOCATION_NO_CANDIDATE,
    SqliteFieldRegistryRepository,
)
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def _approved_participant(runtime, *, provider_user_id: str, name: str):
    invitation_repository = SqliteInvitationRepository(runtime.connection)
    onboarding_repository = SqliteOnboardingRepository(runtime.connection)
    invitation = invitation_repository.create_invitation()
    session = onboarding_repository.create_or_resume_from_invitation(
        invitation=invitation,
        provider_user_id=provider_user_id,
        provider_handle=f"user_{provider_user_id}",
        preferred_locale_code="ko",
        chat_id=67890,
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


def _service(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    repository = SqliteFieldRegistryRepository(runtime.connection)
    service = FieldBindingService(repository)
    return runtime, repository, service


def test_field_binding_service_creates_exception_when_location_has_no_candidate(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        _approved_participant(runtime, provider_user_id="1001", name="홍길동")
        version = repository.create_registry_version(version_label="v1")
        repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        repository.publish_version(version.id)

        result = service.lookup_location(
            provider_user_id="1001",
            latitude=35.0,
            longitude=128.0,
            accuracy_meters=10.0,
            onboarding_session_id=None,
            chat_id=67890,
        )

        assert result.participant is not None
        assert result.candidates == ()
        assert result.exception is not None
        assert result.exception.exception_type_code == FIELD_BINDING_EXCEPTION_LOCATION_NO_CANDIDATE
    finally:
        runtime.close()


def test_field_binding_service_creates_exception_when_location_has_multiple_candidates(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        _approved_participant(runtime, provider_user_id="1001", name="홍길동")
        version = repository.create_registry_version(version_label="v1")
        repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-002",
            display_name="논 2",
            polygon=[(36.95, 126.95), (36.95, 127.15), (37.15, 127.15), (37.15, 126.95)],
        )
        repository.publish_version(version.id)

        result = service.lookup_location(
            provider_user_id="1001",
            latitude=37.05,
            longitude=127.05,
            accuracy_meters=10.0,
            onboarding_session_id=None,
            chat_id=67890,
        )

        assert len(result.candidates) == 2
        assert result.exception is not None
        assert result.exception.exception_type_code == FIELD_BINDING_EXCEPTION_LOCATION_MULTIPLE_CANDIDATES
    finally:
        runtime.close()


def test_field_binding_service_can_bind_by_confirmed_location_candidate(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        _approved_participant(runtime, provider_user_id="1001", name="홍길동")
        version = repository.create_registry_version(version_label="v1")
        record = repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        repository.publish_version(version.id)

        binding, exception = service.confirm_binding(
            provider_user_id="1001",
            field_id=record.field.id,
            field_registry_version_id=version.id,
            binding_source_code=LOCATION_BINDING_SOURCE,
            onboarding_session_id=None,
            chat_id=67890,
            location_latitude=37.05,
            location_longitude=127.05,
            location_accuracy_meters=8.0,
        )

        assert exception is None
        assert binding is not None
        assert binding.field.field_code == "FIELD-001"
        participant, bindings = service.list_myfields(provider_user_id="1001")
        assert participant is not None
        assert [item.field.field_code for item in bindings] == ["FIELD-001"]
    finally:
        runtime.close()


def test_field_binding_service_records_conflict_when_field_is_already_bound(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        _approved_participant(runtime, provider_user_id="1001", name="홍길동")
        _approved_participant(runtime, provider_user_id="1002", name="김영희")
        version = repository.create_registry_version(version_label="v1")
        record = repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        repository.publish_version(version.id)

        first_binding, first_exception = service.confirm_binding(
            provider_user_id="1001",
            field_id=record.field.id,
            field_registry_version_id=version.id,
            binding_source_code=FIELD_CODE_BINDING_SOURCE,
            onboarding_session_id=None,
            chat_id=67890,
            requested_field_code="FIELD-001",
        )
        second_binding, second_exception = service.confirm_binding(
            provider_user_id="1002",
            field_id=record.field.id,
            field_registry_version_id=version.id,
            binding_source_code=FIELD_CODE_BINDING_SOURCE,
            onboarding_session_id=None,
            chat_id=67891,
            requested_field_code="FIELD-001",
        )

        assert first_binding is not None
        assert first_exception is None
        assert second_binding is None
        assert second_exception is not None
        assert second_exception.exception_type_code == FIELD_BINDING_EXCEPTION_FIELD_ALREADY_BOUND
    finally:
        runtime.close()


def test_field_binding_service_creates_exception_when_field_code_is_missing(tmp_path):
    runtime, repository, service = _service(tmp_path)

    try:
        _approved_participant(runtime, provider_user_id="1001", name="홍길동")
        version = repository.create_registry_version(version_label="v1")
        repository.import_field(
            field_registry_version_id=version.id,
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        repository.publish_version(version.id)

        result = service.lookup_field_code(
            provider_user_id="1001",
            field_code="FIELD-404",
            onboarding_session_id=None,
            chat_id=67890,
        )

        assert result.exception is not None
        assert result.exception.exception_type_code == FIELD_BINDING_EXCEPTION_FIELD_CODE_NOT_FOUND
    finally:
        runtime.close()
