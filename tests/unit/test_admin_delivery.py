import asyncio
from datetime import UTC, datetime, timedelta

from PROJECT.admin.delivery import deliver_pending_outbox
from PROJECT.admin.follow_up import (
    DEFAULT_OUTBOX_MAX_RETRY_COUNT,
    DEFAULT_OUTBOX_RETRY_BACKOFF_SECONDS,
    InMemoryAdminRuntime,
    OutboxStatus,
)
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.settings import SqliteSettings
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime, open_sqlite_connection


class FakeBot:
    def __init__(self, *, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str):
        if self.should_fail:
            raise RuntimeError("transport down")
        self.sent_messages.append((chat_id, text))


def _runtime_with_pending_outbox() -> tuple[InMemoryAdminRuntime, str]:
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "사진을 다시 보내주세요.")
    return runtime, outbox_message.outbox_id


def test_deliver_pending_outbox_sends_message_and_marks_sent():
    runtime, outbox_id = _runtime_with_pending_outbox()
    bot = FakeBot()

    delivered = asyncio.run(deliver_pending_outbox(bot, runtime=runtime))

    assert delivered == 1
    assert bot.sent_messages == [(20, "사진을 다시 보내주세요.")]
    assert runtime.list_outbox()[0].outbox_id == outbox_id
    assert runtime.list_outbox()[0].status == OutboxStatus.SENT


def test_deliver_pending_outbox_marks_failed_when_send_fails():
    runtime, outbox_id = _runtime_with_pending_outbox()
    bot = FakeBot(should_fail=True)

    delivered = asyncio.run(deliver_pending_outbox(bot, runtime=runtime))

    assert delivered == 0
    assert runtime.list_outbox()[0].outbox_id == outbox_id
    assert runtime.list_outbox()[0].status == OutboxStatus.FAILED
    assert runtime.list_outbox()[0].retry_count == 1


def test_deliver_pending_outbox_moves_to_manual_review_after_retry_limit():
    runtime, outbox_id = _runtime_with_pending_outbox()

    for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
        runtime.claim_pending_outbox(limit=1)
        failed = runtime.mark_outbox_failed(outbox_id, "transport down")

    delivered = asyncio.run(deliver_pending_outbox(FakeBot(), runtime=runtime))

    assert delivered == 0
    assert failed is not None
    assert failed.status == OutboxStatus.MANUAL_REVIEW
    assert failed.retry_count == DEFAULT_OUTBOX_MAX_RETRY_COUNT


def test_deliver_pending_outbox_does_not_immediately_retry_failed_message():
    runtime, outbox_id = _runtime_with_pending_outbox()

    first = asyncio.run(deliver_pending_outbox(FakeBot(should_fail=True), runtime=runtime))
    second = asyncio.run(deliver_pending_outbox(FakeBot(), runtime=runtime))

    assert first == 0
    assert second == 0
    assert runtime.list_outbox()[0].outbox_id == outbox_id
    assert runtime.list_outbox()[0].status == OutboxStatus.FAILED


def test_deliver_pending_outbox_marks_sqlite_message_sent(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = SqliteAdminRuntime(sqlite_runtime.connection)
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "사진을 다시 보내주세요.")

        delivered = asyncio.run(deliver_pending_outbox(FakeBot(), runtime=runtime))

        assert delivered == 1
        assert runtime.list_outbox()[0].outbox_id == outbox_message.outbox_id
        assert runtime.list_outbox()[0].status == OutboxStatus.SENT
    finally:
        sqlite_runtime.close()

    reopened = open_sqlite_connection(SqliteSettings(database_path=str(tmp_path / "runtime.sqlite3")))
    try:
        loaded = SqliteAdminRuntime(reopened).list_outbox()[0]
        assert loaded.outbox_id == outbox_message.outbox_id
        assert loaded.status == OutboxStatus.SENT
    finally:
        reopened.close()


def test_deliver_pending_outbox_marks_sqlite_message_failed(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = SqliteAdminRuntime(sqlite_runtime.connection)
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "사진을 다시 보내주세요.")

        delivered = asyncio.run(deliver_pending_outbox(FakeBot(should_fail=True), runtime=runtime))

        assert delivered == 0
        assert runtime.list_outbox()[0].outbox_id == outbox_message.outbox_id
        assert runtime.list_outbox()[0].status == OutboxStatus.FAILED
        assert runtime.list_outbox()[0].error_message == "transport down"
        assert runtime.list_outbox()[0].retry_count == 1
    finally:
        sqlite_runtime.close()


def test_deliver_pending_outbox_moves_sqlite_message_to_manual_review_after_retry_limit(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = SqliteAdminRuntime(sqlite_runtime.connection)
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "사진을 다시 보내주세요.")

        for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
            runtime.claim_pending_outbox(limit=1)
            failed = runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")

        delivered = asyncio.run(deliver_pending_outbox(FakeBot(), runtime=runtime))
        loaded = runtime.list_outbox()[0]

        assert delivered == 0
        assert failed is not None
        assert failed.status == OutboxStatus.MANUAL_REVIEW
        assert loaded.status == OutboxStatus.MANUAL_REVIEW
        assert loaded.retry_count == DEFAULT_OUTBOX_MAX_RETRY_COUNT
    finally:
        sqlite_runtime.close()


def test_deliver_pending_outbox_retries_sqlite_failed_message_after_backoff(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = SqliteAdminRuntime(sqlite_runtime.connection)
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "사진을 다시 보내주세요.")

        failed = asyncio.run(deliver_pending_outbox(FakeBot(should_fail=True), runtime=runtime))
        immediate_retry = asyncio.run(deliver_pending_outbox(FakeBot(), runtime=runtime))
        old_timestamp = (datetime.now(UTC) - timedelta(seconds=DEFAULT_OUTBOX_RETRY_BACKOFF_SECONDS + 1)).isoformat()
        sqlite_runtime.connection.execute(
            "UPDATE outbox_messages SET updated_at = ?, failed_at = ? WHERE id = ?",
            (old_timestamp, old_timestamp, outbox_message.outbox_id),
        )
        sqlite_runtime.connection.commit()
        bot = FakeBot()
        retried = asyncio.run(deliver_pending_outbox(bot, runtime=runtime))

        assert failed == 0
        assert immediate_retry == 0
        assert retried == 1
        assert bot.sent_messages == [(20, "사진을 다시 보내주세요.")]
        assert runtime.list_outbox()[0].status == OutboxStatus.SENT
        assert runtime.list_outbox()[0].retry_count == 1
    finally:
        sqlite_runtime.close()
