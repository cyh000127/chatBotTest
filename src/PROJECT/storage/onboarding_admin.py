from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from PROJECT.storage.invitations import DEFAULT_LOCAL_ADMIN_USER_ID, INVITATION_STATUS_USED, utc_now_text
from PROJECT.storage.onboarding import (
    DEFAULT_IDENTITY_PROVIDER_CODE,
    ONBOARDING_ACTOR_TYPE_SYSTEM,
    ONBOARDING_STATUS_APPROVED,
    ONBOARDING_STATUS_PENDING_APPROVAL,
    ONBOARDING_STATUS_REJECTED,
    ONBOARDING_STEP_PENDING_APPROVAL,
    OnboardingSession,
    row_to_onboarding_session,
)


PARTICIPANT_STATUS_ACTIVE = "active"
ENROLLMENT_STATUS_ACTIVE = "active"
ENROLLMENT_SOURCE_INVITATION = "invitation"
CONTACT_TYPE_PHONE = "phone"
IDENTITY_LINK_PROVENANCE_ONBOARDING = "onboarding"
OUTBOX_STATUS_PENDING = "pending"
OUTBOX_SOURCE_ONBOARDING_APPROVED = "admin.onboarding.approved"
OUTBOX_SOURCE_ONBOARDING_REJECTED = "admin.onboarding.rejected"
ONBOARDING_EVENT_APPROVED = "onboarding_approved"
ONBOARDING_EVENT_REJECTED = "onboarding_rejected"


class OnboardingApprovalError(ValueError):
    pass


@dataclass(frozen=True)
class OnboardingSubmission:
    onboarding_session_id: str
    project_id: str
    project_invitation_id: str
    provider_user_id: str
    provider_handle: str | None
    preferred_locale_code: str
    name: str
    phone_normalized: str
    submitted_at: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class OnboardingApprovalResult:
    session: OnboardingSession
    participant_id: str
    contact_id: str
    identity_id: str
    enrollment_id: str
    outbox_id: str


@dataclass(frozen=True)
class OnboardingRejectionResult:
    session: OnboardingSession
    outbox_id: str


class SqliteOnboardingAdminRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def list_pending_submissions(self) -> tuple[OnboardingSubmission, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT *
                FROM onboarding_sessions
                WHERE session_status_code = ?
                  AND current_step_code = ?
                ORDER BY submitted_at ASC, created_at ASC
                """,
                (ONBOARDING_STATUS_PENDING_APPROVAL, ONBOARDING_STEP_PENDING_APPROVAL),
            ).fetchall()
            return tuple(_submission_from_session(row_to_onboarding_session(row)) for row in rows)

    def approve_submission(
        self,
        onboarding_session_id: str,
        *,
        admin_user_id: str = DEFAULT_LOCAL_ADMIN_USER_ID,
        message_text: str = "온보딩이 승인되었습니다. 이제 서비스를 이용할 수 있습니다.",
    ) -> OnboardingApprovalResult:
        with self._lock:
            session = self._require_pending_session(onboarding_session_id)
            draft = _require_submission_draft(session)
            now = utc_now_text()
            participant_id = f"participant_{uuid4().hex}"
            contact_id = f"contact_{uuid4().hex}"
            identity_id = f"identity_{uuid4().hex}"
            enrollment_id = f"enrollment_{uuid4().hex}"
            outbox_id = f"outbox_{uuid4().hex}"

            self._connection.execute(
                """
                INSERT INTO participants (
                  id,
                  full_name,
                  preferred_language,
                  participant_status_code,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    participant_id,
                    draft["name"],
                    draft["preferred_locale"],
                    PARTICIPANT_STATUS_ACTIVE,
                    now,
                    now,
                ),
            )
            self._connection.execute(
                """
                INSERT INTO participant_private_contacts (
                  id,
                  participant_id,
                  contact_type_code,
                  normalized_value,
                  raw_value,
                  is_primary,
                  verified_at,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contact_id,
                    participant_id,
                    CONTACT_TYPE_PHONE,
                    draft["phone_normalized"],
                    draft.get("phone_raw") or draft["phone_normalized"],
                    1,
                    now,
                    now,
                    now,
                ),
            )
            self._connection.execute(
                """
                INSERT INTO participant_identities (
                  id,
                  participant_id,
                  identity_provider_code,
                  provider_user_id,
                  provider_handle,
                  linked_contact_id,
                  link_provenance,
                  is_primary,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identity_id,
                    participant_id,
                    session.identity_provider_code,
                    session.provider_user_id,
                    session.provider_handle,
                    contact_id,
                    IDENTITY_LINK_PROVENANCE_ONBOARDING,
                    1,
                    now,
                    now,
                ),
            )
            self._connection.execute(
                """
                INSERT INTO project_enrollments (
                  id,
                  project_id,
                  participant_id,
                  invitation_id,
                  participant_role_code,
                  enrollment_status_code,
                  enrollment_source_code,
                  accepted_at,
                  activated_at,
                  activated_by_admin_user_id,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    enrollment_id,
                    session.project_id,
                    participant_id,
                    session.project_invitation_id,
                    "farmer",
                    ENROLLMENT_STATUS_ACTIVE,
                    ENROLLMENT_SOURCE_INVITATION,
                    now,
                    now,
                    admin_user_id,
                    now,
                    now,
                ),
            )
            self._connection.execute(
                """
                UPDATE onboarding_sessions
                SET participant_identity_id = ?,
                    participant_id = ?,
                    session_status_code = ?,
                    current_step_code = ?,
                    completed_at = ?,
                    result_participant_id = ?,
                    result_enrollment_id = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    identity_id,
                    participant_id,
                    ONBOARDING_STATUS_APPROVED,
                    ONBOARDING_STATUS_APPROVED,
                    now,
                    participant_id,
                    enrollment_id,
                    now,
                    session.id,
                ),
            )
            self._connection.execute(
                """
                UPDATE project_invitations
                SET invite_status_code = ?,
                    used_at = ?,
                    accepted_participant_id = ?,
                    accepted_enrollment_id = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    INVITATION_STATUS_USED,
                    now,
                    participant_id,
                    enrollment_id,
                    now,
                    session.project_invitation_id,
                ),
            )
            self._insert_onboarding_event(
                onboarding_session_id=session.id,
                event_type_code=ONBOARDING_EVENT_APPROVED,
                from_step_code=session.current_step_code,
                to_step_code=ONBOARDING_STATUS_APPROVED,
                from_status_code=session.session_status_code,
                to_status_code=ONBOARDING_STATUS_APPROVED,
                payload={"admin_user_id": admin_user_id},
                occurred_at=now,
            )
            self._insert_outbox_message(
                outbox_id=outbox_id,
                chat_id=int(draft["chat_id"]),
                message_text=message_text,
                source_code=OUTBOX_SOURCE_ONBOARDING_APPROVED,
                created_at=now,
            )
            self._connection.commit()

            approved = self._require_session(session.id)
            return OnboardingApprovalResult(
                session=approved,
                participant_id=participant_id,
                contact_id=contact_id,
                identity_id=identity_id,
                enrollment_id=enrollment_id,
                outbox_id=outbox_id,
            )

    def reject_submission(
        self,
        onboarding_session_id: str,
        *,
        admin_user_id: str = DEFAULT_LOCAL_ADMIN_USER_ID,
        reason_code: str = "admin_rejected",
        message_text: str = "온보딩 신청이 반려되었습니다. 필요한 경우 지원을 요청해주세요.",
    ) -> OnboardingRejectionResult:
        with self._lock:
            session = self._require_pending_session(onboarding_session_id)
            draft = _require_submission_draft(session)
            now = utc_now_text()
            outbox_id = f"outbox_{uuid4().hex}"

            self._connection.execute(
                """
                UPDATE onboarding_sessions
                SET session_status_code = ?,
                    current_step_code = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    ONBOARDING_STATUS_REJECTED,
                    ONBOARDING_STATUS_REJECTED,
                    now,
                    now,
                    session.id,
                ),
            )
            self._insert_onboarding_event(
                onboarding_session_id=session.id,
                event_type_code=ONBOARDING_EVENT_REJECTED,
                from_step_code=session.current_step_code,
                to_step_code=ONBOARDING_STATUS_REJECTED,
                from_status_code=session.session_status_code,
                to_status_code=ONBOARDING_STATUS_REJECTED,
                payload={"admin_user_id": admin_user_id, "reason_code": reason_code},
                occurred_at=now,
            )
            self._insert_outbox_message(
                outbox_id=outbox_id,
                chat_id=int(draft["chat_id"]),
                message_text=message_text,
                source_code=OUTBOX_SOURCE_ONBOARDING_REJECTED,
                created_at=now,
            )
            self._connection.commit()

            rejected = self._require_session(session.id)
            return OnboardingRejectionResult(session=rejected, outbox_id=outbox_id)

    def _require_pending_session(self, onboarding_session_id: str) -> OnboardingSession:
        session = self._require_session(onboarding_session_id)
        if session.session_status_code != ONBOARDING_STATUS_PENDING_APPROVAL:
            raise OnboardingApprovalError("승인 대기 상태의 온보딩만 처리할 수 있습니다.")
        if session.current_step_code != ONBOARDING_STEP_PENDING_APPROVAL:
            raise OnboardingApprovalError("승인 대기 단계의 온보딩만 처리할 수 있습니다.")
        return session

    def _require_session(self, onboarding_session_id: str) -> OnboardingSession:
        row = self._connection.execute(
            "SELECT * FROM onboarding_sessions WHERE id = ?",
            (onboarding_session_id,),
        ).fetchone()
        if row is None:
            raise OnboardingApprovalError("온보딩 세션을 찾을 수 없습니다.")
        return row_to_onboarding_session(row)

    def _insert_onboarding_event(
        self,
        *,
        onboarding_session_id: str,
        event_type_code: str,
        from_step_code: str,
        to_step_code: str,
        from_status_code: str,
        to_status_code: str,
        payload: dict,
        occurred_at: str,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO onboarding_session_events (
              id,
              onboarding_session_id,
              event_type_code,
              from_step_code,
              to_step_code,
              from_status_code,
              to_status_code,
              payload_json,
              acted_by_type,
              occurred_at,
              recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"onboarding_event_{uuid4().hex}",
                onboarding_session_id,
                event_type_code,
                from_step_code,
                to_step_code,
                from_status_code,
                to_status_code,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                ONBOARDING_ACTOR_TYPE_SYSTEM,
                occurred_at,
                occurred_at,
            ),
        )

    def _insert_outbox_message(
        self,
        *,
        outbox_id: str,
        chat_id: int,
        message_text: str,
        source_code: str,
        created_at: str,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO outbox_messages (
              id,
              chat_id,
              message_text,
              delivery_state_code,
              source_code,
              created_at,
              updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                outbox_id,
                chat_id,
                message_text,
                OUTBOX_STATUS_PENDING,
                source_code,
                created_at,
                created_at,
            ),
        )


def _submission_from_session(session: OnboardingSession) -> OnboardingSubmission:
    draft = _require_submission_draft(session)
    if session.project_id is None or session.project_invitation_id is None:
        raise OnboardingApprovalError("온보딩 세션의 프로젝트 또는 초대 정보가 없습니다.")
    return OnboardingSubmission(
        onboarding_session_id=session.id,
        project_id=session.project_id,
        project_invitation_id=session.project_invitation_id,
        provider_user_id=session.provider_user_id,
        provider_handle=session.provider_handle,
        preferred_locale_code=session.preferred_locale_code,
        name=draft["name"],
        phone_normalized=draft["phone_normalized"],
        submitted_at=session.submitted_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _require_submission_draft(session: OnboardingSession) -> dict:
    try:
        draft = json.loads(session.draft_payload_json)
    except json.JSONDecodeError as exc:
        raise OnboardingApprovalError("온보딩 draft를 읽을 수 없습니다.") from exc
    if not isinstance(draft, dict):
        raise OnboardingApprovalError("온보딩 draft 형식이 올바르지 않습니다.")
    required = ("name", "preferred_locale", "phone_normalized", "chat_id")
    missing = [field for field in required if not draft.get(field)]
    if missing:
        raise OnboardingApprovalError(f"온보딩 draft 필수 값이 없습니다: {', '.join(missing)}")
    return draft
