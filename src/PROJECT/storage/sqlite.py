from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from PROJECT.settings import SqliteSettings


@dataclass
class SqliteRuntime:
    settings: SqliteSettings
    connection: sqlite3.Connection

    def close(self) -> None:
        self.connection.close()


def open_sqlite_connection(settings: SqliteSettings) -> sqlite3.Connection:
    if not settings.enabled:
        raise ValueError("SQLite 설정이 비활성화되어 있습니다.")

    database_path = Path(settings.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {settings.busy_timeout_ms}")
    return connection


def bootstrap_sqlite_runtime(settings: SqliteSettings) -> SqliteRuntime | None:
    if not settings.enabled:
        return None
    return SqliteRuntime(settings=settings, connection=open_sqlite_connection(settings))


def read_sqlite_pragma(connection: sqlite3.Connection, name: str) -> int:
    row = connection.execute(f"PRAGMA {name}").fetchone()
    if row is None:
        raise RuntimeError(f"SQLite PRAGMA 값을 읽을 수 없습니다: {name}")
    return int(row[0])
