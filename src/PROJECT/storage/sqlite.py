from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import re

from PROJECT.settings import SqliteSettings

DEFAULT_MIGRATIONS_PATH = Path(__file__).with_name("migrations")
MIGRATION_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class SqliteMigration:
    version: str
    path: Path
    sql: str


@dataclass
class SqliteRuntime:
    settings: SqliteSettings
    connection: sqlite3.Connection
    applied_migrations: tuple[str, ...] = ()

    def close(self) -> None:
        self.connection.close()


def open_sqlite_connection(settings: SqliteSettings) -> sqlite3.Connection:
    if not settings.enabled:
        raise ValueError("SQLite 설정이 비활성화되어 있습니다.")

    database_path = Path(settings.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {settings.busy_timeout_ms}")
    return connection


def bootstrap_sqlite_runtime(
    settings: SqliteSettings,
    *,
    migrations_path: Path = DEFAULT_MIGRATIONS_PATH,
) -> SqliteRuntime | None:
    if not settings.enabled:
        return None
    connection = open_sqlite_connection(settings)
    try:
        applied_migrations = ()
        if settings.migrations_enabled:
            applied_migrations = apply_pending_migrations(connection, migrations_path=migrations_path)
        return SqliteRuntime(
            settings=settings,
            connection=connection,
            applied_migrations=applied_migrations,
        )
    except Exception:
        connection.close()
        raise


def read_sqlite_pragma(connection: sqlite3.Connection, name: str) -> int:
    row = connection.execute(f"PRAGMA {name}").fetchone()
    if row is None:
        raise RuntimeError(f"SQLite PRAGMA 값을 읽을 수 없습니다: {name}")
    return int(row[0])


def ensure_schema_migrations_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version TEXT PRIMARY KEY,
          applied_at TEXT NOT NULL
        )
        """
    )
    connection.commit()


def load_sql_migrations(migrations_path: Path = DEFAULT_MIGRATIONS_PATH) -> tuple[SqliteMigration, ...]:
    if not migrations_path.exists():
        return ()
    if not migrations_path.is_dir():
        raise ValueError(f"SQLite migration 경로가 디렉터리가 아닙니다: {migrations_path}")

    migrations: list[SqliteMigration] = []
    seen_versions: set[str] = set()
    for path in sorted(migrations_path.glob("*.sql")):
        version = path.stem
        if not MIGRATION_VERSION_PATTERN.fullmatch(version):
            raise ValueError(f"잘못된 SQLite migration 버전명입니다: {version}")
        if version in seen_versions:
            raise ValueError(f"중복 SQLite migration 버전입니다: {version}")
        sql = path.read_text(encoding="utf-8").strip()
        if not sql:
            raise ValueError(f"비어 있는 SQLite migration 입니다: {path}")
        migrations.append(SqliteMigration(version=version, path=path, sql=sql))
        seen_versions.add(version)
    return tuple(migrations)


def read_applied_migration_versions(connection: sqlite3.Connection) -> set[str]:
    ensure_schema_migrations_table(connection)
    rows = connection.execute("SELECT version FROM schema_migrations").fetchall()
    return {str(row["version"]) for row in rows}


def apply_pending_migrations(
    connection: sqlite3.Connection,
    *,
    migrations_path: Path = DEFAULT_MIGRATIONS_PATH,
) -> tuple[str, ...]:
    ensure_schema_migrations_table(connection)
    applied_versions = read_applied_migration_versions(connection)
    newly_applied: list[str] = []

    for migration in load_sql_migrations(migrations_path):
        if migration.version in applied_versions:
            continue
        apply_single_migration(connection, migration)
        applied_versions.add(migration.version)
        newly_applied.append(migration.version)

    return tuple(newly_applied)


def apply_single_migration(connection: sqlite3.Connection, migration: SqliteMigration) -> None:
    sql = migration.sql
    if not sql.endswith(";"):
        sql = f"{sql};"
    applied_at = datetime.now(UTC).isoformat()
    script = "\n".join(
        (
            "BEGIN;",
            sql,
            "INSERT INTO schema_migrations (version, applied_at) VALUES "
            f"({_quote_sql_literal(migration.version)}, {_quote_sql_literal(applied_at)});",
            "COMMIT;",
        )
    )
    try:
        connection.executescript(script)
    except Exception:
        connection.rollback()
        raise


def _quote_sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
