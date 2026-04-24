import pytest

from PROJECT.settings import SqliteSettings
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime, open_sqlite_connection, read_sqlite_pragma


def test_bootstrap_sqlite_runtime_returns_none_when_disabled():
    assert bootstrap_sqlite_runtime(SqliteSettings()) is None


def test_open_sqlite_connection_rejects_disabled_settings():
    with pytest.raises(ValueError):
        open_sqlite_connection(SqliteSettings())


def test_open_sqlite_connection_creates_parent_and_sets_pragmas(tmp_path):
    database_path = tmp_path / "state" / "runtime.sqlite3"
    connection = open_sqlite_connection(
        SqliteSettings(
            database_path=str(database_path),
            busy_timeout_ms=1234,
        )
    )

    try:
        assert database_path.exists()
        assert read_sqlite_pragma(connection, "foreign_keys") == 1
        assert read_sqlite_pragma(connection, "busy_timeout") == 1234
        row = connection.execute("SELECT 1 AS value").fetchone()
        assert row["value"] == 1
    finally:
        connection.close()


def test_bootstrap_sqlite_runtime_wraps_connection(tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    settings = SqliteSettings(database_path=str(database_path), migrations_enabled=True)
    runtime = bootstrap_sqlite_runtime(settings)

    assert runtime is not None
    try:
        assert runtime.settings == settings
        assert read_sqlite_pragma(runtime.connection, "foreign_keys") == 1
    finally:
        runtime.close()
