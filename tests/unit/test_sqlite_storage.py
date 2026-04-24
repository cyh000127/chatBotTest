import pytest

from PROJECT.settings import SqliteSettings
from PROJECT.storage.sqlite import (
    apply_pending_migrations,
    bootstrap_sqlite_runtime,
    load_sql_migrations,
    open_sqlite_connection,
    read_applied_migration_versions,
    read_sqlite_pragma,
)


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


def test_load_sql_migrations_returns_sorted_migrations(tmp_path):
    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()
    (migrations_path / "002_second.sql").write_text("CREATE TABLE second_item (id INTEGER);", encoding="utf-8")
    (migrations_path / "001_first.sql").write_text("CREATE TABLE first_item (id INTEGER);", encoding="utf-8")

    migrations = load_sql_migrations(migrations_path)

    assert [migration.version for migration in migrations] == ["001_first", "002_second"]


def test_load_sql_migrations_rejects_invalid_inputs(tmp_path):
    missing_path = tmp_path / "missing"
    assert load_sql_migrations(missing_path) == ()

    file_path = tmp_path / "not_a_directory.sql"
    file_path.write_text("SELECT 1;", encoding="utf-8")
    with pytest.raises(ValueError):
        load_sql_migrations(file_path)

    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()
    (migrations_path / "_bad.sql").write_text("SELECT 1;", encoding="utf-8")
    with pytest.raises(ValueError):
        load_sql_migrations(migrations_path)

    (migrations_path / "_bad.sql").unlink()
    (migrations_path / "001_empty.sql").write_text(" ", encoding="utf-8")
    with pytest.raises(ValueError):
        load_sql_migrations(migrations_path)


def test_apply_pending_migrations_applies_once_and_records_versions(tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()
    (migrations_path / "001_create_items.sql").write_text(
        "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL);",
        encoding="utf-8",
    )
    (migrations_path / "002_insert_items.sql").write_text(
        "INSERT INTO items (name) VALUES ('seed');",
        encoding="utf-8",
    )
    connection = open_sqlite_connection(SqliteSettings(database_path=str(database_path)))

    try:
        assert apply_pending_migrations(connection, migrations_path=migrations_path) == (
            "001_create_items",
            "002_insert_items",
        )
        assert read_applied_migration_versions(connection) == {"001_create_items", "002_insert_items"}
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 1

        assert apply_pending_migrations(connection, migrations_path=migrations_path) == ()
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 1
    finally:
        connection.close()


def test_apply_pending_migrations_rolls_back_failed_migration(tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()
    (migrations_path / "001_broken.sql").write_text(
        """
        CREATE TABLE should_rollback (id INTEGER);
        INSERT INTO missing_table (id) VALUES (1);
        """,
        encoding="utf-8",
    )
    connection = open_sqlite_connection(SqliteSettings(database_path=str(database_path)))

    try:
        with pytest.raises(Exception):
            apply_pending_migrations(connection, migrations_path=migrations_path)

        assert "001_broken" not in read_applied_migration_versions(connection)
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'should_rollback'"
        ).fetchone()
        assert table is None
    finally:
        connection.close()


def test_bootstrap_sqlite_runtime_applies_migrations_when_enabled(tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    migrations_path = tmp_path / "migrations"
    migrations_path.mkdir()
    (migrations_path / "001_create_items.sql").write_text(
        "CREATE TABLE items (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    settings = SqliteSettings(
        database_path=str(database_path),
        migrations_enabled=True,
    )

    runtime = bootstrap_sqlite_runtime(settings, migrations_path=migrations_path)

    assert runtime is not None
    try:
        assert runtime.applied_migrations == ("001_create_items",)
        assert runtime.connection.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0
    finally:
        runtime.close()
