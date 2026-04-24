from PROJECT.admin.follow_up import InMemoryAdminRuntime
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.admin_api.server import admin_runtime_for_storage
from PROJECT.settings import SqliteSettings
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def test_admin_runtime_for_storage_keeps_in_memory_runtime_without_sqlite():
    runtime = InMemoryAdminRuntime()

    selected = admin_runtime_for_storage(runtime, None)

    assert selected is runtime


def test_admin_runtime_for_storage_uses_sqlite_runtime_when_available(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None

    try:
        selected = admin_runtime_for_storage(InMemoryAdminRuntime(), sqlite_runtime)

        assert isinstance(selected, SqliteAdminRuntime)
        follow_up = selected.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="/support",
        )
        assert selected.get_follow_up(follow_up.follow_up_id).user_messages == ("/support",)
    finally:
        sqlite_runtime.close()
