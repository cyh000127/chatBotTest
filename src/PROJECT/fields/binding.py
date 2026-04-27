from __future__ import annotations

from dataclasses import dataclass

from PROJECT.fields.lookup import FieldCandidate, FieldLookupService
from PROJECT.storage.fields import (
    FIELD_BINDING_EXCEPTION_FIELD_ALREADY_BOUND,
    FIELD_BINDING_EXCEPTION_FIELD_CODE_NOT_FOUND,
    FIELD_BINDING_EXCEPTION_LOCATION_NO_CANDIDATE,
    FIELD_BINDING_EXCEPTION_LOCATION_MULTIPLE_CANDIDATES,
    FIELD_BINDING_EXCEPTION_PARTICIPANT_DUPLICATE,
    FIELD_BINDING_SOURCE_FIELD_CODE,
    FIELD_BINDING_SOURCE_LOCATION,
    FieldBindingConflictError,
    FieldBindingException,
    ParticipantContext,
    ParticipantFieldBindingRecord,
    SqliteFieldRegistryRepository,
)


@dataclass(frozen=True)
class FieldBindingLookupResult:
    participant: ParticipantContext | None
    version_id: str | None
    candidates: tuple[FieldCandidate, ...]
    exception: FieldBindingException | None = None


@dataclass(frozen=True)
class FieldCodeLookupResult:
    participant: ParticipantContext | None
    field: ParticipantFieldBindingRecord | None = None
    candidate: FieldCandidate | None = None
    exception: FieldBindingException | None = None


class FieldBindingService:
    def __init__(self, repository: SqliteFieldRegistryRepository) -> None:
        self._repository = repository
        self._lookup = FieldLookupService(repository)

    def participant_context(self, *, provider_user_id: str) -> ParticipantContext | None:
        return self._repository.find_active_participant_context(provider_user_id=provider_user_id)

    def list_myfields(self, *, provider_user_id: str) -> tuple[ParticipantContext | None, tuple[ParticipantFieldBindingRecord, ...]]:
        participant = self.participant_context(provider_user_id=provider_user_id)
        if participant is None:
            return None, ()
        return participant, self._repository.list_active_bindings_for_participant(
            participant_id=participant.participant_id,
            project_id=participant.project_id,
        )

    def lookup_location(
        self,
        *,
        provider_user_id: str,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None,
        onboarding_session_id: str | None,
        chat_id: int | None,
    ) -> FieldBindingLookupResult:
        participant = self.participant_context(provider_user_id=provider_user_id)
        if participant is None:
            return FieldBindingLookupResult(participant=None, version_id=None, candidates=())
        lookup_result = self._lookup.find_location_candidates(
            latitude=latitude,
            longitude=longitude,
            project_id=participant.project_id,
        )
        if lookup_result.version_id is None:
            return FieldBindingLookupResult(participant=participant, version_id=None, candidates=())
        if not lookup_result.candidates:
            exception = self._repository.create_binding_exception(
                project_id=participant.project_id,
                participant_id=participant.participant_id,
                onboarding_session_id=onboarding_session_id,
                provider_user_id=provider_user_id,
                chat_id=chat_id,
                field_registry_version_id=lookup_result.version_id,
                exception_type_code=FIELD_BINDING_EXCEPTION_LOCATION_NO_CANDIDATE,
                location_latitude=latitude,
                location_longitude=longitude,
                location_accuracy_meters=accuracy_meters,
            )
            return FieldBindingLookupResult(
                participant=participant,
                version_id=lookup_result.version_id,
                candidates=(),
                exception=exception,
            )
        if len(lookup_result.candidates) > 1:
            exception = self._repository.create_binding_exception(
                project_id=participant.project_id,
                participant_id=participant.participant_id,
                onboarding_session_id=onboarding_session_id,
                provider_user_id=provider_user_id,
                chat_id=chat_id,
                field_registry_version_id=lookup_result.version_id,
                exception_type_code=FIELD_BINDING_EXCEPTION_LOCATION_MULTIPLE_CANDIDATES,
                location_latitude=latitude,
                location_longitude=longitude,
                location_accuracy_meters=accuracy_meters,
                candidate_field_ids=[candidate.field_id for candidate in lookup_result.candidates],
            )
            return FieldBindingLookupResult(
                participant=participant,
                version_id=lookup_result.version_id,
                candidates=lookup_result.candidates,
                exception=exception,
            )
        return FieldBindingLookupResult(
            participant=participant,
            version_id=lookup_result.version_id,
            candidates=lookup_result.candidates,
        )

    def lookup_field_code(
        self,
        *,
        provider_user_id: str,
        field_code: str,
        onboarding_session_id: str | None,
        chat_id: int | None,
    ) -> FieldBindingLookupResult:
        participant = self.participant_context(provider_user_id=provider_user_id)
        if participant is None:
            return FieldBindingLookupResult(participant=None, version_id=None, candidates=())
        field = self._lookup.find_field_by_code(
            field_code=field_code,
            project_id=participant.project_id,
        )
        version_id = field.field.field_registry_version_id if field is not None else None
        if version_id is None and self._repository.latest_published_version(project_id=participant.project_id) is None:
            return FieldBindingLookupResult(participant=participant, version_id=None, candidates=())
        if field is None:
            exception = self._repository.create_binding_exception(
                project_id=participant.project_id,
                participant_id=participant.participant_id,
                onboarding_session_id=onboarding_session_id,
                provider_user_id=provider_user_id,
                chat_id=chat_id,
                field_registry_version_id=version_id,
                exception_type_code=FIELD_BINDING_EXCEPTION_FIELD_CODE_NOT_FOUND,
                requested_field_code=field_code,
            )
            return FieldBindingLookupResult(
                participant=participant,
                version_id=version_id,
                candidates=(),
                exception=exception,
            )
        candidate = FieldCandidate(
            field_id=field.field.id,
            field_code=field.field.field_code,
            display_name=field.field.display_name,
            field_registry_version_id=field.field.field_registry_version_id,
            centroid_distance_meters=0.0,
        )
        return FieldBindingLookupResult(
            participant=participant,
            version_id=field.field.field_registry_version_id,
            candidates=(candidate,),
        )

    def confirm_binding(
        self,
        *,
        provider_user_id: str,
        field_id: str,
        field_registry_version_id: str,
        binding_source_code: str,
        onboarding_session_id: str | None,
        chat_id: int | None,
        location_latitude: float | None = None,
        location_longitude: float | None = None,
        location_accuracy_meters: float | None = None,
        requested_field_code: str | None = None,
    ) -> tuple[ParticipantFieldBindingRecord | None, FieldBindingException | None]:
        participant = self.participant_context(provider_user_id=provider_user_id)
        if participant is None:
            return None, None
        try:
            binding = self._repository.create_binding(
                participant_id=participant.participant_id,
                project_id=participant.project_id,
                field_id=field_id,
                field_registry_version_id=field_registry_version_id,
                binding_source_code=binding_source_code,
                onboarding_session_id=onboarding_session_id,
                provider_user_id=provider_user_id,
                chat_id=chat_id,
                location_latitude=location_latitude,
                location_longitude=location_longitude,
                location_accuracy_meters=location_accuracy_meters,
                requested_field_code=requested_field_code,
            )
            return binding, None
        except FieldBindingConflictError as exc:
            exception = self._repository.create_binding_exception(
                project_id=participant.project_id,
                participant_id=participant.participant_id,
                onboarding_session_id=onboarding_session_id,
                provider_user_id=provider_user_id,
                chat_id=chat_id,
                field_registry_version_id=field_registry_version_id,
                exception_type_code=exc.code,
                requested_field_code=requested_field_code,
                location_latitude=location_latitude,
                location_longitude=location_longitude,
                location_accuracy_meters=location_accuracy_meters,
                candidate_field_ids=[field_id],
            )
            return None, exception


LOCATION_BINDING_SOURCE = FIELD_BINDING_SOURCE_LOCATION
FIELD_CODE_BINDING_SOURCE = FIELD_BINDING_SOURCE_FIELD_CODE
FIELD_BINDING_CONFLICT_CODES = {
    FIELD_BINDING_EXCEPTION_FIELD_ALREADY_BOUND,
    FIELD_BINDING_EXCEPTION_PARTICIPANT_DUPLICATE,
}
