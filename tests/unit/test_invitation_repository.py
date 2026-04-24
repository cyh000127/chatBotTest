import re
import sqlite3

import pytest

from PROJECT.settings import SqliteSettings
from PROJECT.storage.invitations import (
    DEFAULT_LOCAL_ADMIN_USER_ID,
    DEFAULT_LOCAL_PROJECT_ID,
    INVITATION_STATUS_ISSUED,
    SqliteInvitationRepository,
    generate_invite_code,
)
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime, open_sqlite_connection


def bootstrap_repository(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    return runtime, SqliteInvitationRepository(runtime.connection)


def test_generate_invite_code_uses_human_operable_shape():
    assert re.fullmatch(r"INV-[A-Z2-9]{8}", generate_invite_code())


def test_invitation_repository_creates_and_lists_invitation(tmp_path):
    runtime, repository = bootstrap_repository(tmp_path)

    try:
        invitation = repository.create_invitation()

        assert invitation.id.startswith("invite_")
        assert invitation.project_id == DEFAULT_LOCAL_PROJECT_ID
        assert invitation.invited_by_admin_user_id == DEFAULT_LOCAL_ADMIN_USER_ID
        assert invitation.invite_status_code == INVITATION_STATUS_ISSUED
        assert invitation.target_participant_role_code == "farmer"
        assert invitation.start_command == f"/start {invitation.invite_code}"
        assert repository.get_by_code(invitation.invite_code) == invitation
        assert repository.list_invitations() == (invitation,)
        assert repository.list_invitations(status=INVITATION_STATUS_ISSUED) == (invitation,)
        assert repository.list_invitations(status="used") == ()
    finally:
        runtime.close()


def test_invitation_repository_persists_invitation_after_reopen(tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    settings = SqliteSettings(database_path=str(database_path), migrations_enabled=True)
    first_runtime = bootstrap_sqlite_runtime(settings)
    assert first_runtime is not None
    try:
        created = SqliteInvitationRepository(first_runtime.connection).create_invitation(
            target_contact_type_code="phone",
            target_contact_normalized="+85500000000",
            target_contact_raw="+855 00 000 000",
        )
    finally:
        first_runtime.close()

    second_connection = open_sqlite_connection(SqliteSettings(database_path=str(database_path)))
    try:
        repository = SqliteInvitationRepository(second_connection)
        loaded = repository.get_by_code(created.invite_code)

        assert loaded == created
        assert loaded.target_contact_type_code == "phone"
        assert loaded.target_contact_normalized == "+85500000000"
        assert loaded.target_contact_raw == "+855 00 000 000"
    finally:
        second_connection.close()


def test_invitation_repository_rejects_unknown_project(tmp_path):
    runtime, repository = bootstrap_repository(tmp_path)

    try:
        with pytest.raises(sqlite3.IntegrityError):
            repository.create_invitation(project_id="missing_project")
    finally:
        runtime.close()
