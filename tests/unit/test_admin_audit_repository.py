from PROJECT.settings import SqliteSettings
from PROJECT.storage.admin_audit import RESULT_FAILURE, RESULT_SUCCESS, SqliteAdminAuditRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def test_admin_audit_repository_records_and_lists_events(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None

    try:
        repository = SqliteAdminAuditRepository(runtime.connection)

        created = repository.record_event(
            action_code="admin.follow_up.reply",
            actor_id="admin_local_default",
            target_type_code="admin_follow_up_queue",
            target_id="followup_123",
            result_code=RESULT_SUCCESS,
            source_code="admin.api.reply",
            request_path="/admin/follow-ups/followup_123/reply",
            detail={"close_after_send": False},
        )

        events = repository.list_events()

        assert events == [created]
        assert events[0].detail == {"close_after_send": False}
        assert events[0].request_path == "/admin/follow-ups/followup_123/reply"
    finally:
        runtime.close()


def test_admin_audit_repository_keeps_sensitive_detail_out_of_schema_contract(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None

    try:
        repository = SqliteAdminAuditRepository(runtime.connection)

        repository.record_event(
            action_code="admin.login",
            actor_type_code="unknown",
            actor_id=None,
            result_code=RESULT_FAILURE,
            source_code="admin.web.login",
            request_path="/admin/login",
            detail={"attempt": 1},
        )

        event = repository.list_events()[0]

        assert event.action_code == "admin.login"
        assert event.actor_type_code == "unknown"
        assert event.actor_id is None
        assert event.detail == {"attempt": 1}
    finally:
        runtime.close()
