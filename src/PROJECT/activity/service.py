from __future__ import annotations

import re
from dataclasses import dataclass

from PROJECT.conversations.fertilizer_intake.service import FertilizerDraft
from PROJECT.conversations.yield_intake.service import YieldDraft
from PROJECT.storage.activity import (
    ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
    SEASONAL_EVENT_TYPE_FERTILIZER_INPUT,
    SEASONAL_EVENT_TYPE_YIELD_INPUT,
    SqliteSeasonActivityRepository,
)
from PROJECT.storage.fields import ParticipantContext, ParticipantFieldBindingRecord, SqliteFieldRegistryRepository

BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING = "single_active_binding"
BINDING_RESOLUTION_MATCHED_FIELD_TEXT = "matched_field_text"
BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING = "unresolved_no_active_binding"
BINDING_RESOLUTION_UNRESOLVED_MULTIPLE_ACTIVE_BINDINGS = "unresolved_multiple_active_bindings"


@dataclass(frozen=True)
class SeasonActivityWriteResult:
    project_season_id: str
    field_season_id: str | None
    seasonal_event_id: str
    record_id: str
    binding_resolution_code: str
    field_binding_id: str | None
    field_id: str | None


class SeasonActivityService:
    def __init__(
        self,
        activity_repository: SqliteSeasonActivityRepository,
        field_repository: SqliteFieldRegistryRepository,
    ) -> None:
        self._activity_repository = activity_repository
        self._field_repository = field_repository

    def record_fertilizer(
        self,
        *,
        provider_user_id: str,
        draft: FertilizerDraft,
    ) -> SeasonActivityWriteResult:
        if draft.used is None or not draft.applied_date:
            raise ValueError("확정되지 않은 비료 입력은 canonical write를 만들 수 없습니다.")
        participant = self._require_participant(provider_user_id=provider_user_id)
        binding, resolution_code = self._resolve_fertilizer_binding(participant=participant)
        return self._write_fertilizer(
            participant=participant,
            binding=binding,
            resolution_code=resolution_code,
            draft=draft,
        )

    def record_yield(
        self,
        *,
        provider_user_id: str,
        draft: YieldDraft,
    ) -> SeasonActivityWriteResult:
        if draft.ready is None or not draft.harvest_date:
            raise ValueError("확정되지 않은 수확량 입력은 canonical write를 만들 수 없습니다.")
        participant = self._require_participant(provider_user_id=provider_user_id)
        binding, resolution_code = self._resolve_yield_binding(
            participant=participant,
            field_name=draft.field_name,
        )
        return self._write_yield(
            participant=participant,
            binding=binding,
            resolution_code=resolution_code,
            draft=draft,
        )

    def _write_fertilizer(
        self,
        *,
        participant: ParticipantContext,
        binding: ParticipantFieldBindingRecord | None,
        resolution_code: str,
        draft: FertilizerDraft,
    ) -> SeasonActivityWriteResult:
        project_season = self._activity_repository.ensure_project_season(
            project_id=participant.project_id,
            season_year=_season_year_from_date(draft.applied_date),
        )
        field_season = self._ensure_field_season(
            participant=participant,
            project_season_id=project_season.id,
            binding=binding,
        )
        payload = {
            "binding_resolution_code": resolution_code,
            "product_name": draft.product_name,
        }
        event = self._activity_repository.create_seasonal_event(
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            event_type_code=SEASONAL_EVENT_TYPE_FERTILIZER_INPUT,
            occurred_on=draft.applied_date,
            input_source_code=ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
            field_season_id=field_season.id if field_season is not None else None,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
            payload=payload,
        )
        record = self._activity_repository.create_fertilizer_record(
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            field_season_id=field_season.id if field_season is not None else None,
            seasonal_event_id=event.id,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
            input_source_code=ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
            used_flag=draft.used,
            fertilizer_kind_code=draft.kind or None,
            product_name=draft.product_name or None,
            amount_value=draft.amount_value,
            amount_unit=draft.amount_unit or None,
            applied_date=draft.applied_date,
            payload=payload,
        )
        return SeasonActivityWriteResult(
            project_season_id=project_season.id,
            field_season_id=field_season.id if field_season is not None else None,
            seasonal_event_id=event.id,
            record_id=record.id,
            binding_resolution_code=resolution_code,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
        )

    def _write_yield(
        self,
        *,
        participant: ParticipantContext,
        binding: ParticipantFieldBindingRecord | None,
        resolution_code: str,
        draft: YieldDraft,
    ) -> SeasonActivityWriteResult:
        project_season = self._activity_repository.ensure_project_season(
            project_id=participant.project_id,
            season_year=_season_year_from_date(draft.harvest_date),
        )
        field_season = self._ensure_field_season(
            participant=participant,
            project_season_id=project_season.id,
            binding=binding,
        )
        payload = {
            "binding_resolution_code": resolution_code,
            "field_name_input": draft.field_name,
        }
        event = self._activity_repository.create_seasonal_event(
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            event_type_code=SEASONAL_EVENT_TYPE_YIELD_INPUT,
            occurred_on=draft.harvest_date,
            input_source_code=ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
            field_season_id=field_season.id if field_season is not None else None,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
            payload=payload,
        )
        record = self._activity_repository.create_yield_record(
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            field_season_id=field_season.id if field_season is not None else None,
            seasonal_event_id=event.id,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
            input_source_code=ACTIVITY_INPUT_SOURCE_CHAT_CONFIRM,
            ready_flag=draft.ready,
            field_name=draft.field_name or None,
            amount_value=draft.amount_value,
            amount_unit=draft.amount_unit or None,
            harvest_date=draft.harvest_date,
            payload=payload,
        )
        return SeasonActivityWriteResult(
            project_season_id=project_season.id,
            field_season_id=field_season.id if field_season is not None else None,
            seasonal_event_id=event.id,
            record_id=record.id,
            binding_resolution_code=resolution_code,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
        )

    def _require_participant(self, *, provider_user_id: str) -> ParticipantContext:
        participant = self._field_repository.find_active_participant_context(provider_user_id=provider_user_id)
        if participant is None:
            raise ValueError("활성 participant context를 찾을 수 없습니다.")
        return participant

    def _resolve_fertilizer_binding(
        self,
        *,
        participant: ParticipantContext,
    ) -> tuple[ParticipantFieldBindingRecord | None, str]:
        active_bindings = self._field_repository.list_active_bindings_for_participant(
            participant_id=participant.participant_id,
            project_id=participant.project_id,
        )
        if len(active_bindings) == 1:
            return active_bindings[0], BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING
        if not active_bindings:
            return None, BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING
        return None, BINDING_RESOLUTION_UNRESOLVED_MULTIPLE_ACTIVE_BINDINGS

    def _resolve_yield_binding(
        self,
        *,
        participant: ParticipantContext,
        field_name: str,
    ) -> tuple[ParticipantFieldBindingRecord | None, str]:
        active_bindings = self._field_repository.list_active_bindings_for_participant(
            participant_id=participant.participant_id,
            project_id=participant.project_id,
        )
        if len(active_bindings) == 1:
            return active_bindings[0], BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING
        if not active_bindings:
            return None, BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING
        matched = _match_binding_by_field_name(field_name, active_bindings)
        if matched is not None:
            return matched, BINDING_RESOLUTION_MATCHED_FIELD_TEXT
        return None, BINDING_RESOLUTION_UNRESOLVED_MULTIPLE_ACTIVE_BINDINGS

    def _ensure_field_season(
        self,
        *,
        participant: ParticipantContext,
        project_season_id: str,
        binding: ParticipantFieldBindingRecord | None,
    ):
        if binding is None:
            return None
        return self._activity_repository.ensure_field_season(
            project_season_id=project_season_id,
            participant_id=participant.participant_id,
            field_binding_id=binding.binding.id,
            field_id=binding.field.id,
        )


def _season_year_from_date(value: str) -> int:
    return int(value[:4])


def _match_binding_by_field_name(
    field_name: str,
    active_bindings: tuple[ParticipantFieldBindingRecord, ...],
) -> ParticipantFieldBindingRecord | None:
    normalized = _normalize(field_name)
    if not normalized:
        return None
    matches = [
        binding
        for binding in active_bindings
        if normalized in {
            _normalize(binding.field.display_name),
            _normalize(binding.field.field_code),
        }
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())
