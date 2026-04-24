from fastapi.testclient import TestClient

from PROJECT.admin.follow_up import FOLLOW_UP_CLOSED_NOTICE, InMemoryAdminRuntime, OutboxStatus
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.settings import SqliteSettings
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
        client = TestClient(create_admin_api_app(InMemoryAdminRuntime(), invitation_repository=repository))

        created = client.post("/admin/invitations", json={})
        listed = client.get("/admin/invitations")

        assert created.status_code == 201
        invitation = created.json()["invitation"]
        assert invitation["invite_status_code"] == INVITATION_STATUS_ISSUED
        assert invitation["start_command"] == f"/start {invitation['invite_code']}"
        assert listed.status_code == 200
        assert listed.json()["items"] == [invitation]
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
