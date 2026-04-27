import asyncio
from types import SimpleNamespace

from PROJECT.activity import (
    BINDING_RESOLUTION_MATCHED_FIELD_TEXT,
    BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING,
    BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING,
    SeasonActivityService,
)
from PROJECT.channels.telegram.handlers import messages
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM
from PROJECT.conversations.yield_intake import service as yield_service
from PROJECT.conversations.yield_intake.states import STATE_YIELD_CONFIRM
from PROJECT.dispatch.session_dispatcher import reset_session, set_fertilizer_draft, set_state, set_yield_draft
from PROJECT.fields.binding import FIELD_CODE_BINDING_SOURCE
from PROJECT.settings import SqliteSettings
from PROJECT.storage.activity import SqliteSeasonActivityRepository
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


class FakeMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.replies: list[tuple[str, object | None]] = []

    async def reply_text(self, text: str, reply_markup=None):
        self.replies.append((text, reply_markup))


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


def _seed_field_repository(runtime):
    repository = SqliteFieldRegistryRepository(runtime.connection)
    activity_repository = SqliteSeasonActivityRepository(runtime.connection)
    service = SeasonActivityService(activity_repository, repository)
    return repository, activity_repository, service


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


def test_season_activity_repository_creates_core_rows(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        field_repository, activity_repository, _ = _seed_field_repository(runtime)
        binding = _bind_field(
            field_repository,
            provider_user_id="1001",
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        project_season = activity_repository.ensure_project_season(
            project_id=binding.binding.project_id,
            season_year=2026,
        )
        field_season = activity_repository.ensure_field_season(
            project_season_id=project_season.id,
            participant_id=binding.binding.participant_id,
            field_binding_id=binding.binding.id,
            field_id=binding.field.id,
        )
        event = activity_repository.create_seasonal_event(
            project_id=binding.binding.project_id,
            participant_id=binding.binding.participant_id,
            event_type_code="fertilizer_input_confirmed",
            occurred_on="2026-04-21",
            field_season_id=field_season.id,
            field_binding_id=binding.binding.id,
            field_id=binding.field.id,
            payload={"binding_resolution_code": "single_active_binding"},
        )
        fertilizer_record = activity_repository.create_fertilizer_record(
            project_id=binding.binding.project_id,
            participant_id=binding.binding.participant_id,
            field_season_id=field_season.id,
            seasonal_event_id=event.id,
            field_binding_id=binding.binding.id,
            field_id=binding.field.id,
            used_flag=True,
            fertilizer_kind_code="compound",
            product_name="비료A",
            amount_value=20.0,
            amount_unit="kg",
            applied_date="2026-04-21",
            payload={"binding_resolution_code": "single_active_binding"},
        )
        yield_record = activity_repository.create_yield_record(
            project_id=binding.binding.project_id,
            participant_id=binding.binding.participant_id,
            field_season_id=field_season.id,
            seasonal_event_id=event.id,
            field_binding_id=binding.binding.id,
            field_id=binding.field.id,
            ready_flag=True,
            field_name="논 1",
            amount_value=150.0,
            amount_unit="kg",
            harvest_date="2026-10-01",
            payload={"binding_resolution_code": "single_active_binding"},
        )

        assert fertilizer_record.field_id == binding.field.id
        assert yield_record.field_id == binding.field.id
        assert activity_repository.list_fertilizer_records(participant_id=binding.binding.participant_id)[0].id == fertilizer_record.id
        assert activity_repository.list_yield_records(participant_id=binding.binding.participant_id)[0].id == yield_record.id
    finally:
        runtime.close()


def test_season_activity_service_uses_single_active_binding_for_fertilizer(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        field_repository, activity_repository, service = _seed_field_repository(runtime)
        binding = _bind_field(
            field_repository,
            provider_user_id="1001",
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )

        result = service.record_fertilizer(
            provider_user_id="1001",
            draft=fertilizer_service.FertilizerDraft(
                used=True,
                kind="compound",
                product_name="복합비료A",
                amount_value=20.0,
                amount_unit="kg",
                applied_date="2026-04-21",
            ),
        )

        stored = activity_repository.list_fertilizer_records(participant_id=binding.binding.participant_id)
        assert len(stored) == 1
        assert result.binding_resolution_code == BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING
        assert stored[0].field_id == binding.field.id
        assert stored[0].payload["binding_resolution_code"] == BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING
    finally:
        runtime.close()


def test_season_activity_service_matches_yield_field_name_when_multiple_bindings_exist(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        field_repository, activity_repository, service = _seed_field_repository(runtime)
        _bind_field(
            field_repository,
            provider_user_id="1001",
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        binding_two = _bind_field(
            field_repository,
            provider_user_id="1001",
            field_code="FIELD-002",
            display_name="논 2",
            polygon=[(37.2, 127.2), (37.2, 127.3), (37.3, 127.3), (37.3, 127.2)],
        )

        result = service.record_yield(
            provider_user_id="1001",
            draft=yield_service.YieldDraft(
                ready=True,
                field_name="FIELD-002",
                amount_value=150.0,
                amount_unit="kg",
                harvest_date="2026-10-01",
            ),
        )

        stored = activity_repository.list_yield_records(participant_id=binding_two.binding.participant_id)
        assert len(stored) == 1
        assert result.binding_resolution_code == BINDING_RESOLUTION_MATCHED_FIELD_TEXT
        assert stored[0].field_id == binding_two.field.id
    finally:
        runtime.close()


def test_season_activity_service_preserves_unresolved_state_without_binding(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="1001")
        _, activity_repository, service = _seed_field_repository(runtime)

        result = service.record_fertilizer(
            provider_user_id="1001",
            draft=fertilizer_service.FertilizerDraft(
                used=True,
                kind="compound",
                product_name="복합비료A",
                amount_value=20.0,
                amount_unit="kg",
                applied_date="2026-04-21",
            ),
        )

        stored = activity_repository.list_fertilizer_records()
        assert len(stored) == 1
        assert result.binding_resolution_code == BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING
        assert stored[0].field_id is None
        assert stored[0].payload["binding_resolution_code"] == BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING
    finally:
        runtime.close()


def test_confirm_persistence_helper_writes_canonical_records(tmp_path):
    runtime = _runtime(tmp_path)
    try:
        _approve_participant(runtime, provider_user_id="12345")
        field_repository, activity_repository, service = _seed_field_repository(runtime)
        _bind_field(
            field_repository,
            provider_user_id="12345",
            field_code="FIELD-001",
            display_name="논 1",
            polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
        )
        user_data: dict = {}
        reset_session(user_data)
        set_state(user_data, STATE_FERTILIZER_CONFIRM)
        set_fertilizer_draft(
            user_data,
            fertilizer_service.FertilizerDraft(
                used=True,
                kind="compound",
                product_name="복합비료A",
                amount_value=20.0,
                amount_unit="kg",
                applied_date="2026-04-21",
            ).to_dict(),
        )
        context = SimpleNamespace(
            user_data=user_data,
            bot_data={"season_activity_service": service},
        )
        update = SimpleNamespace(
            effective_user=SimpleNamespace(id=12345),
            effective_chat=SimpleNamespace(id=67890),
            effective_message=FakeMessage(),
        )

        assert asyncio.run(messages.persist_fertilizer_canonical_record(update, context)) is True
        assert len(activity_repository.list_fertilizer_records()) == 1

        set_state(user_data, STATE_YIELD_CONFIRM)
        set_yield_draft(
            user_data,
            yield_service.YieldDraft(
                ready=True,
                field_name="논 1",
                amount_value=150.0,
                amount_unit="kg",
                harvest_date="2026-10-01",
            ).to_dict(),
        )

        assert asyncio.run(messages.persist_yield_canonical_record(update, context)) is True
        assert len(activity_repository.list_yield_records()) == 1
    finally:
        runtime.close()
