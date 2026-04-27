from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from PROJECT.conversations.input_resolve.states import (
    STATE_INPUT_RESOLVE_CANDIDATES,
    STATE_INPUT_RESOLVE_DECISION,
    STATE_INPUT_RESOLVE_METHOD,
    STATE_INPUT_RESOLVE_RAW_INPUT,
    STATE_INPUT_RESOLVE_TARGET,
)
from PROJECT.storage.invitations import utc_now_text

INPUT_RESOLUTION_STATUS_COLLECTING_TARGET = "collecting_target"
INPUT_RESOLUTION_STATUS_COLLECTING_METHOD = "collecting_method"
INPUT_RESOLUTION_STATUS_COLLECTING_RAW_INPUT = "collecting_raw_input"
INPUT_RESOLUTION_STATUS_CANDIDATE_REVIEW = "candidate_review"
INPUT_RESOLUTION_STATUS_DECISION_PENDING = "decision_pending"
INPUT_RESOLUTION_STATUS_RESOLVED = "resolved"
INPUT_RESOLUTION_STATUS_MANUAL_REVIEW_REQUIRED = "manual_review_required"


@dataclass(frozen=True)
class InputResolutionSession:
    id: str
    project_id: str
    participant_id: str
    provider_user_id: str
    chat_id: int
    target_type_code: str | None
    method_code: str | None
    session_status_code: str
    current_step_code: str
    raw_input_text: str | None
    selected_candidate_id: str | None
    resolved_value_json: str | None
    created_at: str
    updated_at: str
    resolved_at: str | None
    escalated_at: str | None

    @property
    def resolved_value(self) -> dict | None:
        if not self.resolved_value_json:
            return None
        parsed = json.loads(self.resolved_value_json)
        return parsed if isinstance(parsed, dict) else None


@dataclass(frozen=True)
class InputResolutionAttempt:
    id: str
    input_resolution_session_id: str
    method_code: str
    raw_input_text: str
    created_at: str


@dataclass(frozen=True)
class InputResolutionCandidate:
    id: str
    input_resolution_session_id: str
    input_resolution_attempt_id: str
    candidate_rank: int
    candidate_type_code: str
    raw_value: str
    normalized_value_json: str
    confidence_score: float | None
    created_at: str

    @property
    def normalized_value(self) -> dict:
        parsed = json.loads(self.normalized_value_json)
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class InputResolutionDecision:
    id: str
    input_resolution_session_id: str
    selected_candidate_id: str | None
    decision_code: str
    note: str | None
    created_at: str


class SqliteInputResolutionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def create_session(
        self,
        *,
        project_id: str,
        participant_id: str,
        provider_user_id: str,
        chat_id: int,
    ) -> InputResolutionSession:
        with self._lock:
            now = utc_now_text()
            session_id = f"input_resolution_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO input_resolution_sessions (
                  id,
                  project_id,
                  participant_id,
                  provider_user_id,
                  chat_id,
                  session_status_code,
                  current_step_code,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    project_id,
                    participant_id,
                    provider_user_id,
                    chat_id,
                    INPUT_RESOLUTION_STATUS_COLLECTING_TARGET,
                    STATE_INPUT_RESOLVE_TARGET,
                    now,
                    now,
                ),
            )
            self._connection.commit()
            created = self.get_session(session_id)
            if created is None:
                raise RuntimeError("생성한 input-resolution session을 다시 읽을 수 없습니다.")
            return created

    def get_session(self, session_id: str) -> InputResolutionSession | None:
        row = self._connection.execute(
            "SELECT * FROM input_resolution_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return InputResolutionSession(**dict(row))

    def update_target(self, session_id: str, target_type_code: str) -> InputResolutionSession:
        return self._update_session(
            session_id,
            target_type_code=target_type_code,
            session_status_code=INPUT_RESOLUTION_STATUS_COLLECTING_METHOD,
            current_step_code=STATE_INPUT_RESOLVE_METHOD,
        )

    def update_method(self, session_id: str, method_code: str) -> InputResolutionSession:
        return self._update_session(
            session_id,
            method_code=method_code,
            session_status_code=INPUT_RESOLUTION_STATUS_COLLECTING_RAW_INPUT,
            current_step_code=STATE_INPUT_RESOLVE_RAW_INPUT,
        )

    def create_attempt(
        self,
        *,
        session_id: str,
        method_code: str,
        raw_input_text: str,
    ) -> InputResolutionAttempt:
        with self._lock:
            now = utc_now_text()
            attempt_id = f"input_resolution_attempt_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO input_resolution_attempts (
                  id,
                  input_resolution_session_id,
                  method_code,
                  raw_input_text,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    session_id,
                    method_code,
                    raw_input_text,
                    now,
                ),
            )
            self._connection.execute(
                """
                UPDATE input_resolution_sessions
                SET method_code = ?,
                    raw_input_text = ?,
                    session_status_code = ?,
                    current_step_code = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    method_code,
                    raw_input_text,
                    INPUT_RESOLUTION_STATUS_COLLECTING_RAW_INPUT,
                    STATE_INPUT_RESOLVE_RAW_INPUT,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
            return InputResolutionAttempt(
                id=attempt_id,
                input_resolution_session_id=session_id,
                method_code=method_code,
                raw_input_text=raw_input_text,
                created_at=now,
            )

    def create_candidates(
        self,
        *,
        session_id: str,
        attempt_id: str,
        candidates: list[dict],
    ) -> tuple[InputResolutionCandidate, ...]:
        with self._lock:
            now = utc_now_text()
            created_items: list[InputResolutionCandidate] = []
            for rank, candidate in enumerate(candidates, start=1):
                candidate_id = f"input_resolution_candidate_{uuid4().hex}"
                normalized_value = candidate.get("normalized_value") or {}
                self._connection.execute(
                    """
                    INSERT INTO input_resolution_candidates (
                      id,
                      input_resolution_session_id,
                      input_resolution_attempt_id,
                      candidate_rank,
                      candidate_type_code,
                      raw_value,
                      normalized_value_json,
                      confidence_score,
                      created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate_id,
                        session_id,
                        attempt_id,
                        rank,
                        candidate["candidate_type_code"],
                        candidate["raw_value"],
                        json.dumps(normalized_value, ensure_ascii=False, sort_keys=True),
                        candidate.get("confidence_score"),
                        now,
                    ),
                )
                created_items.append(
                    InputResolutionCandidate(
                        id=candidate_id,
                        input_resolution_session_id=session_id,
                        input_resolution_attempt_id=attempt_id,
                        candidate_rank=rank,
                        candidate_type_code=candidate["candidate_type_code"],
                        raw_value=candidate["raw_value"],
                        normalized_value_json=json.dumps(normalized_value, ensure_ascii=False, sort_keys=True),
                        confidence_score=candidate.get("confidence_score"),
                        created_at=now,
                    )
                )
            next_status = (
                INPUT_RESOLUTION_STATUS_CANDIDATE_REVIEW if created_items else INPUT_RESOLUTION_STATUS_COLLECTING_RAW_INPUT
            )
            next_step = STATE_INPUT_RESOLVE_CANDIDATES if created_items else STATE_INPUT_RESOLVE_RAW_INPUT
            self._connection.execute(
                """
                UPDATE input_resolution_sessions
                SET session_status_code = ?,
                    current_step_code = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    next_status,
                    next_step,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
            return tuple(created_items)

    def latest_candidates(self, session_id: str) -> tuple[InputResolutionCandidate, ...]:
        rows = self._connection.execute(
            """
            SELECT c.*
            FROM input_resolution_candidates c
            JOIN (
              SELECT input_resolution_attempt_id
              FROM input_resolution_candidates
              WHERE input_resolution_session_id = ?
              ORDER BY created_at DESC, candidate_rank ASC
              LIMIT 1
            ) latest
              ON latest.input_resolution_attempt_id = c.input_resolution_attempt_id
            WHERE c.input_resolution_session_id = ?
            ORDER BY c.candidate_rank ASC
            """,
            (session_id, session_id),
        ).fetchall()
        return tuple(InputResolutionCandidate(**dict(row)) for row in rows)

    def candidate_by_id(self, candidate_id: str) -> InputResolutionCandidate | None:
        row = self._connection.execute(
            "SELECT * FROM input_resolution_candidates WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            return None
        return InputResolutionCandidate(**dict(row))

    def mark_candidate_selected(self, session_id: str, candidate_id: str) -> InputResolutionSession:
        return self._update_session(
            session_id,
            selected_candidate_id=candidate_id,
            session_status_code=INPUT_RESOLUTION_STATUS_DECISION_PENDING,
            current_step_code=STATE_INPUT_RESOLVE_DECISION,
        )

    def mark_resolved(
        self,
        session_id: str,
        *,
        selected_candidate_id: str,
        resolved_value: dict,
        note: str | None = None,
    ) -> InputResolutionSession:
        with self._lock:
            now = utc_now_text()
            decision_id = f"input_resolution_decision_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO input_resolution_decisions (
                  id,
                  input_resolution_session_id,
                  selected_candidate_id,
                  decision_code,
                  note,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    session_id,
                    selected_candidate_id,
                    "resolved",
                    note,
                    now,
                ),
            )
            self._connection.execute(
                """
                UPDATE input_resolution_sessions
                SET selected_candidate_id = ?,
                    resolved_value_json = ?,
                    session_status_code = ?,
                    current_step_code = ?,
                    resolved_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    selected_candidate_id,
                    json.dumps(resolved_value, ensure_ascii=False, sort_keys=True),
                    INPUT_RESOLUTION_STATUS_RESOLVED,
                    STATE_INPUT_RESOLVE_DECISION,
                    now,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
        updated = self.get_session(session_id)
        if updated is None:
            raise RuntimeError("resolved session을 다시 읽을 수 없습니다.")
        return updated

    def mark_retry_later(self, session_id: str, *, note: str | None = None) -> InputResolutionSession:
        with self._lock:
            now = utc_now_text()
            decision_id = f"input_resolution_decision_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO input_resolution_decisions (
                  id,
                  input_resolution_session_id,
                  selected_candidate_id,
                  decision_code,
                  note,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    session_id,
                    None,
                    "retry_later",
                    note,
                    now,
                ),
            )
            self._connection.execute(
                """
                UPDATE input_resolution_sessions
                SET session_status_code = ?,
                    current_step_code = ?,
                    selected_candidate_id = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    INPUT_RESOLUTION_STATUS_COLLECTING_RAW_INPUT,
                    STATE_INPUT_RESOLVE_RAW_INPUT,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
        updated = self.get_session(session_id)
        if updated is None:
            raise RuntimeError("retry session을 다시 읽을 수 없습니다.")
        return updated

    def mark_manual_review(self, session_id: str, *, note: str | None = None) -> InputResolutionSession:
        with self._lock:
            now = utc_now_text()
            decision_id = f"input_resolution_decision_{uuid4().hex}"
            self._connection.execute(
                """
                INSERT INTO input_resolution_decisions (
                  id,
                  input_resolution_session_id,
                  selected_candidate_id,
                  decision_code,
                  note,
                  created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    session_id,
                    None,
                    "manual_review",
                    note,
                    now,
                ),
            )
            self._connection.execute(
                """
                UPDATE input_resolution_sessions
                SET session_status_code = ?,
                    current_step_code = ?,
                    escalated_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    INPUT_RESOLUTION_STATUS_MANUAL_REVIEW_REQUIRED,
                    STATE_INPUT_RESOLVE_DECISION,
                    now,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
        updated = self.get_session(session_id)
        if updated is None:
            raise RuntimeError("manual review session을 다시 읽을 수 없습니다.")
        return updated

    def count_attempts(self, session_id: str) -> int:
        row = self._connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM input_resolution_attempts
            WHERE input_resolution_session_id = ?
            """,
            (session_id,),
        ).fetchone()
        return int(row["count"]) if row is not None else 0

    def list_decisions(self, session_id: str) -> tuple[InputResolutionDecision, ...]:
        rows = self._connection.execute(
            """
            SELECT *
            FROM input_resolution_decisions
            WHERE input_resolution_session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        ).fetchall()
        return tuple(InputResolutionDecision(**dict(row)) for row in rows)

    def _update_session(
        self,
        session_id: str,
        *,
        target_type_code: str | None = None,
        method_code: str | None = None,
        selected_candidate_id: str | None = None,
        session_status_code: str | None = None,
        current_step_code: str | None = None,
    ) -> InputResolutionSession:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE input_resolution_sessions
                SET target_type_code = COALESCE(?, target_type_code),
                    method_code = COALESCE(?, method_code),
                    selected_candidate_id = COALESCE(?, selected_candidate_id),
                    session_status_code = COALESCE(?, session_status_code),
                    current_step_code = COALESCE(?, current_step_code),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    target_type_code,
                    method_code,
                    selected_candidate_id,
                    session_status_code,
                    current_step_code,
                    now,
                    session_id,
                ),
            )
            self._connection.commit()
        updated = self.get_session(session_id)
        if updated is None:
            raise RuntimeError("input-resolution session을 다시 읽을 수 없습니다.")
        return updated
