from fastapi.testclient import TestClient

from PROJECT.admin.follow_up import DEFAULT_OUTBOX_MAX_RETRY_COUNT, FOLLOW_UP_CLOSED_NOTICE, InMemoryAdminRuntime, OutboxStatus
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.settings import SqliteSettings
from PROJECT.storage.admin_audit import RESULT_FAILURE, RESULT_SUCCESS, SqliteAdminAuditRepository
from PROJECT.storage.invitations import INVITATION_STATUS_ISSUED, SqliteInvitationRepository
from PROJECT.storage.onboarding import ONBOARDING_STATUS_APPROVED, ONBOARDING_STATUS_REJECTED, SqliteOnboardingRepository
from PROJECT.storage.onboarding_admin import OUTBOX_STATUS_PENDING, SqliteOnboardingAdminRepository
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def create_pending_onboarding_submission(runtime):
    invitation_repository = SqliteInvitationRepository(runtime.connection)
    onboarding_repository = SqliteOnboardingRepository(runtime.connection)
    invitation = invitation_repository.create_invitation()
    session = onboarding_repository.create_or_resume_from_invitation(
        invitation=invitation,
        provider_user_id="12345",
        provider_handle="farmer_user",
        preferred_locale_code="ko",
        chat_id=67890,
    )
    session = onboarding_repository.update_locale(session.id, "ko")
    session = onboarding_repository.update_name(session.id, "홍길동")
    session = onboarding_repository.update_phone(
        session.id,
        phone_raw="+855 12 345 678",
        phone_normalized="+85512345678",
    )
    return onboarding_repository.submit_pending_approval(session.id)


def test_admin_api_lists_follow_ups_and_accepts_reply():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="/support",
    )
    client = TestClient(create_admin_api_app(runtime))

    listed = client.get("/admin/follow-ups")
    reply = client.post(
        f"/admin/follow-ups/{follow_up.follow_up_id}/reply",
        json={"message": "사진을 다시 보내주세요."},
    )

    assert listed.status_code == 200
    assert listed.json()["items"][0]["follow_up_id"] == follow_up.follow_up_id
    assert reply.status_code == 200
    assert reply.json()["outbox_message"]["status"] == OutboxStatus.PENDING.value
    assert runtime.list_outbox(status=OutboxStatus.PENDING)[0].text == "사진을 다시 보내주세요."


def test_admin_api_follow_up_reply_writes_audit_event(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = InMemoryAdminRuntime()
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="/support",
        )
        audit_repository = SqliteAdminAuditRepository(sqlite_runtime.connection)
        client = TestClient(create_admin_api_app(runtime, admin_audit_repository=audit_repository))

        response = client.post(
            f"/admin/follow-ups/{follow_up.follow_up_id}/reply",
            json={"message": "사진을 다시 보내주세요.", "close_after_send": True},
            headers={"X-Admin-User-Id": "admin_test"},
        )
        events = audit_repository.list_events()

        assert response.status_code == 200
        assert [event.action_code for event in events] == [
            "admin.follow_up.close",
            "admin.follow_up.reply",
        ]
        assert {event.actor_id for event in events} == {"admin_test"}
        assert all(event.target_id == follow_up.follow_up_id for event in events)
        assert events[1].detail == {"close_after_send": True}
    finally:
        sqlite_runtime.close()


def test_admin_api_access_token_blocks_admin_api_without_credentials():
    runtime = InMemoryAdminRuntime()
    client = TestClient(create_admin_api_app(runtime, admin_access_token="secret-token"))

    response = client.get("/admin/follow-ups")
    health = client.get("/healthz")

    assert response.status_code == 401
    assert response.json()["detail"] == "admin authentication required"
    assert health.status_code == 200


def test_admin_api_access_token_allows_header_credentials():
    runtime = InMemoryAdminRuntime()
    runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    client = TestClient(create_admin_api_app(runtime, admin_access_token="secret-token"))

    response = client.get("/admin/follow-ups", headers={"X-Admin-Token": "secret-token"})

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_admin_api_allows_previous_token_before_rotation_expiry():
    runtime = InMemoryAdminRuntime()
    runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    client = TestClient(
        create_admin_api_app(
            runtime,
            admin_access_token="new-token",
            admin_previous_access_token="old-token",
            admin_previous_access_token_expires_at="2999-01-01T00:00:00+00:00",
        )
    )

    previous_token_response = client.get("/admin/follow-ups", headers={"X-Admin-Token": "old-token"})
    current_token_response = client.get(
        "/admin/follow-ups",
        headers={"Authorization": "Bearer new-token"},
    )

    assert previous_token_response.status_code == 200
    assert current_token_response.status_code == 200


def test_admin_api_rejects_previous_token_after_rotation_expiry():
    runtime = InMemoryAdminRuntime()
    client = TestClient(
        create_admin_api_app(
            runtime,
            admin_access_token="new-token",
            admin_previous_access_token="old-token",
            admin_previous_access_token_expires_at="2000-01-01T00:00:00+00:00",
        )
    )

    response = client.get("/admin/follow-ups", headers={"X-Admin-Token": "old-token"})

    assert response.status_code == 401


def test_admin_login_allows_previous_token_and_records_token_slot(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        audit_repository = SqliteAdminAuditRepository(sqlite_runtime.connection)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                admin_audit_repository=audit_repository,
                admin_access_token="new-token",
                admin_previous_access_token="old-token",
                admin_previous_access_token_expires_at="2999-01-01T00:00:00+00:00",
            )
        )

        login = client.post("/admin/login", data={"access_token": "old-token"}, follow_redirects=False)
        allowed = client.get("/admin/follow-ups")
        event = audit_repository.list_events()[0]

        assert login.status_code == 303
        assert "admin_access_token" in login.headers["set-cookie"]
        assert allowed.status_code == 200
        assert event.action_code == "admin.login"
        assert event.detail == {"role": "operator", "token_slot": "previous"}
    finally:
        sqlite_runtime.close()


def test_admin_api_viewer_role_allows_reads_and_blocks_writes(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = InMemoryAdminRuntime()
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        audit_repository = SqliteAdminAuditRepository(sqlite_runtime.connection)
        client = TestClient(
            create_admin_api_app(
                runtime,
                admin_audit_repository=audit_repository,
                admin_access_token="secret-token",
                admin_access_role="viewer",
            )
        )

        listed = client.get("/admin/follow-ups", headers={"X-Admin-Token": "secret-token"})
        blocked = client.post(
            f"/admin/follow-ups/{follow_up.follow_up_id}/reply",
            json={"message": "확인했습니다."},
            headers={"X-Admin-Token": "secret-token", "X-Admin-User-Id": "viewer_admin"},
        )
        events = audit_repository.list_events()

        assert listed.status_code == 200
        assert blocked.status_code == 403
        assert blocked.json()["detail"] == "admin write access required"
        assert runtime.get_follow_up(follow_up.follow_up_id).admin_messages == ()
        assert events[0].action_code == "admin.rbac.denied"
        assert events[0].actor_id == "viewer_admin"
        assert events[0].detail == {"method": "POST", "role": "viewer"}
    finally:
        sqlite_runtime.close()


def test_admin_page_viewer_role_blocks_write_forms(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        invitation_repository = SqliteInvitationRepository(sqlite_runtime.connection)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                invitation_repository=invitation_repository,
                admin_access_token="secret-token",
                admin_access_role="viewer",
            )
        )

        login = client.post("/admin/login", data={"access_token": "secret-token"}, follow_redirects=False)
        page = client.get("/admin/pages/invitations")
        blocked = client.post("/admin/pages/invitations", data={}, follow_redirects=False)

        assert login.status_code == 303
        assert page.status_code == 200
        assert blocked.status_code == 403
        assert "쓰기 작업을 수행할 수 없습니다" in blocked.text
        assert invitation_repository.list_invitations() == ()
    finally:
        sqlite_runtime.close()


def test_admin_page_access_token_redirects_to_login_and_sets_cookie():
    runtime = InMemoryAdminRuntime()
    client = TestClient(create_admin_api_app(runtime, admin_access_token="secret-token"))

    blocked = client.get("/admin/pages/follow-ups", follow_redirects=False)
    failed_login = client.post("/admin/login", data={"access_token": "wrong"})
    login = client.post("/admin/login", data={"access_token": "secret-token"}, follow_redirects=False)
    allowed = client.get("/admin/pages/follow-ups")

    assert blocked.status_code == 303
    assert blocked.headers["location"] == "/admin/login"
    assert failed_login.status_code == 401
    assert "올바르지 않습니다" in failed_login.text
    assert login.status_code == 303
    assert login.headers["location"] == "/admin"
    assert "admin_access_token" in login.headers["set-cookie"]
    assert allowed.status_code == 200
    assert "지원 이관 요청 목록" in allowed.text


def test_admin_login_attempts_can_be_audited(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                admin_audit_repository=audit_repository,
                admin_access_token="secret-token",
            )
        )

        failed = client.post("/admin/login", data={"access_token": "wrong"})
        success = client.post("/admin/login", data={"access_token": "secret-token"}, follow_redirects=False)
        events = audit_repository.list_events()

        assert failed.status_code == 401
        assert success.status_code == 303
        assert [event.result_code for event in events] == [RESULT_SUCCESS, RESULT_FAILURE]
        assert {event.action_code for event in events} == {"admin.login"}
        assert all(event.request_path == "/admin/login" for event in events)
    finally:
        runtime.close()


def test_admin_api_returns_404_for_missing_follow_up_reply():
    client = TestClient(create_admin_api_app(InMemoryAdminRuntime()))

    response = client.post("/admin/follow-ups/missing/reply", json={"message": "확인했습니다."})

    assert response.status_code == 404


def test_admin_api_can_close_follow_up():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    client = TestClient(create_admin_api_app(runtime))

    response = client.post(f"/admin/follow-ups/{follow_up.follow_up_id}/close", json={"reason": "admin_resolved"})

    assert response.status_code == 200
    assert response.json()["follow_up"]["closed"] is True
    assert runtime.list_outbox(status=OutboxStatus.PENDING)[0].text == FOLLOW_UP_CLOSED_NOTICE


def test_admin_api_reply_close_after_send_creates_reply_and_closed_notice_outbox():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    client = TestClient(create_admin_api_app(runtime))

    response = client.post(
        f"/admin/follow-ups/{follow_up.follow_up_id}/reply",
        json={"message": "처리를 완료했습니다.", "close_after_send": True},
    )

    assert response.status_code == 200
    assert response.json()["follow_up"]["closed"] is True
    assert [message.text for message in runtime.list_outbox(status=OutboxStatus.PENDING)] == [
        "처리를 완료했습니다.",
        FOLLOW_UP_CLOSED_NOTICE,
    ]


def test_admin_pages_show_follow_up_request_list():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="상담원 연결해주세요",
    )
    runtime.append_user_message(follow_up.follow_up_id, "추가로 사진 업로드도 안 됩니다")
    client = TestClient(create_admin_api_app(runtime))

    response = client.get("/admin/pages/follow-ups")

    assert response.status_code == 200
    assert "지원 이관 요청 목록" in response.text
    assert follow_up.follow_up_id in response.text
    assert "사용자 메시지 2개" in response.text
    assert "최근 사용자 메시지" in response.text
    assert "추가로 사진 업로드도 안 됩니다" in response.text
    assert "전체 대화 보기" in response.text
    assert "/admin/pages/invitations" in response.text
    assert "/admin/pages/onboarding/submissions" in response.text
    assert "/admin/pages/outbox" in response.text
    assert "/admin/pages/audit-events" in response.text


def test_admin_pages_show_outbox_messages():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="확인해주세요",
    )
    runtime.create_admin_reply(follow_up.follow_up_id, "입력 내용을 확인했습니다.")
    client = TestClient(create_admin_api_app(runtime))

    response = client.get("/admin/pages/outbox")

    assert response.status_code == 200
    assert "발송 대기" in response.text
    assert "입력 내용을 확인했습니다." in response.text
    assert "/admin/pages/outbox?status=manual_review" in response.text
    assert "/admin/pages/follow-ups" in response.text
    assert "/admin/pages/invitations" in response.text
    assert "/admin/pages/onboarding/submissions" in response.text
    assert "/admin/pages/audit-events" in response.text


def test_admin_outbox_api_can_filter_manual_review_messages():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "입력 내용을 확인했습니다.")
    for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
        runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")
    client = TestClient(create_admin_api_app(runtime))

    manual_review = client.get("/admin/outbox?status=manual_review")
    failed = client.get("/admin/outbox?status=failed")
    invalid = client.get("/admin/outbox?status=unknown")

    assert manual_review.status_code == 200
    assert manual_review.json()["items"][0]["status"] == OutboxStatus.MANUAL_REVIEW.value
    assert failed.status_code == 200
    assert failed.json()["items"] == []
    assert invalid.status_code == 400


def test_admin_outbox_api_can_requeue_manual_review_messages(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = InMemoryAdminRuntime()
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "입력 내용을 확인했습니다.")
        for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
            runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")
        audit_repository = SqliteAdminAuditRepository(sqlite_runtime.connection)
        client = TestClient(create_admin_api_app(runtime, admin_audit_repository=audit_repository))

        response = client.post(f"/admin/outbox/{outbox_message.outbox_id}/requeue")

        assert response.status_code == 200
        assert response.json()["outbox_message"]["status"] == OutboxStatus.PENDING.value
        assert response.json()["outbox_message"]["retry_count"] == 0
        assert response.json()["outbox_message"]["error_message"] is None
        assert runtime.claim_pending_outbox(limit=1)[0].outbox_id == outbox_message.outbox_id
        assert audit_repository.list_events()[0].action_code == "admin.outbox.requeue"
    finally:
        sqlite_runtime.close()


def test_admin_outbox_page_can_requeue_manual_review_messages():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(follow_up.follow_up_id, "입력 내용을 확인했습니다.")
    for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
        runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")
    client = TestClient(create_admin_api_app(runtime))

    page = client.get("/admin/pages/outbox?status=manual_review")
    response = client.post(
        f"/admin/pages/outbox/{outbox_message.outbox_id}/requeue",
        follow_redirects=False,
    )

    assert page.status_code == 200
    assert "다시 발송 대기열로 이동" in page.text
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/pages/outbox?status=manual_review"
    assert runtime.list_outbox(status=OutboxStatus.PENDING)[0].outbox_id == outbox_message.outbox_id


def test_admin_pages_share_navigation_links():
    runtime = InMemoryAdminRuntime()
    client = TestClient(create_admin_api_app(runtime))

    for path in (
        "/admin/pages/follow-ups",
        "/admin/pages/invitations",
        "/admin/pages/onboarding/submissions",
        "/admin/pages/outbox",
        "/admin/pages/audit-events",
    ):
        response = client.get(path)

        assert response.status_code == 200
        assert "/admin/pages/follow-ups" in response.text
        assert "/admin/pages/invitations" in response.text
        assert "/admin/pages/onboarding/submissions" in response.text
        assert "/admin/pages/outbox" in response.text
        assert "/admin/pages/audit-events" in response.text


def test_admin_home_dashboard_shows_summary_and_links(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        invitation_repository = SqliteInvitationRepository(sqlite_runtime.connection)
        onboarding_admin_repository = SqliteOnboardingAdminRepository(sqlite_runtime.connection)
        audit_repository = SqliteAdminAuditRepository(sqlite_runtime.connection)
        invitation_repository.create_invitation()
        create_pending_onboarding_submission(sqlite_runtime)
        audit_repository.record_event(action_code="admin.test", source_code="test")

        runtime = InMemoryAdminRuntime()
        runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
        )
        reply_target = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=21,
            user_id=11,
            current_step="main_menu",
        )
        _, outbox_message = runtime.create_admin_reply(reply_target.follow_up_id, "입력 내용을 확인했습니다.")
        for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
            runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")

        client = TestClient(
            create_admin_api_app(
                runtime,
                invitation_repository=invitation_repository,
                onboarding_admin_repository=onboarding_admin_repository,
                admin_audit_repository=audit_repository,
            )
        )

        response = client.get("/admin")

        assert response.status_code == 200
        assert "Admin Dashboard" in response.text
        assert "지원 이관" in response.text
        assert "초대 코드" in response.text
        assert "온보딩 승인" in response.text
        assert "발송 대기" in response.text
        assert "운영 검토" in response.text
        assert "감사 로그" in response.text
        assert "/admin/pages/follow-ups" in response.text
        assert "/admin/pages/invitations" in response.text
        assert "/admin/pages/onboarding/submissions" in response.text
        assert "/admin/pages/outbox?status=manual_review" in response.text
        assert "/admin/pages/audit-events" in response.text
    finally:
        sqlite_runtime.close()


def test_admin_pages_show_follow_up_conversation():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="입력이 안 됩니다",
    )
    runtime.append_user_message(follow_up.follow_up_id, "사진 업로드도 안 됩니다")
    runtime.create_admin_reply(follow_up.follow_up_id, "확인 후 다시 안내드리겠습니다.")
    client = TestClient(create_admin_api_app(runtime))

    response = client.get(f"/admin/pages/follow-ups/{follow_up.follow_up_id}")

    assert response.status_code == 200
    assert "사용자 대화 내용" in response.text
    assert "입력이 안 됩니다" in response.text
    assert "사진 업로드도 안 됩니다" in response.text
    assert "확인 후 다시 안내드리겠습니다." in response.text
    assert "요청 종료" in response.text
    assert f"/admin/pages/follow-ups/{follow_up.follow_up_id}/close" in response.text


def test_admin_follow_up_detail_page_can_close_without_reply(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = InMemoryAdminRuntime()
        follow_up = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="확인해주세요",
        )
        audit_repository = SqliteAdminAuditRepository(sqlite_runtime.connection)
        client = TestClient(create_admin_api_app(runtime, admin_audit_repository=audit_repository))

        response = client.post(
            f"/admin/pages/follow-ups/{follow_up.follow_up_id}/close",
            data={"reason": "duplicate_request"},
            follow_redirects=False,
        )
        closed_page = client.get(f"/admin/pages/follow-ups/{follow_up.follow_up_id}")
        events = audit_repository.list_events()

        assert response.status_code == 303
        assert response.headers["location"] == f"/admin/pages/follow-ups/{follow_up.follow_up_id}"
        assert runtime.get_follow_up(follow_up.follow_up_id).closed is True
        assert runtime.list_outbox(status=OutboxStatus.PENDING)[0].text == FOLLOW_UP_CLOSED_NOTICE
        assert closed_page.status_code == 200
        assert "이미 종료된 요청입니다." in closed_page.text
        assert events[0].action_code == "admin.follow_up.close"
        assert events[0].source_code == "admin.web.close"
        assert events[0].detail == {"reason": "duplicate_request"}
    finally:
        sqlite_runtime.close()


def test_admin_reply_page_accepts_utf8_reply_and_creates_outbox():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="확인해주세요",
    )
    client = TestClient(create_admin_api_app(runtime))

    response = client.post(
        f"/admin/pages/follow-ups/{follow_up.follow_up_id}/reply",
        data={"message": "입력 내용을 확인했습니다. 아래 메뉴에서 다시 선택해주세요."},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == f"/admin/pages/follow-ups/{follow_up.follow_up_id}"
    assert runtime.get_follow_up(follow_up.follow_up_id).admin_messages == (
        "입력 내용을 확인했습니다. 아래 메뉴에서 다시 선택해주세요.",
    )
    assert runtime.list_outbox(status=OutboxStatus.PENDING)[0].text == (
        "입력 내용을 확인했습니다. 아래 메뉴에서 다시 선택해주세요."
    )


def test_admin_reply_page_close_after_send_creates_closed_notice_outbox():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="확인해주세요",
    )
    client = TestClient(create_admin_api_app(runtime))

    response = client.post(
        f"/admin/pages/follow-ups/{follow_up.follow_up_id}/reply",
        data={"message": "처리를 완료했습니다.", "close_after_send": "true"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert runtime.get_follow_up(follow_up.follow_up_id).closed is True
    assert [message.text for message in runtime.list_outbox(status=OutboxStatus.PENDING)] == [
        "처리를 완료했습니다.",
        FOLLOW_UP_CLOSED_NOTICE,
    ]


def test_admin_reply_page_rejects_closed_follow_up():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    runtime.close_follow_up(follow_up.follow_up_id)
    client = TestClient(create_admin_api_app(runtime))

    response = client.post(
        f"/admin/pages/follow-ups/{follow_up.follow_up_id}/reply",
        data={"message": "확인했습니다."},
    )

    assert response.status_code == 404


def test_admin_api_returns_503_when_invitation_repository_is_unavailable():
    client = TestClient(create_admin_api_app(InMemoryAdminRuntime()))

    response = client.post("/admin/invitations", json={})

    assert response.status_code == 503


def test_admin_api_creates_and_lists_invitations(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        repository = SqliteInvitationRepository(runtime.connection)
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                invitation_repository=repository,
                admin_audit_repository=audit_repository,
            )
        )

        created = client.post("/admin/invitations", json={})
        listed = client.get("/admin/invitations")
        audit_events = client.get("/admin/audit-events")

        assert created.status_code == 201
        invitation = created.json()["invitation"]
        assert invitation["invite_status_code"] == INVITATION_STATUS_ISSUED
        assert invitation["start_command"] == f"/start {invitation['invite_code']}"
        assert listed.status_code == 200
        assert listed.json()["items"] == [invitation]
        assert audit_events.status_code == 200
        audit_event = audit_events.json()["items"][0]
        assert audit_event["action_code"] == "admin.invitation.create"
        assert audit_event["target_id"] == invitation["id"]
        assert audit_event["detail"]["channel_code"] == "telegram"
    finally:
        runtime.close()


def test_admin_invitation_page_creates_invitation(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        repository = SqliteInvitationRepository(runtime.connection)
        client = TestClient(create_admin_api_app(InMemoryAdminRuntime(), invitation_repository=repository))

        create_response = client.post("/admin/pages/invitations", data={}, follow_redirects=False)
        page_response = client.get("/admin/pages/invitations")

        assert create_response.status_code == 303
        assert create_response.headers["location"] == "/admin/pages/invitations"
        assert page_response.status_code == 200
        assert "초대 코드" in page_response.text
        assert "/start INV-" in page_response.text
    finally:
        runtime.close()


def test_admin_audit_page_lists_admin_actions(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        invitation_repository = SqliteInvitationRepository(runtime.connection)
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                invitation_repository=invitation_repository,
                admin_audit_repository=audit_repository,
            )
        )

        create_response = client.post("/admin/pages/invitations", data={}, follow_redirects=False)
        page_response = client.get("/admin/pages/audit-events")

        assert create_response.status_code == 303
        assert page_response.status_code == 200
        assert "감사 로그" in page_response.text
        assert "admin.invitation.create" in page_response.text
        assert "project_invitation" in page_response.text
    finally:
        runtime.close()


def test_admin_api_returns_503_when_onboarding_admin_repository_is_unavailable():
    client = TestClient(create_admin_api_app(InMemoryAdminRuntime()))

    response = client.get("/admin/onboarding/submissions")

    assert response.status_code == 503


def test_admin_api_lists_pending_onboarding_submissions(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        session = create_pending_onboarding_submission(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                onboarding_admin_repository=SqliteOnboardingAdminRepository(runtime.connection),
            )
        )

        response = client.get("/admin/onboarding/submissions")

        assert response.status_code == 200
        assert response.json()["items"][0]["onboarding_session_id"] == session.id
        assert response.json()["items"][0]["name"] == "홍길동"
    finally:
        runtime.close()


def test_admin_api_approves_onboarding_submission_and_writes_outbox(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        session = create_pending_onboarding_submission(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                onboarding_admin_repository=SqliteOnboardingAdminRepository(runtime.connection),
            )
        )

        response = client.post(
            f"/admin/onboarding/submissions/{session.id}/approve",
            json={"message": "승인되었습니다."},
        )
        outbox = runtime.connection.execute("SELECT * FROM outbox_messages").fetchone()

        assert response.status_code == 200
        assert response.json()["session"]["session_status_code"] == ONBOARDING_STATUS_APPROVED
        assert response.json()["enrollment_id"].startswith("enrollment_")
        assert outbox["message_text"] == "승인되었습니다."
        assert outbox["delivery_state_code"] == OUTBOX_STATUS_PENDING
    finally:
        runtime.close()


def test_admin_api_rejects_onboarding_submission_without_enrollment(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        session = create_pending_onboarding_submission(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                onboarding_admin_repository=SqliteOnboardingAdminRepository(runtime.connection),
            )
        )

        response = client.post(
            f"/admin/onboarding/submissions/{session.id}/reject",
            json={"reason_code": "wrong_invitation", "message": "반려되었습니다."},
        )
        enrollment_count = runtime.connection.execute("SELECT COUNT(*) FROM project_enrollments").fetchone()[0]

        assert response.status_code == 200
        assert response.json()["session"]["session_status_code"] == ONBOARDING_STATUS_REJECTED
        assert enrollment_count == 0
    finally:
        runtime.close()


def test_admin_api_rejects_duplicate_onboarding_approval(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        session = create_pending_onboarding_submission(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                onboarding_admin_repository=SqliteOnboardingAdminRepository(runtime.connection),
            )
        )

        first = client.post(f"/admin/onboarding/submissions/{session.id}/approve", json={})
        second = client.post(f"/admin/onboarding/submissions/{session.id}/approve", json={})

        assert first.status_code == 200
        assert second.status_code == 409
    finally:
        runtime.close()


def test_admin_onboarding_page_lists_pending_submissions(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        session = create_pending_onboarding_submission(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                onboarding_admin_repository=SqliteOnboardingAdminRepository(runtime.connection),
            )
        )

        response = client.get("/admin/pages/onboarding/submissions")

        assert response.status_code == 200
        assert "온보딩 승인" in response.text
        assert "홍길동" in response.text
        assert session.id in response.text
        assert "승인" in response.text
        assert "반려" in response.text
    finally:
        runtime.close()


def test_admin_onboarding_page_approves_submission_and_creates_outbox(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        session = create_pending_onboarding_submission(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                onboarding_admin_repository=SqliteOnboardingAdminRepository(runtime.connection),
            )
        )

        response = client.post(
            f"/admin/pages/onboarding/submissions/{session.id}/approve",
            data={"message": "승인되었습니다."},
            follow_redirects=False,
        )
        outbox = runtime.connection.execute("SELECT * FROM outbox_messages").fetchone()

        assert response.status_code == 303
        assert response.headers["location"] == "/admin/pages/onboarding/submissions"
        assert outbox["message_text"] == "승인되었습니다."
    finally:
        runtime.close()


def test_admin_onboarding_page_rejects_submission_and_creates_outbox(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        session = create_pending_onboarding_submission(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                onboarding_admin_repository=SqliteOnboardingAdminRepository(runtime.connection),
            )
        )

        response = client.post(
            f"/admin/pages/onboarding/submissions/{session.id}/reject",
            data={"reason_code": "wrong_invitation", "message": "반려되었습니다."},
            follow_redirects=False,
        )
        outbox = runtime.connection.execute("SELECT * FROM outbox_messages").fetchone()

        assert response.status_code == 303
        assert response.headers["location"] == "/admin/pages/onboarding/submissions"
        assert outbox["message_text"] == "반려되었습니다."
    finally:
        runtime.close()
