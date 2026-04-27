from __future__ import annotations

from dataclasses import dataclass

from PROJECT.evidence.signals import EvidenceSignalExtractionResult, extract_signal_candidates
from PROJECT.storage.evidence import (
    EVIDENCE_ARTIFACT_STATUS_ACCEPTED,
    EVIDENCE_ARTIFACT_STATUS_MANUAL_REVIEW_REQUIRED,
    EVIDENCE_ARTIFACT_STATUS_REJECTED,
    EVIDENCE_ARTIFACT_STATUS_SIGNALS_READY,
    EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT,
    EVIDENCE_SESSION_STATUS_WAITING_LOCATION,
    EvidenceRequestEvent,
    EvidenceSubmission,
    EvidenceSubmissionSession,
    SqliteEvidenceRepository,
)
from PROJECT.storage.fields import ParticipantContext, ParticipantFieldBindingRecord, SqliteFieldRegistryRepository
from PROJECT.storage.invitations import utc_now_text

EVIDENCE_BINDING_RESOLUTION_SINGLE_ACTIVE_BINDING = "single_active_binding"
EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_NO_ACTIVE_BINDING = "unresolved_no_active_binding"
EVIDENCE_BINDING_RESOLUTION_UNRESOLVED_MULTIPLE_ACTIVE_BINDINGS = "unresolved_multiple_active_bindings"
EVIDENCE_VALIDATION_OUTCOME_ACCEPTED = "accepted"
EVIDENCE_VALIDATION_OUTCOME_RETRY_DOCUMENT = "retry_document"
EVIDENCE_REASON_MISSING_EXIF = "missing_exif"
EVIDENCE_REASON_MISSING_GPS = "missing_gps"
EVIDENCE_REASON_MISSING_CAPTURE_TIME = "missing_capture_time"
EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR = "location_distance_too_far"
EVIDENCE_REASON_UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
EVIDENCE_REASON_ARTIFACT_READ_FAILED = "artifact_read_failed"
EVIDENCE_MANUAL_REVIEW_REASON_DISTANCE_CONFLICT = "distance_conflict"
EVIDENCE_MANUAL_REVIEW_REASON_RETRY_LIMIT = "retry_limit"
MAX_EVIDENCE_LOCATION_DISTANCE_METERS = 500.0
MAX_EVIDENCE_RETRY_BEFORE_MANUAL_REVIEW = 2
SUPPORTED_EVIDENCE_MIME_TYPES = {"image/jpeg", "image/jpg"}
SUPPORTED_EVIDENCE_FILE_SUFFIXES = {".jpg", ".jpeg"}


@dataclass(frozen=True)
class EvidenceRequestContext:
    request_event: EvidenceRequestEvent
    binding_resolution_code: str
    field_binding_id: str | None
    field_id: str | None


@dataclass(frozen=True)
class EvidenceValidationDecision:
    outcome_code: str
    reason_codes: tuple[str, ...]
    missing_signal_codes: tuple[str, ...]
    location_distance_meters: float | None
    upload_delay_seconds: float | None
    artifact_status_code: str


@dataclass(frozen=True)
class EvidenceManualReviewAssessment:
    required: bool
    trigger_reason_code: str | None
    rejected_submission_count: int


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
        uploaded_at: str | None = None,
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
            uploaded_at=uploaded_at,
            payload=submission_payload,
        )
        self._evidence_repository.append_state_log(
            evidence_submission_id=submission.id,
            to_state_code="uploaded",
            reason_code="document_received",
            detail={"session_id": session.id},
        )
        self.extract_submission_signals(submission.id)
        self._evidence_repository.mark_session_validating(session.id)
        updated_submission = self._evidence_repository.get_submission(submission.id)
        if updated_submission is None:
            raise RuntimeError("등록한 evidence submission을 다시 읽을 수 없습니다.")
        return updated_submission

    def extract_submission_signals(self, submission_id: str) -> EvidenceSignalExtractionResult:
        submission = self._require_submission(submission_id)
        session = self._require_session(submission.evidence_submission_session_id)
        result = extract_signal_candidates(submission, session)
        for signal in result.signals:
            self._evidence_repository.create_validation_signal(
                evidence_submission_id=submission.id,
                signal_type_code=signal.signal_type_code,
                signal_status_code=signal.signal_status_code,
                numeric_value=signal.numeric_value,
                text_value=signal.text_value,
                detail=signal.detail,
            )
        self._evidence_repository.update_submission_artifact_status(
            submission.id,
            artifact_status_code=EVIDENCE_ARTIFACT_STATUS_SIGNALS_READY,
        )
        self._evidence_repository.append_state_log(
            evidence_submission_id=submission.id,
            from_state_code="uploaded",
            to_state_code="signals_ready",
            reason_code="signal_extraction_completed",
            detail={"signal_count": len(result.signals)},
        )
        return result

    def evaluate_submission(self, submission_id: str) -> EvidenceValidationDecision:
        submission = self._require_submission(submission_id)
        session = self._require_session(submission.evidence_submission_session_id)
        request_event = self._evidence_repository.get_request_event(submission.evidence_request_event_id)
        if request_event is None:
            raise ValueError("증빙 요청을 찾을 수 없습니다.")

        signals_by_type = {
            signal.signal_type_code: signal
            for signal in self._evidence_repository.list_validation_signals(submission.id)
        }

        missing_signal_codes: list[str] = []
        reason_codes: list[str] = []
        parser_status = self._artifact_parser_status(signals_by_type)

        if self._has_staged_artifact(submission) and not self._is_supported_artifact_file(submission):
            reason_codes.append(EVIDENCE_REASON_UNSUPPORTED_FILE_TYPE)
        elif self._has_staged_artifact(submission) and parser_status in {"missing_file", "read_failed", "unsupported_uri"}:
            reason_codes.append(EVIDENCE_REASON_ARTIFACT_READ_FAILED)
        else:
            if self._signal_status(signals_by_type, "exif_present") != "present":
                missing_signal_codes.append("exif_present")
                reason_codes.append(EVIDENCE_REASON_MISSING_EXIF)
            if self._signal_status(signals_by_type, "gps_present") != "present":
                missing_signal_codes.append("gps_present")
                reason_codes.append(EVIDENCE_REASON_MISSING_GPS)
            if self._signal_status(signals_by_type, "capture_time_present") != "present":
                missing_signal_codes.append("capture_time_present")
                reason_codes.append(EVIDENCE_REASON_MISSING_CAPTURE_TIME)

        distance_signal = signals_by_type.get("location_distance_meters")
        distance_meters = distance_signal.numeric_value if distance_signal is not None else None
        if (
            distance_signal is not None
            and distance_signal.signal_status_code == "computed"
            and distance_meters is not None
            and distance_meters > MAX_EVIDENCE_LOCATION_DISTANCE_METERS
        ):
            reason_codes.append(EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR)

        upload_delay_signal = signals_by_type.get("upload_delay_seconds")
        upload_delay_seconds = upload_delay_signal.numeric_value if upload_delay_signal is not None else None

        if reason_codes:
            self._evidence_repository.update_submission_artifact_status(
                submission.id,
                artifact_status_code=EVIDENCE_ARTIFACT_STATUS_REJECTED,
            )
            self._evidence_repository.append_state_log(
                evidence_submission_id=submission.id,
                from_state_code="signals_ready",
                to_state_code="rejected",
                reason_code="validation_retry_required",
                detail={
                    "reason_codes": reason_codes,
                    "missing_signal_codes": missing_signal_codes,
                    "location_distance_meters": distance_meters,
                },
            )
            self._evidence_repository.mark_session_waiting_document(session.id)
            artifact_status_code = EVIDENCE_ARTIFACT_STATUS_REJECTED
            outcome_code = EVIDENCE_VALIDATION_OUTCOME_RETRY_DOCUMENT
        else:
            self._evidence_repository.update_submission_artifact_status(
                submission.id,
                artifact_status_code=EVIDENCE_ARTIFACT_STATUS_ACCEPTED,
                submitted_at=utc_now_text(),
            )
            self._evidence_repository.append_state_log(
                evidence_submission_id=submission.id,
                from_state_code="signals_ready",
                to_state_code="accepted",
                reason_code="validation_passed",
                detail={
                    "location_distance_meters": distance_meters,
                    "upload_delay_seconds": upload_delay_seconds,
                },
            )
            self._evidence_repository.mark_session_completed(session.id)
            self._evidence_repository.mark_request_satisfied(request_event.id)
            artifact_status_code = EVIDENCE_ARTIFACT_STATUS_ACCEPTED
            outcome_code = EVIDENCE_VALIDATION_OUTCOME_ACCEPTED

        return EvidenceValidationDecision(
            outcome_code=outcome_code,
            reason_codes=tuple(reason_codes),
            missing_signal_codes=tuple(missing_signal_codes),
            location_distance_meters=distance_meters,
            upload_delay_seconds=upload_delay_seconds,
            artifact_status_code=artifact_status_code,
        )

    def assess_manual_review_requirement(
        self,
        submission_id: str,
        decision: EvidenceValidationDecision,
    ) -> EvidenceManualReviewAssessment:
        submission = self._require_submission(submission_id)
        rejected_submission_count = self._count_rejected_submissions(submission.evidence_submission_session_id)
        if EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR in decision.reason_codes:
            return EvidenceManualReviewAssessment(
                required=True,
                trigger_reason_code=EVIDENCE_MANUAL_REVIEW_REASON_DISTANCE_CONFLICT,
                rejected_submission_count=rejected_submission_count,
            )
        if (
            decision.outcome_code == EVIDENCE_VALIDATION_OUTCOME_RETRY_DOCUMENT
            and rejected_submission_count >= MAX_EVIDENCE_RETRY_BEFORE_MANUAL_REVIEW
        ):
            return EvidenceManualReviewAssessment(
                required=True,
                trigger_reason_code=EVIDENCE_MANUAL_REVIEW_REASON_RETRY_LIMIT,
                rejected_submission_count=rejected_submission_count,
            )
        return EvidenceManualReviewAssessment(
            required=False,
            trigger_reason_code=None,
            rejected_submission_count=rejected_submission_count,
        )

    def escalate_submission_manual_review(
        self,
        submission_id: str,
        *,
        trigger_reason_code: str,
        detail: dict | None = None,
    ) -> EvidenceSubmission:
        submission = self._require_submission(submission_id)
        self._evidence_repository.update_submission_artifact_status(
            submission.id,
            artifact_status_code=EVIDENCE_ARTIFACT_STATUS_MANUAL_REVIEW_REQUIRED,
        )
        self._evidence_repository.append_state_log(
            evidence_submission_id=submission.id,
            from_state_code=submission.artifact_status_code,
            to_state_code=EVIDENCE_ARTIFACT_STATUS_MANUAL_REVIEW_REQUIRED,
            reason_code="manual_review_required",
            detail={
                "trigger_reason_code": trigger_reason_code,
                **(detail or {}),
            },
        )
        self._evidence_repository.mark_session_manual_review(submission.evidence_submission_session_id)
        updated_submission = self._evidence_repository.get_submission(submission.id)
        if updated_submission is None:
            raise RuntimeError("운영 검토로 전환한 evidence submission을 다시 읽을 수 없습니다.")
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

    def _require_submission(self, submission_id: str) -> EvidenceSubmission:
        submission = self._evidence_repository.get_submission(submission_id)
        if submission is None:
            raise ValueError("증빙 제출 파일을 찾을 수 없습니다.")
        return submission

    @staticmethod
    def _signal_status(signals_by_type: dict, signal_type_code: str) -> str | None:
        signal = signals_by_type.get(signal_type_code)
        if signal is None:
            return None
        return signal.signal_status_code

    def _count_rejected_submissions(self, session_id: str) -> int:
        submissions = self._evidence_repository.list_submissions_for_session(session_id)
        return sum(
            1
            for item in submissions
            if item.artifact_status_code in {
                EVIDENCE_ARTIFACT_STATUS_REJECTED,
                EVIDENCE_ARTIFACT_STATUS_MANUAL_REVIEW_REQUIRED,
            }
        )

    @staticmethod
    def _artifact_parser_status(signals_by_type: dict) -> str | None:
        for signal_type_code in ("exif_present", "gps_present", "capture_time_present"):
            signal = signals_by_type.get(signal_type_code)
            if signal is None:
                continue
            parser_status = signal.detail.get("parser_status")
            if isinstance(parser_status, str) and parser_status:
                return parser_status
        return None

    @staticmethod
    def _has_staged_artifact(submission: EvidenceSubmission) -> bool:
        return bool(submission.staged_artifact_uri)

    @staticmethod
    def _is_supported_artifact_file(submission: EvidenceSubmission) -> bool:
        mime_type = (submission.mime_type or "").strip().lower()
        if mime_type and mime_type not in SUPPORTED_EVIDENCE_MIME_TYPES:
            return False
        file_name = (submission.file_name or "").strip().lower()
        if "." not in file_name:
            return True
        suffix = "." + file_name.rsplit(".", 1)[-1]
        if suffix not in SUPPORTED_EVIDENCE_FILE_SUFFIXES:
            return False
        return True
