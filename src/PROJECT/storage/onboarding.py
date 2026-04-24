from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from PROJECT.i18n.translator import DEFAULT_LOCALE
from PROJECT.storage.invitations import AdminInvitation, utc_now_text


DEFAULT_CHANNEL_CODE = "telegram"
DEFAULT_IDENTITY_PROVIDER_CODE = "telegram"
ONBOARDING_STATUS_STARTED = "started"
ONBOARDING_STATUS_COLLECTING = "collecting_basic_info"
ONBOARDING_STATUS_PENDING_APPROVAL = "pending_approval"
ONBOARDING_STATUS_APPROVED = "approved"
ONBOARDING_STATUS_REJECTED = "rejected"
ONBOARDING_STEP_LANGUAGE_SELECT = "language_select"
ONBOARDING_STEP_NAME_INPUT = "name_input"
ONBOARDING_STEP_PHONE_INPUT = "phone_input"
ONBOARDING_STEP_PROJECT_CONFIRM = "project_confirm"
ONBOARDING_STEP_PENDING_APPROVAL = "pending_approval"
ONBOARDING_EVENT_STARTED = "onboarding_started"
ONBOARDING_EVENT_LOCALE_SELECTED = "onboarding_locale_selected"
ONBOARDING_EVENT_NAME_COLLECTED = "onboarding_name_collected"
ONBOARDING_EVENT_PHONE_COLLECTED = "onboarding_phone_collected"
ONBOARDING_EVENT_STEP_CHANGED = "onboarding_step_changed"
ONBOARDING_EVENT_SUBMITTED = "onboarding_submitted"
ONBOARDING_ACTOR_TYPE_SYSTEM = "system"
OPEN_ONBOARDING_STATUSES = (
    ONBOARDING_STATUS_STARTED,
    ONBOARDING_STATUS_COLLECTING,
    ONBOARDING_STATUS_PENDING_APPROVAL,
)


@dataclass(frozen=True)
class OnboardingSession:
    id: str
    channel_code: str
    identity_provider_code: str
    provider_user_id: str
    provider_handle: str | None
    participant_identity_id: str | None
    participant_id: str | None
    project_invitation_id: str | None
    project_id: str | None
    session_status_code: str
    current_step_code: str
    preferred_locale_code: str
    draft_payload_json: str
    last_inbound_channel_message_id: str | None
    last_outbound_channel_message_id: str | None
    started_at: str
    last_interaction_at: str
    expires_at: str | None
    submitted_at: str | None
    completed_at: str | None
    abandoned_at: str | None
    result_participant_id: str | None
    result_enrollment_id: str | None
    created_at: str
    updated_at: str


class SqliteOnboardingRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def create_or_resume_from_invitation(
        self,
        *,
        invitation: AdminInvitation,
        provider_user_id: str,
        provider_handle: str | None = None,
        preferred_locale_code: str = DEFAULT_LOCALE,
    ) -> OnboardingSession:
        with self._lock:
            existing = self._find_open_session(
                project_invitation_id=invitation.id,
                provider_user_id=provider_user_id,
            )
            if existing is not None:
                self._touch_session(existing.id, provider_handle=provider_handle)
                refreshed = self.get_by_id(existing.id)
                if refreshed is None:
                    raise RuntimeError("온보딩 세션을 다시 읽을 수 없습니다.")
                return refreshed

            now = utc_now_text()
            onboarding_session_id = f"onboarding_{uuid4().hex}"
            draft_payload = {
                "invite_code": invitation.invite_code,
                "project_id": invitation.project_id,
            }
            self._connection.execute(
                """
                INSERT INTO onboarding_sessions (
                  id,
                  channel_code,
                  identity_provider_code,
                  provider_user_id,
                  provider_handle,
                  project_invitation_id,
                  project_id,
                  session_status_code,
                  current_step_code,
                  preferred_locale_code,
                  draft_payload_json,
                  started_at,
                  last_interaction_at,
                  created_at,
                  updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    onboarding_session_id,
                    invitation.channel_code or DEFAULT_CHANNEL_CODE,
                    DEFAULT_IDENTITY_PROVIDER_CODE,
                    provider_user_id,
                    provider_handle,
                    invitation.id,
                    invitation.project_id,
                    ONBOARDING_STATUS_STARTED,
                    ONBOARDING_STEP_LANGUAGE_SELECT,
                    preferred_locale_code,
                    json.dumps(draft_payload, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                    now,
                    now,
                ),
            )
            self._insert_event(
                onboarding_session_id=onboarding_session_id,
                event_type_code=ONBOARDING_EVENT_STARTED,
                to_step_code=ONBOARDING_STEP_LANGUAGE_SELECT,
                to_status_code=ONBOARDING_STATUS_STARTED,
                payload={
                    "invite_code": invitation.invite_code,
                    "project_id": invitation.project_id,
                },
                occurred_at=now,
            )
            self._connection.commit()

            created = self.get_by_id(onboarding_session_id)
            if created is None:
                raise RuntimeError("생성한 온보딩 세션을 다시 읽을 수 없습니다.")
            return created

    def get_by_id(self, onboarding_session_id: str) -> OnboardingSession | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM onboarding_sessions WHERE id = ?",
                (onboarding_session_id,),
            ).fetchone()
            if row is None:
                return None
            return row_to_onboarding_session(row)

    def update_locale(self, onboarding_session_id: str, locale_code: str) -> OnboardingSession:
        session = self._require_by_id(onboarding_session_id)
        draft = _draft_from_json(session.draft_payload_json)
        draft["preferred_locale"] = locale_code
        return self._update_session(
            session=session,
            next_step=ONBOARDING_STEP_NAME_INPUT,
            next_status=ONBOARDING_STATUS_COLLECTING,
            draft=draft,
            event_type_code=ONBOARDING_EVENT_LOCALE_SELECTED,
            preferred_locale_code=locale_code,
            event_payload={"preferred_locale": locale_code},
        )

    def update_name(self, onboarding_session_id: str, name: str) -> OnboardingSession:
        session = self._require_by_id(onboarding_session_id)
        draft = _draft_from_json(session.draft_payload_json)
        draft["name"] = name
        return self._update_session(
            session=session,
            next_step=ONBOARDING_STEP_PHONE_INPUT,
            next_status=ONBOARDING_STATUS_COLLECTING,
            draft=draft,
            event_type_code=ONBOARDING_EVENT_NAME_COLLECTED,
            event_payload={"field": "name"},
        )

    def update_phone(
        self,
        onboarding_session_id: str,
        *,
        phone_raw: str,
        phone_normalized: str,
    ) -> OnboardingSession:
        session = self._require_by_id(onboarding_session_id)
        draft = _draft_from_json(session.draft_payload_json)
        draft["phone_raw"] = phone_raw
        draft["phone_normalized"] = phone_normalized
        return self._update_session(
            session=session,
            next_step=ONBOARDING_STEP_PROJECT_CONFIRM,
            next_status=ONBOARDING_STATUS_COLLECTING,
            draft=draft,
            event_type_code=ONBOARDING_EVENT_PHONE_COLLECTED,
            event_payload={"field": "phone"},
        )

    def move_to_step(self, onboarding_session_id: str, next_step: str) -> OnboardingSession:
        session = self._require_by_id(onboarding_session_id)
        return self._update_session(
            session=session,
            next_step=next_step,
            next_status=ONBOARDING_STATUS_COLLECTING,
            draft=_draft_from_json(session.draft_payload_json),
            event_type_code=ONBOARDING_EVENT_STEP_CHANGED,
            event_payload={"target_step": next_step},
        )

    def submit_pending_approval(self, onboarding_session_id: str) -> OnboardingSession:
        session = self._require_by_id(onboarding_session_id)
        submitted_at = utc_now_text()
        return self._update_session(
            session=session,
            next_step=ONBOARDING_STEP_PENDING_APPROVAL,
            next_status=ONBOARDING_STATUS_PENDING_APPROVAL,
            draft=_draft_from_json(session.draft_payload_json),
            event_type_code=ONBOARDING_EVENT_SUBMITTED,
            event_payload={"status": ONBOARDING_STATUS_PENDING_APPROVAL},
            submitted_at=submitted_at,
        )

    def _find_open_session(
        self,
        *,
        project_invitation_id: str,
        provider_user_id: str,
    ) -> OnboardingSession | None:
        placeholders = ", ".join("?" for _ in OPEN_ONBOARDING_STATUSES)
        row = self._connection.execute(
            f"""
            SELECT *
            FROM onboarding_sessions
            WHERE identity_provider_code = ?
              AND provider_user_id = ?
              AND project_invitation_id = ?
              AND session_status_code IN ({placeholders})
            ORDER BY last_interaction_at DESC, created_at DESC
            LIMIT 1
            """,
            (
                DEFAULT_IDENTITY_PROVIDER_CODE,
                provider_user_id,
                project_invitation_id,
                *OPEN_ONBOARDING_STATUSES,
            ),
        ).fetchone()
        if row is None:
            return None
        return row_to_onboarding_session(row)

    def _touch_session(self, onboarding_session_id: str, *, provider_handle: str | None) -> None:
        now = utc_now_text()
        self._connection.execute(
            """
            UPDATE onboarding_sessions
            SET provider_handle = COALESCE(?, provider_handle),
                last_interaction_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (provider_handle, now, now, onboarding_session_id),
        )
        self._connection.commit()

    def _require_by_id(self, onboarding_session_id: str) -> OnboardingSession:
        session = self.get_by_id(onboarding_session_id)
        if session is None:
            raise ValueError("온보딩 세션을 찾을 수 없습니다.")
        return session

    def _update_session(
        self,
        *,
        session: OnboardingSession,
        next_step: str,
        next_status: str,
        draft: dict,
        event_type_code: str,
        event_payload: dict,
        preferred_locale_code: str | None = None,
        submitted_at: str | None = None,
    ) -> OnboardingSession:
        with self._lock:
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE onboarding_sessions
                SET session_status_code = ?,
                    current_step_code = ?,
                    preferred_locale_code = COALESCE(?, preferred_locale_code),
                    draft_payload_json = ?,
                    last_interaction_at = ?,
                    submitted_at = COALESCE(?, submitted_at),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    next_status,
                    next_step,
                    preferred_locale_code,
                    json.dumps(draft, ensure_ascii=False, sort_keys=True),
                    now,
                    submitted_at,
                    now,
                    session.id,
                ),
            )
            self._insert_event(
                onboarding_session_id=session.id,
                event_type_code=event_type_code,
                from_step_code=session.current_step_code,
                to_step_code=next_step,
                from_status_code=session.session_status_code,
                to_status_code=next_status,
                payload=event_payload,
                occurred_at=now,
            )
            self._connection.commit()
            updated = self.get_by_id(session.id)
            if updated is None:
                raise RuntimeError("수정한 온보딩 세션을 다시 읽을 수 없습니다.")
            return updated

    def _insert_event(
        self,
        *,
        onboarding_session_id: str,
        event_type_code: str,
        from_step_code: str | None = None,
        to_step_code: str | None = None,
        from_status_code: str | None = None,
        to_status_code: str | None = None,
        payload: dict,
        occurred_at: str,
    ) -> None:
        event_id = f"onboarding_event_{uuid4().hex}"
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
                event_id,
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


def row_to_onboarding_session(row: sqlite3.Row) -> OnboardingSession:
    return OnboardingSession(**dict(row))


def _draft_from_json(payload_json: str) -> dict:
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload
