import sqlite3

import pytest

from PROJECT.settings import SqliteSettings
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime, read_applied_migration_versions


REQUIRED_TABLES = {
    "schema_migrations",
    "admin_users",
    "projects",
    "project_invitations",
    "participants",
    "participant_private_contacts",
    "participant_identities",
    "onboarding_sessions",
    "onboarding_session_events",
    "project_enrollments",
    "channel_messages",
    "message_deliveries",
    "admin_follow_up_queue",
    "admin_follow_up_messages",
    "admin_follow_up_outcomes",
    "outbox_messages",
}

DEFERRED_TABLES = {
    "ai_follow_up_attempts",
    "participant_identity_link_reviews",
    "participant_reachability_states",
    "reminder_deliveries",
    "escalations",
}

REQUIRED_INDEXES = {
    "idx_project_invitations_code_status",
    "idx_onboarding_identity_status",
    "idx_admin_follow_up_status_created",
    "idx_outbox_state_created",
    "idx_channel_messages_chat_time",
    "idx_follow_up_messages_queue_time",
    "idx_project_enrollments_participant_status",
    "idx_participant_identities_provider_user",
}


def table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def index_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'").fetchall()
    return {str(row["name"]) for row in rows}


def column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def bootstrap_schema(tmp_path):
    return bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )


def test_initial_schema_migration_creates_required_tables_and_indexes(tmp_path):
    runtime = bootstrap_schema(tmp_path)

    assert runtime is not None
    try:
        assert runtime.applied_migrations == ("001_initial_schema",)
        existing_tables = table_names(runtime.connection)
        existing_indexes = index_names(runtime.connection)
        assert REQUIRED_TABLES <= existing_tables
        assert DEFERRED_TABLES.isdisjoint(existing_tables)
        assert REQUIRED_INDEXES <= existing_indexes
        assert read_applied_migration_versions(runtime.connection) == {"001_initial_schema"}
    finally:
        runtime.close()


def test_initial_schema_contains_reference_alignment_columns(tmp_path):
    runtime = bootstrap_schema(tmp_path)

    assert runtime is not None
    try:
        assert {
            "invite_code",
            "invite_token_hash",
            "accepted_participant_id",
            "accepted_enrollment_id",
            "used_channel_message_id",
        } <= column_names(runtime.connection, "project_invitations")
        assert {"participant_identity_id", "project_id"} <= column_names(runtime.connection, "channel_messages")
        assert {
            "field_id",
            "field_season_id",
            "seasonal_event_id",
            "evidence_request_event_id",
            "input_resolution_session_id",
        } <= column_names(runtime.connection, "admin_follow_up_queue")
    finally:
        runtime.close()


def test_initial_schema_seeds_local_admin_and_project_once(tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    settings = SqliteSettings(database_path=str(database_path), migrations_enabled=True)
    first_runtime = bootstrap_sqlite_runtime(settings)

    assert first_runtime is not None
    first_runtime.close()

    second_runtime = bootstrap_sqlite_runtime(settings)

    assert second_runtime is not None
    try:
        assert second_runtime.applied_migrations == ()
        admin_count = second_runtime.connection.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]
        project_count = second_runtime.connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        assert admin_count == 1
        assert project_count == 1
        admin = second_runtime.connection.execute("SELECT username FROM admin_users").fetchone()
        project = second_runtime.connection.execute("SELECT project_status_code FROM projects").fetchone()
        assert admin["username"] == "local-admin"
        assert project["project_status_code"] == "active"
    finally:
        second_runtime.close()


def test_initial_schema_enforces_foreign_keys(tmp_path):
    runtime = bootstrap_schema(tmp_path)

    assert runtime is not None
    try:
        with pytest.raises(sqlite3.IntegrityError):
            runtime.connection.execute(
                """
                INSERT INTO participant_private_contacts (
                  id,
                  participant_id,
                  contact_type_code,
                  normalized_value,
                  raw_value,
                  created_at,
                  updated_at
                )
                VALUES (
                  'contact_missing',
                  'missing_participant',
                  'phone',
                  '+85500000000',
                  '+85500000000',
                  '1970-01-01T00:00:00+00:00',
                  '1970-01-01T00:00:00+00:00'
                )
                """
            )
    finally:
        runtime.close()
