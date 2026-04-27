from PROJECT.admin.follow_up import DEFAULT_OUTBOX_MAX_RETRY_COUNT, FOLLOW_UP_CLOSED_NOTICE, FollowUpStatus, OutboxStatus
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.settings import SqliteSettings
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime, open_sqlite_connection


def bootstrap_runtime(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    return sqlite_runtime, SqliteAdminRuntime(sqlite_runtime.connection)


def test_sqlite_follow_up_runtime_creates_queue_item_and_messages(tmp_path):
    sqlite_runtime, runtime = bootstrap_runtime(tmp_path)

    try:
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            locale="ko",
            user_message="/support",
        )

        loaded = runtime.get_follow_up(follow_up.follow_up_id)
        assert loaded == follow_up
        assert loaded.status == FollowUpStatus.WAITING_ADMIN_REPLY
        assert loaded.user_messages == ("/support",)
        assert runtime.list_follow_ups() == [follow_up]
    finally:
        sqlite_runtime.close()


def test_sqlite_follow_up_runtime_can_filter_by_status(tmp_path):
    sqlite_runtime, runtime = bootstrap_runtime(tmp_path)

    try:
        waiting = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        opened = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=21,
            user_id=11,
            current_step="main_menu",
        )
        closed = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=22,
            user_id=12,
            current_step="main_menu",
        )
        runtime.create_admin_reply(opened.follow_up_id, "확인했습니다.")
        runtime.close_follow_up(closed.follow_up_id)

        assert [item.follow_up_id for item in runtime.list_follow_ups(status=FollowUpStatus.WAITING_ADMIN_REPLY)] == [
            waiting.follow_up_id,
        ]
        assert [item.follow_up_id for item in runtime.list_follow_ups(status=FollowUpStatus.OPEN)] == [
            opened.follow_up_id,
        ]
        assert [item.follow_up_id for item in runtime.list_follow_ups(status=FollowUpStatus.CLOSED)] == [
            closed.follow_up_id,
        ]
    finally:
        sqlite_runtime.close()


def test_sqlite_follow_up_runtime_can_search_by_query(tmp_path):
    sqlite_runtime, runtime = bootstrap_runtime(tmp_path)

    try:
        runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="사진 업로드 문의",
        )
        matched = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=55,
            user_id=987654321,
            current_step="yield_confirm",
            user_message="수확량 값을 다시 확인해주세요",
        )

        by_message = runtime.list_follow_ups(query="수확량 값")
        by_user = runtime.list_follow_ups(query="987654321")

        assert [item.follow_up_id for item in by_message] == [matched.follow_up_id]
        assert [item.follow_up_id for item in by_user] == [matched.follow_up_id]
    finally:
        sqlite_runtime.close()


def test_sqlite_follow_up_runtime_survives_restart(tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(database_path),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        created = SqliteAdminRuntime(sqlite_runtime.connection).create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="/support",
        )
    finally:
        sqlite_runtime.close()

    reopened = open_sqlite_connection(SqliteSettings(database_path=str(database_path)))
    try:
        runtime = SqliteAdminRuntime(reopened)
        loaded = runtime.get_follow_up(created.follow_up_id)

        assert loaded is not None
        assert loaded.follow_up_id == created.follow_up_id
        assert loaded.user_messages == ("/support",)
    finally:
        reopened.close()


def test_sqlite_follow_up_runtime_persists_user_and_admin_messages_with_outbox(tmp_path):
    sqlite_runtime, runtime = bootstrap_runtime(tmp_path)

    try:
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="/support",
        )

        updated = runtime.append_user_message(follow_up.follow_up_id, "추가 문의입니다.")
        result = runtime.create_admin_reply(follow_up.follow_up_id, "확인했습니다.")

        assert updated is not None
        assert updated.user_messages == ("/support", "추가 문의입니다.")
        assert result is not None
        replied, outbox = result
        assert replied.status == FollowUpStatus.OPEN
        assert replied.admin_messages == ("확인했습니다.",)
        assert outbox.status == OutboxStatus.PENDING
        assert outbox.text == "확인했습니다."
        assert runtime.list_outbox(status=OutboxStatus.PENDING) == [outbox]
    finally:
        sqlite_runtime.close()


def test_sqlite_follow_up_runtime_close_can_write_notice_outbox(tmp_path):
    sqlite_runtime, runtime = bootstrap_runtime(tmp_path)

    try:
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )

        closed = runtime.close_follow_up(follow_up.follow_up_id, notify_user=True)
        duplicate = runtime.close_follow_up(follow_up.follow_up_id, notify_user=True)
        outbox = runtime.list_outbox(status=OutboxStatus.PENDING)

        assert closed is not None
        assert duplicate == closed
        assert closed.status == FollowUpStatus.CLOSED
        assert len(outbox) == 1
        assert outbox[0].text == FOLLOW_UP_CLOSED_NOTICE
    finally:
        sqlite_runtime.close()


def test_sqlite_manual_review_outbox_can_be_requeued_for_bot_delivery(tmp_path):
    sqlite_runtime, runtime = bootstrap_runtime(tmp_path)

    try:
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "확인했습니다.")
        for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
            runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")

        requeued = runtime.requeue_manual_review_outbox(outbox_message.outbox_id)
        claimed = runtime.claim_pending_outbox(limit=1)

        assert requeued is not None
        assert requeued.status == OutboxStatus.PENDING
        assert requeued.retry_count == 0
        assert requeued.error_message is None
        assert claimed[0].outbox_id == outbox_message.outbox_id
        assert claimed[0].status == OutboxStatus.SENDING
    finally:
        sqlite_runtime.close()
