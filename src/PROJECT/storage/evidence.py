from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from PROJECT.storage.invitations import utc_now_text

EVIDENCE_REQUEST_STATUS_OPEN = "open"
EVIDENCE_REQUEST_STATUS_SATISFIED = "satisfied"
EVIDENCE_REQUEST_STATUS_CANCELLED = "cancelled"
EVIDENCE_REQUEST_STATUS_EXPIRED = "expired"

EVIDENCE_SESSION_STATUS_WAITING_LOCATION = "waiting_location"
EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT = "waiting_document"
EVIDENCE_SESSION_STATUS_VALIDATING = "validating"
EVIDENCE_SESSION_STATUS_COMPLETED = "completed"
EVIDENCE_SESSION_STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"
EVIDENCE_SESSION_STATUS_ABANDONED = "abandoned"

EVIDENCE_ARTIFACT_STATUS_UPLOADED = "uploaded"
EVIDENCE_ARTIFACT_STATUS_SIGNALS_READY = "signals_ready"
EVIDENCE_ARTIFACT_STATUS_ACCEPTED = "accepted"
EVIDENCE_ARTIFACT_STATUS_REJECTED = "rejected"
EVIDENCE_ARTIFACT_STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"


@dataclass(frozen=True)
class EvidenceRequestEvent:
    id: str
    project_id: str
    participant_id: str
    field_season_id: str | None
    seasonal_event_id: str | None
    field_binding_id: str | None
    field_id: str | None
    request_type_code: str
    request_status_code: str
    request_reason_code: str | None
    requested_via_code: str
    due_at: str | None
    satisfied_at: str | None
    cancelled_at: str | None
    payload_json: str
    created_at: str
    updated_at: str

    @property
    def payload(self) -> dict:
        parsed = json.loads(self.payload_json)
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class EvidenceSubmissionSession:
    id: str
    evidence_request_event_id: str
    project_id: str
    participant_id: str
    provider_user_id: str
    chat_id: int
    field_season_id: str | None
    field_binding_id: str | None
    field_id: str | None
    session_status_code: str
    current_step_code: str
    accepted_location_latitude: float | None
    accepted_location_longitude: float | None
    accepted_location_accuracy_meters: float | None
    accepted_location_recorded_at: str | None
    draft_payload_json: str
    created_at: str
    updated_at: str
    completed_at: str | None
    abandoned_at: str | None

    @property
    def draft_payload(self) -> dict:
        parsed = json.loads(self.draft_payload_json)
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class EvidenceSubmission:
    id: str
    evidence_submission_session_id: str
    evidence_request_event_id: str
    project_id: str
    participant_id: str
    field_season_id: str | None
    field_binding_id: str | None
    field_id: str | None
    provider_message_id: str | None
    provider_file_id: str | None
    provider_file_unique_id: str | None
    file_name: str | None
    mime_type: str | None
    file_size_bytes: int | None
    artifact_status_code: str
    staged_artifact_uri: str | None
    checksum_sha256: str | None
    captured_at: str | None
    uploaded_at: str
    submitted_at: str | None
    payload_json: str
    created_at: str
    updated_at: str

    @property
    def payload(self) -> dict:
        parsed = json.loads(self.payload_json)
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class EvidenceValidationSignal:
    id: str
    evidence_submission_id: str
    signal_type_code: str
    signal_status_code: str
    numeric_value: float | None
    text_value: str | None
    detail_json: str
    created_at: str

    @property
    def detail(self) -> dict:
        parsed = json.loads(self.detail_json)
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class EvidenceValidationStateLog:
    id: str
    evidence_submission_id: str
    from_state_code: str | None
    to_state_code: str
    reason_code: str | None
    detail_json: str
    created_at: str

    @property
    def detail(self) -> dict:
        parsed = json.loads(self.detail_json)
        return parsed if isinstance(parsed, dict) else {}


class SqliteEvidenceRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def create_request_event(
        self,
        *,
        project_id: str,
        participant_id: str,
        request_type_code: str,
        request_reason_code: str | None = None,
        requested_via_code: str = "runtime",
        due_at: str | None = None,
        field_season_id: str | None = None,
        seasonal_event_id: str | None = None,
        field_binding_id: str | None = None,
        field_id: str | None = None,
        payload: dict | None = None,
    ) -> EvidenceRequestEvent:
        with self._lock:
            now = utc_now_text()
            request_id = f"evidence_request_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO evidence_request_events (
                  id,
                  project_id,
                  participant_id,
                  field_season_id,
                  seasonal_event_id,
                  field_binding_id,
                  field_id,
                  request_type_code,
                  request_status_code,
                  request_reason_code,
                  requested_via_code,
                  due_at,
                  payload_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    project_id,
                    participant_id,
                    field_season_id,
                    seasonal_event_id,
                    field_binding_id,
                    field_id,
                    request_type_code,
                    EVIDENCE_REQUEST_STATUS_OPEN,
                    request_reason_code,
                    requested_via_code,
                    due_at,
                    json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_request_event(request_id)
            if created is None:
                raise RuntimeError("생성한 evidence request를 다시 읽을 수 없습니다.")
            return created

    def get_request_event(self, request_id: str) -> EvidenceRequestEvent | None:
        row = self._connection.execute(
            "SELECT * FROM evidence_request_events WHERE id = ?",
            (request_id,),
        ).fetchone()
        if row is None:
            return None
        return EvidenceRequestEvent(**dict(row))

    def create_submission_session(
        self,
        *,
        evidence_request_event_id: str,
        project_id: str,
        participant_id: str,
        provider_user_id: str,
        chat_id: int,
        field_season_id: str | None = None,
        field_binding_id: str | None = None,
        field_id: str | None = None,
        draft_payload: dict | None = None,
    ) -> EvidenceSubmissionSession:
        with self._lock:
            now = utc_now_text()
            session_id = f"evidence_session_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO evidence_submission_sessions (
                  id,
                  evidence_request_event_id,
                  project_id,
                  participant_id,
                  provider_user_id,
                  chat_id,
                  field_season_id,
                  field_binding_id,
                  field_id,
                  session_status_code,
                  current_step_code,
                  draft_payload_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    evidence_request_event_id,
                    project_id,
                    participant_id,
                    provider_user_id,
                    chat_id,
                    field_season_id,
                    field_binding_id,
                    field_id,
                    EVIDENCE_SESSION_STATUS_WAITING_LOCATION,
                    EVIDENCE_SESSION_STATUS_WAITING_LOCATION,
                    json.dumps(draft_payload or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_submission_session(session_id)
            if created is None:
                raise RuntimeError("생성한 evidence session을 다시 읽을 수 없습니다.")
            return created

    def get_submission_session(self, session_id: str) -> EvidenceSubmissionSession | None:
        row = self._connection.execute(
            "SELECT * FROM evidence_submission_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return EvidenceSubmissionSession(**dict(row))

    def accept_location(
        self,
        session_id: str,
        *,
        latitude: float,
        longitude: float,
        accuracy_meters: float | None,
        recorded_at: str | None = None,
    ) -> EvidenceSubmissionSession:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE evidence_submission_sessions
                SET accepted_location_latitude = ?,
                    accepted_location_longitude = ?,
                    accepted_location_accuracy_meters = ?,
                    accepted_location_recorded_at = ?,
                    session_status_code = ?,
                    current_step_code = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    latitude,
                    longitude,
                    accuracy_meters,
                    recorded_at or now,
                    EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT,
                    EVIDENCE_SESSION_STATUS_WAITING_DOCUMENT,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
        updated = self.get_submission_session(session_id)
        if updated is None:
            raise RuntimeError("위치를 반영한 evidence session을 다시 읽을 수 없습니다.")
        return updated

    def mark_session_validating(self, session_id: str) -> EvidenceSubmissionSession:
        return self._update_session_status(
            session_id,
            session_status_code=EVIDENCE_SESSION_STATUS_VALIDATING,
            current_step_code=EVIDENCE_SESSION_STATUS_VALIDATING,
        )

    def mark_session_completed(self, session_id: str) -> EvidenceSubmissionSession:
        return self._update_session_status(
            session_id,
            session_status_code=EVIDENCE_SESSION_STATUS_COMPLETED,
            current_step_code=EVIDENCE_SESSION_STATUS_COMPLETED,
            completed_at=utc_now_text(),
        )

    def mark_session_manual_review(self, session_id: str) -> EvidenceSubmissionSession:
        return self._update_session_status(
            session_id,
            session_status_code=EVIDENCE_SESSION_STATUS_MANUAL_REVIEW_REQUIRED,
            current_step_code=EVIDENCE_SESSION_STATUS_MANUAL_REVIEW_REQUIRED,
        )

    def mark_session_abandoned(self, session_id: str) -> EvidenceSubmissionSession:
        return self._update_session_status(
            session_id,
            session_status_code=EVIDENCE_SESSION_STATUS_ABANDONED,
            current_step_code=EVIDENCE_SESSION_STATUS_ABANDONED,
            abandoned_at=utc_now_text(),
        )

    def create_submission(
        self,
        *,
        evidence_submission_session_id: str,
        evidence_request_event_id: str,
        project_id: str,
        participant_id: str,
        uploaded_at: str | None = None,
        field_season_id: str | None = None,
        field_binding_id: str | None = None,
        field_id: str | None = None,
        provider_message_id: str | None = None,
        provider_file_id: str | None = None,
        provider_file_unique_id: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        file_size_bytes: int | None = None,
        staged_artifact_uri: str | None = None,
        checksum_sha256: str | None = None,
        captured_at: str | None = None,
        payload: dict | None = None,
    ) -> EvidenceSubmission:
        with self._lock:
            now = utc_now_text()
            uploaded = uploaded_at or now
            submission_id = f"evidence_submission_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO evidence_submissions (
                  id,
                  evidence_submission_session_id,
                  evidence_request_event_id,
                  project_id,
                  participant_id,
                  field_season_id,
                  field_binding_id,
                  field_id,
                  provider_message_id,
                  provider_file_id,
                  provider_file_unique_id,
                  file_name,
                  mime_type,
                  file_size_bytes,
                  artifact_status_code,
                  staged_artifact_uri,
                  checksum_sha256,
                  captured_at,
                  uploaded_at,
                  payload_json,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    submission_id,
                    evidence_submission_session_id,
                    evidence_request_event_id,
                    project_id,
                    participant_id,
                    field_season_id,
                    field_binding_id,
                    field_id,
                    provider_message_id,
                    provider_file_id,
                    provider_file_unique_id,
                    file_name,
                    mime_type,
                    file_size_bytes,
                    EVIDENCE_ARTIFACT_STATUS_UPLOADED,
                    staged_artifact_uri,
                    checksum_sha256,
                    captured_at,
                    uploaded,
                    json.dumps(payload or {}, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_submission(submission_id)
            if created is None:
                raise RuntimeError("생성한 evidence submission을 다시 읽을 수 없습니다.")
            return created

    def get_submission(self, submission_id: str) -> EvidenceSubmission | None:
        row = self._connection.execute(
            "SELECT * FROM evidence_submissions WHERE id = ?",
            (submission_id,),
        ).fetchone()
        if row is None:
            return None
        return EvidenceSubmission(**dict(row))

    def list_submissions_for_session(self, session_id: str) -> tuple[EvidenceSubmission, ...]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM evidence_submissions
            WHERE evidence_submission_session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        ).fetchall()
        return tuple(EvidenceSubmission(**dict(row)) for row in rows)

    def update_submission_artifact_status(
        self,
        submission_id: str,
        *,
        artifact_status_code: str,
        submitted_at: str | None = None,
    ) -> EvidenceSubmission:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE evidence_submissions
                SET artifact_status_code = ?,
                    submitted_at = COALESCE(?, submitted_at),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    artifact_status_code,
                    submitted_at,
                    now,
                    submission_id,
                ),
            )
            self._connection.commit()
        updated = self.get_submission(submission_id)
        if updated is None:
            raise RuntimeError("갱신한 evidence submission을 다시 읽을 수 없습니다.")
        return updated

    def create_validation_signal(
        self,
        *,
        evidence_submission_id: str,
        signal_type_code: str,
        signal_status_code: str,
        numeric_value: float | None = None,
        text_value: str | None = None,
        detail: dict | None = None,
    ) -> EvidenceValidationSignal:
        with self._lock:
            now = utc_now_text()
            signal_id = f"evidence_signal_{uuid4().hex}"
            detail_json = json.dumps(detail or {}, ensure_ascii=False, sort_keys=True)
            self._connection.execute(
                """
                INSERT INTO evidence_validation_signals (
                  id,
                  evidence_submission_id,
                  signal_type_code,
                  signal_status_code,
                  numeric_value,
                  text_value,
                  detail_json,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal_id,
                    evidence_submission_id,
                    signal_type_code,
                    signal_status_code,
                    numeric_value,
                    text_value,
                    detail_json,
                    now,
                ),
            )
            self._connection.commit()
            return EvidenceValidationSignal(
                id=signal_id,
                evidence_submission_id=evidence_submission_id,
                signal_type_code=signal_type_code,
                signal_status_code=signal_status_code,
                numeric_value=numeric_value,
                text_value=text_value,
                detail_json=detail_json,
                created_at=now,
            )

    def list_validation_signals(self, evidence_submission_id: str) -> tuple[EvidenceValidationSignal, ...]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM evidence_validation_signals
            WHERE evidence_submission_id = ?
            ORDER BY created_at ASC
            """,
            (evidence_submission_id,),
        ).fetchall()
        return tuple(EvidenceValidationSignal(**dict(row)) for row in rows)

    def append_state_log(
        self,
        *,
        evidence_submission_id: str,
        to_state_code: str,
        from_state_code: str | None = None,
        reason_code: str | None = None,
        detail: dict | None = None,
    ) -> EvidenceValidationStateLog:
        with self._lock:
            now = utc_now_text()
            log_id = f"evidence_state_{uuid4().hex}"
            detail_json = json.dumps(detail or {}, ensure_ascii=False, sort_keys=True)
            self._connection.execute(
                """
                INSERT INTO evidence_validation_state_logs (
                  id,
                  evidence_submission_id,
                  from_state_code,
                  to_state_code,
                  reason_code,
                  detail_json,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    evidence_submission_id,
                    from_state_code,
                    to_state_code,
                    reason_code,
                    detail_json,
                    now,
                ),
            )
            self._connection.commit()
            return EvidenceValidationStateLog(
                id=log_id,
                evidence_submission_id=evidence_submission_id,
                from_state_code=from_state_code,
                to_state_code=to_state_code,
                reason_code=reason_code,
                detail_json=detail_json,
                created_at=now,
            )

    def list_state_logs(self, evidence_submission_id: str) -> tuple[EvidenceValidationStateLog, ...]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM evidence_validation_state_logs
            WHERE evidence_submission_id = ?
            ORDER BY created_at ASC
            """,
            (evidence_submission_id,),
        ).fetchall()
        return tuple(EvidenceValidationStateLog(**dict(row)) for row in rows)

    def _update_session_status(
        self,
        session_id: str,
        *,
        session_status_code: str,
        current_step_code: str,
        completed_at: str | None = None,
        abandoned_at: str | None = None,
    ) -> EvidenceSubmissionSession:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE evidence_submission_sessions
                SET session_status_code = ?,
                    current_step_code = ?,
                    completed_at = COALESCE(?, completed_at),
                    abandoned_at = COALESCE(?, abandoned_at),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    session_status_code,
                    current_step_code,
                    completed_at,
                    abandoned_at,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
        updated = self.get_submission_session(session_id)
        if updated is None:
            raise RuntimeError("갱신한 evidence session을 다시 읽을 수 없습니다.")
        return updated
