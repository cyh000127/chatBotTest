from PROJECT.admin.follow_up import (
    DEFAULT_OUTBOX_MAX_RETRY_COUNT,
    FOLLOW_UP_CLOSED_NOTICE,
    FollowUpStatus,
    InMemoryAdminRuntime,
    OutboxStatus,
)


def test_create_follow_up_records_command_request_and_queue_item():
    runtime = InMemoryAdminRuntime()

    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        locale="ko",
        user_message="/support",
    )

    assert follow_up.status == FollowUpStatus.WAITING_ADMIN_REPLY
    assert follow_up.chat_id == 20
    assert follow_up.user_messages == ("/support",)
    assert runtime.get_follow_up(follow_up.follow_up_id) == follow_up
    assert len(runtime.list_command_requests()) == 1


def test_admin_reply_creates_pending_outbox_message():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="/support",
    )

    result = runtime.create_admin_reply(follow_up.follow_up_id, "사진을 다시 보내주세요.")

    assert result is not None
    updated, outbox_message = result
    assert updated.status == FollowUpStatus.OPEN
    assert updated.awaiting_admin_reply is False
    assert updated.admin_reply_count == 1
    assert outbox_message.status == OutboxStatus.PENDING
    assert outbox_message.chat_id == 20
    assert runtime.list_outbox(status=OutboxStatus.PENDING) == [outbox_message]


def test_outbox_claim_and_delivery_status_transitions():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "확인했습니다.")

    claimed = runtime.claim_pending_outbox(limit=1)

    assert len(claimed) == 1
    assert claimed[0].status == OutboxStatus.SENDING
    assert runtime.mark_outbox_sent(outbox_message.outbox_id).status == OutboxStatus.SENT


def test_outbox_moves_to_manual_review_after_retry_limit():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "확인했습니다.")

    for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
        failed = runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")

    assert failed is not None
    assert failed.status == OutboxStatus.MANUAL_REVIEW
    assert failed.retry_count == DEFAULT_OUTBOX_MAX_RETRY_COUNT
    assert runtime.claim_pending_outbox() == []


def test_manual_review_outbox_can_be_requeued_for_bot_delivery():
    runtime = InMemoryAdminRuntime()
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


def test_closed_follow_up_does_not_accept_more_messages_or_admin_replies():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )

    closed = runtime.close_follow_up(follow_up.follow_up_id)

    assert closed is not None
    assert closed.status == FollowUpStatus.CLOSED
    assert runtime.append_user_message(follow_up.follow_up_id, "추가 문의") is None
    assert runtime.create_admin_reply(follow_up.follow_up_id, "답변") is None


def test_close_follow_up_can_create_user_notice_outbox():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )

    closed = runtime.close_follow_up(follow_up.follow_up_id, notify_user=True)

    assert closed is not None
    assert closed.status == FollowUpStatus.CLOSED
    outbox = runtime.list_outbox(status=OutboxStatus.PENDING)
    assert len(outbox) == 1
    assert outbox[0].chat_id == 20
    assert outbox[0].text == FOLLOW_UP_CLOSED_NOTICE


def test_closing_already_closed_follow_up_does_not_duplicate_notice():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )

    runtime.close_follow_up(follow_up.follow_up_id, notify_user=True)
    runtime.close_follow_up(follow_up.follow_up_id, notify_user=True)

    assert len(runtime.list_outbox(status=OutboxStatus.PENDING)) == 1
