from __future__ import annotations

from dataclasses import dataclass

from PROJECT.storage.evidence import (
    EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT,
    EVIDENCE_SESSION_STATUS_WAITING_LOCATION,
    EvidenceRequestEvent,
    EvidenceSubmission,
    EvidenceSubmissionSession,
    SqliteEvidenceRepository,
)
from PROJECT.storage.fields import ParticipantContext, ParticipantFieldBindingRecord, SqliteFieldRegistryRepository

EVIDENCE_BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING = "single_active_binding"
EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING = "unresolved_no_active_binding"
EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_MULTIPLE_ACTIVE_BINDINGS = "unresolved_multiple_active_bindings"


@dataclass(frozen=True)
class EvidenceRequestContext:
    request_event: EvidenceRequestEvent
    binding_resolution_code: str
    field_binding_id: str | None
    field_id: str | None


class EvidenceSubmissionService:
    def __init__(
        self,
        evidence_repository: SqliteEvidenceRepository,
        field_repository: SqliteFieldRegistryRepository,
    ) -> None:
        self._evidence_repository = evidence_repository
        self._field_repository = field_repository

    def create_request(
        self,
        *,
        provider_user_id: str,
        request_type_code: str,
        request_reason_code: str | None = None,
        requested_via_code: str = "runtime",
        due_at: str | None = None,
        seasonal_event_id: str | None = None,
        payload: dict | None = None,
    ) -> EvidenceRequestContext:
        participant = self._require_participant(provider_user_id=provider_user_id)
        binding, resolution_code = self._resolve_binding(participant=participant)
        request_payload = dict(payload or {})
        request_payload["binding_resolution_code"] = resolution_code
        event = self._evidence_repository.create_request_event(
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            request_type_code=request_type_code,
            request_reason_code=request_reason_code,
            requested_via_code=requested_via_code,
            due_at=due_at,
            seasonal_event_id=seasonal_event_id,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
            payload=request_payload,
        )
        return EvidenceRequestContext(
            request_event=event,
            binding_resolution_code=resolution_code,
            field_binding_id=binding.binding.id if binding is not None else None,
            field_id=binding.field.id if binding is not None else None,
        )

    def start_submission_session(
        self,
        *,
        provider_user_id: str,
        chat_id: int,
        request_event_id: str,
        draft_payload: dict | None = None,
    ) -> EvidenceSubmissionSession:
        participant = self._require_participant(provider_user_id=provider_user_id)
        request_event = self._evidence_repository.get_request_event(request_event_id)
        if request_event is None:
            raise ValueError("증빙 요청을 찾을 수 없습니다.")
        if request_event.participant_id != participant.participant_id:
            raise ValueError("다른 참여자의 증빙 요청에는 접근할 수 없습니다.")
        return self._evidence_repository.create_submission_session(
            evidence_request_event_id=request_event.id,
            project_id=participant.project_id,
            participant_id=participant.participant_id,
            provider_user_id=provider_user_id,
            chat_id=chat_id,
            field_season_id=request_event.field_season_id,
            field_binding_id=request_event.field_binding_id,
            field_id=request_event.field_id,
            draft_payload=draft_payload,
        )

    def accept_location(
        self,
        session_id: str,
        *,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None,
    ) -> EvidenceSubmissionSession:
        session = self._require_session(session_id)
        if session.session_status_code != EVIDENCE_SESSION_STATUS_WAITING_LOCATION:
            raise ValueError("위치를 받을 수 없는 증빙 세션 상태입니다.")
        return self._evidence_repository.accept_location(
            session_id,
            latitude=latitude,
            longitude=longitude,
            accuracy_meters=accuracy_meters,
        )

    def register_document_upload(
        self,
        session_id: str,
        *,
        provider_file_id: str,
        provider_file_unique_id: str | None = None,
        provider_message_id: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
        staged_artifact_uri: str | None = None,
        checksum_sha256: str | None = None,
        captured_at: str | None = None,
        payload: dict | None = None,
    ) -> EvidenceSubmission:
        session = self._require_session(session_id)
        if session.session_status_code != EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT:
            raise ValueError("위치 확인 전에는 증빙 파일을 등록할 수 없습니다.")
        if session.accepted_location_latitude is None or session.accepted_location_longitude is None:
            raise ValueError("위치 확인 전에는 증빙 파일을 등록할 수 없습니다.")
        request_event = self._evidence_repository.get_request_event(session.evidence_request_event_id)
        if request_event is None:
            raise ValueError("증빙 요청을 찾을 수 없습니다.")
        submission_payload = dict(payload or {})
        submission_payload["accepted_location_latitude"] = session.accepted_location_latitude
        submission_payload["accepted_location_longitude"] = session.accepted_location_longitude
        submission_payload["accepted_location_accuracy_meters"] = session.accepted_location_accuracy_meters
        submission = self._evidence_repository.create_submission(
            evidence_submission_session_id=session.id,
            evidence_request_event_id=request_event.id,
            project_id=session.project_id,
            participant_id=session.participant_id,
            field_season_id=session.field_season_id,
            field_binding_id=session.field_binding_id,
            field_id=session.field_id,
            provider_message_id=provider_message_id,
            provider_file_id=provider_file_id,
            provider_file_unique_id=provider_file_unique_id,
            file_name=file_name,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            staged_artifact_uri=staged_artifact_uri,
            checksum_sha256=checksum_sha256,
            captured_at=captured_at,
            payload=submission_payload,
        )
        self._evidence_repository.append_state_log(
            evidence_submission_id=submission.id,
            to_state_code="uploaded",
            reason_code="document_received",
            detail={"session_id": session.id},
        )
        self._evidence_repository.mark_session_validating(session.id)
        updated_submission = self._evidence_repository.get_submission(submission.id)
        if updated_submission is None:
            raise RuntimeError("등록한 evidence submission을 다시 읽을 수 없습니다.")
        return updated_submission

    def _require_participant(self, *, provider_user_id: str) -> ParticipantContext:
        participant = self._field_repository.find_active_participant_context(provider_user_id=provider_user_id)
        if participant is None:
            raise ValueError("활성 participant context를 찾을 수 없습니다.")
        return participant

    def _resolve_binding(
        self,
        *,
        participant: ParticipantContext,
    ) -> tuple[ParticipantFieldBindingRecord | None, str]:
        active_bindings = self._field_repository.list_active_bindings_for_participant(
            participant_id=participant.participant_id,
            project_id=participant.project_id,
        )
        if len(active_bindings) == 1:
            return active_bindings[0], EVIDENCE_BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING
        if not active_bindings:
            return None, EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING
        return None, EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_MULTIPLE_ACTIVE_BINDINGS

    def _require_session(self, session_id: str) -> EvidenceSubmissionSession:
        session = self._evidence_repository.get_submission_session(session_id)
        if session is None:
            raise ValueError("증빙 제출 세션을 찾을 수 없습니다.")
        return session
