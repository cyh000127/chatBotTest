from __future__ import annotations

import secrets
import sqlite3
import string
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4


DEFAULT_LOCAL_ADMIN_USER_ID = "admin_local_default"
DEFAULT_LOCAL_PROJECT_ID = "project_local_default"
DEFAULT_INVITATION_CHANNEL = "telegram"
DEFAULT_INVITATION_ROLE = "farmer"
INVITATION_STATUS_ISSUED = "issued"
INVITATION_STATUS_REVOKED = "revoked"
INVITATION_STATUS_USED = "used"
INVITE_CODE_PREFIX = "INV"
INVITE_CODE_ALPHABET = "".join(ch for ch in string.ascii_uppercase + string.digits if ch not in {"0", "O", "1", "I"})


@dataclass(frozen=True)
class AdminInvitation:
    id: str
    project_id: str
    channel_code: str
    invite_code: str
    invite_token_hash: str | None
    invite_status_code: str
    target_contact_type_code: str | None
    target_contact_normalized: str | None
    target_contact_raw: str | None
    target_participant_role_code: str
    invited_by_admin_user_id: str | None
    issued_at: str
    expires_at: str | None
    used_at: str | None
    revoked_at: str | None
    accepted_participant_id: str | None
    accepted_enrollment_id: str | None
    used_channel_message_id: str | None
    created_at: str
    updated_at: str

    @property
    def start_command(self) -> str:
        return f"/start {self.invite_code}"


class InvitationRepositoryUnavailable(RuntimeError):
    pass


class SqliteInvitationRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = RLock()

    def create_invitation(
        self,
        *,
        project_id: str = DEFAULT_LOCAL_PROJECT_ID,
        invited_by_admin_user_id: str = DEFAULT_LOCAL_ADMIN_USER_ID,
        channel_code: str = DEFAULT_INVITATION_CHANNEL,
        target_contact_type_code: str | None = None,
        target_contact_normalized: str | None = None,
        target_contact_raw: str | None = None,
        target_participant_role_code: str = DEFAULT_INVITATION_ROLE,
        expires_at: str | None = None,
    ) -> AdminInvitation:
        with self._lock:
            for _ in range(10):
                try:
                    return self._insert_invitation(
                        project_id=project_id,
                        invited_by_admin_user_id=invited_by_admin_user_id,
                        channel_code=channel_code,
                        invite_code=generate_invite_code(),
                        target_contact_type_code=target_contact_type_code,
                        target_contact_normalized=target_contact_normalized,
                        target_contact_raw=target_contact_raw,
                        target_participant_role_code=target_participant_role_code,
                        expires_at=expires_at,
                    )
                except sqlite3.IntegrityError as exc:
                    if "UNIQUE" not in str(exc).upper():
                        raise
            raise RuntimeError("고유한 초대 코드를 생성하지 못했습니다.")

    def list_invitations(self, *, status: str | None = None) -> tuple[AdminInvitation, ...]:
        with self._lock:
            if status:
                rows = self._connection.execute(
                    """
                    SELECT *
                    FROM project_invitations
                    WHERE invite_status_code = ?
                    ORDER BY issued_at DESC, created_at DESC
                    """,
                    (status,),
                ).fetchall()
            else:
                rows = self._connection.execute(
                    """
                    SELECT *
                    FROM project_invitations
                    ORDER BY issued_at DESC, created_at DESC
                    """
                ).fetchall()
            return tuple(row_to_invitation(row) for row in rows)

    def get_by_code(self, invite_code: str) -> AdminInvitation | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM project_invitations WHERE invite_code = ?",
                (invite_code,),
            ).fetchone()
            if row is None:
                return None
            return row_to_invitation(row)

    def get_by_id(self, invitation_id: str) -> AdminInvitation | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM project_invitations WHERE id = ?",
                (invitation_id,),
            ).fetchone()
            if row is None:
                return None
            return row_to_invitation(row)

    def revoke_invitation(self, invitation_id: str) -> AdminInvitation | None:
        with self._lock:
            invitation = self.get_by_id(invitation_id)
            if invitation is None:
                return None
            if invitation.invite_status_code == INVITATION_STATUS_REVOKED:
                return invitation
            if invitation.invite_status_code != INVITATION_STATUS_ISSUED:
                return None
            now = utc_now_text()
            self._connection.execute(
                """
                UPDATE project_invitations
                SET invite_status_code = ?,
                    revoked_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    INVITATION_STATUS_REVOKED,
                    now,
                    now,
                    invitation_id,
                ),
            )
            self._connection.commit()
            revoked = self.get_by_id(invitation_id)
            if revoked is None:
                raise RuntimeError("회수한 초대 코드를 다시 읽을 수 없습니다.")
            return revoked

    def _insert_invitation(
        self,
        *,
        project_id: str,
        invited_by_admin_user_id: str,
        channel_code: str,
        invite_code: str,
        target_contact_type_code: str | None,
        target_contact_normalized: str | None,
        target_contact_raw: str | None,
        target_participant_role_code: str,
        expires_at: str | None,
    ) -> AdminInvitation:
        now = utc_now_text()
        invitation_id = f"invite_{uuid4().hex}"
        self._connection.execute(
            """
            INSERT INTO project_invitations (
              id,
              project_id,
              channel_code,
              invite_code,
              invite_token_hash,
              invite_status_code,
              target_contact_type_code,
              target_contact_normalized,
              target_contact_raw,
              target_participant_role_code,
              invited_by_admin_user_id,
              issued_at,
              expires_at,
              created_at,
              updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invitation_id,
                project_id,
                channel_code,
                invite_code,
                None,
                INVITATION_STATUS_ISSUED,
                target_contact_type_code,
                target_contact_normalized,
                target_contact_raw,
                target_participant_role_code,
                invited_by_admin_user_id,
                now,
                expires_at,
                now,
                now,
            ),
        )
        self._connection.commit()
        created = self.get_by_code(invite_code)
        if created is None:
            raise RuntimeError("생성한 초대 코드를 다시 읽을 수 없습니다.")
        return created


def generate_invite_code(length: int = 8) -> str:
    suffix = "".join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(length))
    return f"{INVITE_CODE_PREFIX}-{suffix}"


def row_to_invitation(row: sqlite3.Row) -> AdminInvitation:
    payload = dict(row)
    return AdminInvitation(**payload)


def utc_now_text() -> str:
    return datetime.now(UTC).isoformat()
