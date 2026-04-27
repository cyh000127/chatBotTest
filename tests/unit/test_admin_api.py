from fastapi.testclient import TestClient

from PROJECT.admin.follow_up import DEFAULT_OUTBOX_MAX_RETRY_COUNT, FOLLOW_UP_CLOSED_NOTICE, InMemoryAdminRuntime, OutboxStatus
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.admin_api.app import create_admin_api_app
from PROJECT.fields.binding import FieldBindingService
from PROJECT.settings import SqliteSettings
from PROJECT.storage.admin_audit import RESULT_FAILURE, RESULT_SUCCESS, SqliteAdminAuditRepository
from PROJECT.storage.fields import FIELD_BINDING_EXCEPTION_STATUS_OPEN, FIELD_BINDING_EXCEPTION_STATUS_RESOLVED, SqliteFieldRegistryRepository
from PROJECT.storage.invitations import INVITATION_STATUS_ISSUED, INVITATION_STATUS_REVOKED, SqliteInvitationRepository
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


def create_field_binding_exception(runtime):
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
    session = onboarding_repository.submit_pending_approval(session.id)
    SqliteOnboardingAdminRepository(runtime.connection).approve_submission(session.id)

    field_repository = SqliteFieldRegistryRepository(runtime.connection)
    version = field_repository.create_registry_version(version_label="v1")
    field_repository.import_field(
        field_registry_version_id=version.id,
        field_code="FIELD-001",
        display_name="논 1",
        polygon=[(37.0, 127.0), (37.0, 127.1), (37.1, 127.1), (37.1, 127.0)],
    )
    field_repository.publish_version(version.id)

    service = FieldBindingService(field_repository)
    result = service.lookup_location(
        provider_user_id="12345",
        latitude=35.0,
        longitude=128.0,
        accuracy_meters=12.0,
        onboarding_session_id=session.id,
        chat_id=67890,
    )
    assert result.exception is not None
    return field_repository, result.exception


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


def test_admin_api_can_filter_follow_ups_by_status():
    runtime = InMemoryAdminRuntime()
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
    client = TestClient(create_admin_api_app(runtime))

    waiting_response = client.get("/admin/follow-ups?status=waiting_admin_reply")
    open_response = client.get("/admin/follow-ups?status=open")
    closed_response = client.get("/admin/follow-ups?status=closed")
    invalid_response = client.get("/admin/follow-ups?status=unknown")

    assert waiting_response.status_code == 200
    assert [item["follow_up_id"] for item in waiting_response.json()["items"]] == [waiting.follow_up_id]
    assert open_response.status_code == 200
    assert [item["follow_up_id"] for item in open_response.json()["items"]] == [opened.follow_up_id]
    assert closed_response.status_code == 200
    assert [item["follow_up_id"] for item in closed_response.json()["items"]] == [closed.follow_up_id]
    assert invalid_response.status_code == 400
    assert invalid_response.json()["detail"] == "unknown follow-up status"


def test_admin_api_can_search_follow_ups_by_query():
    runtime = InMemoryAdminRuntime()
    runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="사진 업로드가 안 됩니다",
    )
    matched = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=21,
        user_id=987654321,
        current_step="fertilizer_confirm",
        user_message="비료 입력을 다시 확인해주세요",
    )
    client = TestClient(create_admin_api_app(runtime))

    message_response = client.get("/admin/follow-ups?query=비료 입력")
    user_response = client.get("/admin/follow-ups?query=987654321")

    assert message_response.status_code == 200
    assert [item["follow_up_id"] for item in message_response.json()["items"]] == [matched.follow_up_id]
    assert user_response.status_code == 200
    assert [item["follow_up_id"] for item in user_response.json()["items"]] == [matched.follow_up_id]


def test_admin_api_can_filter_follow_ups_by_created_date(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = SqliteAdminRuntime(sqlite_runtime.connection)
        older = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="이전 요청",
        )
        newer = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=21,
            user_id=11,
            current_step="main_menu",
            user_message="최신 요청",
        )
        sqlite_runtime.connection.execute(
            "UPDATE admin_follow_up_queue SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-20T09:00:00+00:00", "2026-04-20T09:00:00+00:00", older.follow_up_id),
        )
        sqlite_runtime.connection.execute(
            "UPDATE admin_follow_up_queue SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-23T09:00:00+00:00", "2026-04-23T09:00:00+00:00", newer.follow_up_id),
        )
        sqlite_runtime.connection.commit()
        client = TestClient(create_admin_api_app(runtime))

        response = client.get("/admin/follow-ups?created_from=2026-04-22&created_to=2026-04-23")
        invalid = client.get("/admin/follow-ups?created_from=not-a-date")

        assert response.status_code == 200
        assert [item["follow_up_id"] for item in response.json()["items"]] == [newer.follow_up_id]
        assert invalid.status_code == 400
        assert invalid.json()["detail"] == "invalid created_from"
    finally:
        sqlite_runtime.close()


def test_admin_api_can_export_follow_ups_as_csv():
    runtime = InMemoryAdminRuntime()
    runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="사진 업로드가 안 됩니다",
    )
    matched = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=21,
        user_id=11,
        current_step="fertilizer_confirm",
        user_message="비료 입력을 다시 확인해주세요",
    )
    client = TestClient(create_admin_api_app(runtime))

    response = client.get("/admin/follow-ups/export?query=비료 입력")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="admin_follow_ups.csv"'
    assert matched.follow_up_id in response.text
    assert "사진 업로드가 안 됩니다" not in response.text
    assert "follow_up_id,status,route_hint" in response.text


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


def test_admin_api_access_denial_writes_audit_event_without_token(tmp_path):
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
                admin_access_token="secret-token",
            )
        )

        response = client.get("/admin/follow-ups", headers={"X-Admin-Token": "wrong-token"})
        events = audit_repository.list_events()

        assert response.status_code == 401
        assert len(events) == 1
        event = events[0]
        assert event.action_code == "admin.access.denied"
        assert event.result_code == RESULT_FAILURE
        assert event.source_code == "admin.access.token_gate"
        assert event.actor_type_code == "unknown"
        assert event.actor_id == "unknown"
        assert event.target_type_code == "admin_route"
        assert event.request_path == "/admin/follow-ups"
        assert event.detail == {
            "html_response": False,
            "method": "GET",
            "role": "operator",
            "token_present": True,
        }
        assert "wrong-token" not in str(event.detail)
        assert "secret-token" not in str(event.detail)
    finally:
        sqlite_runtime.close()


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


def test_admin_security_status_reports_local_boundary_without_tokens():
    client = TestClient(
        create_admin_api_app(
            InMemoryAdminRuntime(),
            admin_access_token="secret-token",
            admin_previous_access_token="old-token",
            admin_previous_access_token_expires_at="2999-01-01T00:00:00+00:00",
            admin_access_role="viewer",
        )
    )

    login = client.post("/admin/login", data={"access_token": "secret-token"}, follow_redirects=False)
    page = client.get("/admin/pages/security")
    api = client.get("/admin/security-status", headers={"X-Admin-Token": "secret-token"})

    assert login.status_code == 303
    assert page.status_code == 200
    assert "보안 상태" in page.text
    assert "local_access_token" in page.text
    assert "운영 IDP" in page.text
    assert "secret-token" not in page.text
    assert "old-token" not in page.text
    assert api.status_code == 200
    payload = api.json()
    assert payload["auth_model"] == "local_access_token"
    assert payload["admin_access_required"] is True
    assert payload["admin_access_role"] == "viewer"
    assert payload["current_access_token_configured"] is True
    assert payload["previous_access_token_configured"] is True
    assert payload["previous_access_token_active"] is True
    assert payload["previous_access_token_expires_at"] == "2999-01-01T00:00:00+00:00"
    assert payload["production_identity_provider_connected"] is False
    assert payload["remaining_production_hardening"] == [
        "real_admin_identity_provider",
        "token_rotation_policy",
    ]
    assert "secret-token" not in str(payload)
    assert "old-token" not in str(payload)


def test_admin_security_status_reports_open_local_mode():
    client = TestClient(create_admin_api_app(InMemoryAdminRuntime()))

    response = client.get("/admin/security-status")

    assert response.status_code == 200
    assert response.json()["admin_access_required"] is False
    assert response.json()["current_access_token_configured"] is False


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


def test_admin_page_access_denial_writes_audit_event_without_token(tmp_path):
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
                admin_access_token="secret-token",
            )
        )

        response = client.get("/admin/pages/follow-ups", follow_redirects=False)
        events = audit_repository.list_events()

        assert response.status_code == 303
        assert response.headers["location"] == "/admin/login"
        assert len(events) == 1
        event = events[0]
        assert event.action_code == "admin.access.denied"
        assert event.request_path == "/admin/pages/follow-ups"
        assert event.detail == {
            "html_response": True,
            "method": "GET",
            "role": "operator",
            "token_present": False,
        }
    finally:
        sqlite_runtime.close()


def test_admin_page_logout_clears_cookie_and_blocks_next_request(tmp_path):
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

        login = client.post("/admin/login", data={"access_token": "secret-token"}, follow_redirects=False)
        allowed = client.get("/admin/pages/follow-ups")
        logout = client.post("/admin/logout", follow_redirects=False)
        blocked = client.get("/admin/pages/follow-ups", follow_redirects=False)
        events = audit_repository.list_events()
        logout_event = next(event for event in events if event.action_code == "admin.logout")
        denied_event = next(event for event in events if event.action_code == "admin.access.denied")

        assert login.status_code == 303
        assert allowed.status_code == 200
        assert logout.status_code == 303
        assert logout.headers["location"] == "/admin/login"
        assert "admin_access_token" in logout.headers["set-cookie"]
        assert "Max-Age=0" in logout.headers["set-cookie"]
        assert blocked.status_code == 303
        assert blocked.headers["location"] == "/admin/login"
        assert logout_event.detail == {"role": "operator", "token_slot": "current"}
        assert denied_event.request_path == "/admin/pages/follow-ups"
    finally:
        runtime.close()


def test_admin_logout_is_allowed_for_viewer_role():
    client = TestClient(
        create_admin_api_app(
            InMemoryAdminRuntime(),
            admin_access_token="secret-token",
            admin_access_role="viewer",
        )
    )

    login = client.post("/admin/login", data={"access_token": "secret-token"}, follow_redirects=False)
    logout = client.post("/admin/logout", follow_redirects=False)

    assert login.status_code == 303
    assert logout.status_code == 303
    assert logout.headers["location"] == "/admin/login"


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


def test_admin_pages_can_filter_follow_up_request_list():
    runtime = InMemoryAdminRuntime()
    waiting = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="답변 대기 요청",
    )
    opened = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=21,
        user_id=11,
        current_step="main_menu",
        user_message="응답 완료 요청",
    )
    closed = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=22,
        user_id=12,
        current_step="main_menu",
        user_message="종료된 요청",
    )
    runtime.create_admin_reply(opened.follow_up_id, "확인했습니다.")
    runtime.close_follow_up(closed.follow_up_id)
    client = TestClient(create_admin_api_app(runtime))

    response = client.get("/admin/pages/follow-ups?status=closed")

    assert response.status_code == 200
    assert "답변 대기" in response.text
    assert "진행 중" in response.text
    assert "종료" in response.text
    assert closed.follow_up_id in response.text
    assert "종료된 요청" in response.text
    assert waiting.follow_up_id not in response.text
    assert opened.follow_up_id not in response.text


def test_admin_pages_can_search_follow_up_request_list():
    runtime = InMemoryAdminRuntime()
    runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
        user_message="사진 업로드 도움 요청",
    )
    matched = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=99,
        user_id=88,
        current_step="yield_confirm",
        user_message="수확량 입력을 다시 확인하고 싶어요",
    )
    client = TestClient(create_admin_api_app(runtime))

    response = client.get("/admin/pages/follow-ups?status=waiting_admin_reply&query=수확량 입력")

    assert response.status_code == 200
    assert matched.follow_up_id in response.text
    assert "사진 업로드 도움 요청" not in response.text
    assert "/admin/follow-ups/export?status=waiting_admin_reply&amp;query=%EC%88%98%ED%99%95%EB%9F%89+%EC%9E%85%EB%A0%A5" in response.text
    assert 'name="status" value="waiting_admin_reply"' in response.text
    assert 'value="수확량 입력"' in response.text


def test_admin_pages_can_filter_follow_up_request_list_by_created_date(tmp_path):
    sqlite_runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert sqlite_runtime is not None
    try:
        runtime = SqliteAdminRuntime(sqlite_runtime.connection)
        older = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=20,
            user_id=10,
            current_step="main_menu",
            user_message="예전 요청",
        )
        newer = runtime.create_follow_up(
            route_hint="support.escalate",
            reason="explicit_support_request",
            chat_id=21,
            user_id=11,
            current_step="main_menu",
            user_message="이번 주 요청",
        )
        sqlite_runtime.connection.execute(
            "UPDATE admin_follow_up_queue SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-20T09:00:00+00:00", "2026-04-20T09:00:00+00:00", older.follow_up_id),
        )
        sqlite_runtime.connection.execute(
            "UPDATE admin_follow_up_queue SET created_at = ?, updated_at = ? WHERE id = ?",
            ("2026-04-23T09:00:00+00:00", "2026-04-23T09:00:00+00:00", newer.follow_up_id),
        )
        sqlite_runtime.connection.commit()
        client = TestClient(create_admin_api_app(runtime))

        response = client.get("/admin/pages/follow-ups?created_from=2026-04-22&created_to=2026-04-23")

        assert response.status_code == 200
        assert newer.follow_up_id in response.text
        assert older.follow_up_id not in response.text
        assert 'name="created_from"' in response.text
        assert 'value="2026-04-22"' in response.text
        assert 'name="created_to"' in response.text
        assert 'value="2026-04-23"' in response.text
    finally:
        sqlite_runtime.close()


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
    assert "/admin/outbox/export" in response.text
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


def test_admin_outbox_api_can_export_csv_with_status_filter():
    runtime = InMemoryAdminRuntime()
    follow_up = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=20,
        user_id=10,
        current_step="main_menu",
    )
    _, manual_review_message = runtime.create_admin_reply(follow_up.follow_up_id, "운영 검토가 필요합니다.")
    _, pending_message = runtime.create_admin_reply(follow_up.follow_up_id, "바로 보낼 메시지입니다.")
    for _ in range(DEFAULT_OUTBOX_MAX_RETRY_COUNT):
        runtime.mark_outbox_failed(manual_review_message.outbox_id, "transport down")
    client = TestClient(create_admin_api_app(runtime))

    response = client.get("/admin/outbox/export?status=manual_review")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="admin_outbox.csv"'
    assert manual_review_message.outbox_id in response.text
    assert pending_message.outbox_id not in response.text
    assert "outbox_id,follow_up_id,chat_id,status" in response.text


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
        "/admin/pages/security",
    ):
        response = client.get(path)

        assert response.status_code == 200
        assert "/admin/pages/follow-ups" in response.text
        assert "/admin/pages/invitations" in response.text
        assert "/admin/pages/onboarding/submissions" in response.text
        assert "/admin/pages/outbox" in response.text
        assert "/admin/pages/audit-events" in response.text
        assert "/admin/pages/security" in response.text
        assert "/admin/logout" in response.text


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
        assert "보안 상태" in response.text
        assert "/admin/pages/follow-ups" in response.text
        assert "/admin/pages/invitations" in response.text
        assert "/admin/pages/onboarding/submissions" in response.text
        assert "/admin/pages/outbox?status=manual_review" in response.text
        assert "/admin/pages/audit-events" in response.text
        assert "/admin/pages/security" in response.text
    finally:
        sqlite_runtime.close()


def test_admin_runtime_summary_reports_follow_up_and_outbox_counts():
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
    closed_target = runtime.create_follow_up(
        route_hint="support.escalate",
        reason="explicit_support_request",
        chat_id=22,
        user_id=12,
        current_step="main_menu",
    )
    _, outbox_message = runtime.create_admin_reply(reply_target.follow_up_id, "입력 내용을 확인했습니다.")
    runtime.close_follow_up(closed_target.follow_up_id, notify_user=True)
    runtime.mark_outbox_failed(outbox_message.outbox_id, "transport down")

    client = TestClient(create_admin_api_app(runtime))
    response = client.get("/admin/runtime-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["follow_ups"] == {
        "total": 3,
        "active": 2,
        "waiting_admin_reply": 1,
        "open": 1,
        "closed": 1,
    }
    assert payload["outbox"] == {
        "total": 2,
        "pending": 1,
        "sending": 0,
        "sent": 0,
        "failed": 1,
        "manual_review": 0,
    }


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


def test_admin_api_creates_invitation_with_expiry(tmp_path):
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

        created = client.post("/admin/invitations", json={"expires_at": "2999-01-01T00:00:00Z"})
        invalid = client.post("/admin/invitations", json={"expires_at": "not-a-date"})
        audit_event = audit_repository.list_events()[0]

        assert created.status_code == 201
        assert created.json()["invitation"]["expires_at"] == "2999-01-01T00:00:00+00:00"
        assert repository.list_invitations()[0].expires_at == "2999-01-01T00:00:00+00:00"
        assert invalid.status_code == 400
        assert "ISO-8601" in invalid.json()["detail"]
        assert audit_event.detail["expires_at"] == "2999-01-01T00:00:00+00:00"
    finally:
        runtime.close()


def test_admin_api_revokes_invitation_and_writes_audit_event(tmp_path):
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
        invitation = repository.create_invitation()
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                invitation_repository=repository,
                admin_audit_repository=audit_repository,
            )
        )

        response = client.post(f"/admin/invitations/{invitation.id}/revoke")
        issued = client.get(f"/admin/invitations?status={INVITATION_STATUS_ISSUED}")
        revoked = client.get(f"/admin/invitations?status={INVITATION_STATUS_REVOKED}")
        audit_event = audit_repository.list_events()[0]

        assert response.status_code == 200
        assert response.json()["invitation"]["invite_status_code"] == INVITATION_STATUS_REVOKED
        assert response.json()["invitation"]["revoked_at"] is not None
        assert issued.json()["items"] == []
        assert revoked.json()["items"][0]["id"] == invitation.id
        assert audit_event.action_code == "admin.invitation.revoke"
        assert audit_event.target_id == invitation.id
        assert audit_event.detail == {"invite_status_code": INVITATION_STATUS_REVOKED}
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

        create_response = client.post(
            "/admin/pages/invitations",
            data={"expires_at": "2999-01-01T00:00:00+00:00"},
            follow_redirects=False,
        )
        page_response = client.get("/admin/pages/invitations")
        invitation = repository.list_invitations()[0]

        assert create_response.status_code == 303
        assert create_response.headers["location"] == "/admin/pages/invitations"
        assert page_response.status_code == 200
        assert "초대 코드" in page_response.text
        assert "/start INV-" in page_response.text
        assert invitation.expires_at == "2999-01-01T00:00:00+00:00"
        assert "2999-01-01T00:00:00+00:00" in page_response.text
    finally:
        runtime.close()


def test_admin_invitation_page_rejects_invalid_expiry(tmp_path):
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

        response = client.post("/admin/pages/invitations", data={"expires_at": "not-a-date"})

        assert response.status_code == 200
        assert "ISO-8601" in response.text
        assert repository.list_invitations() == ()
    finally:
        runtime.close()


def test_admin_invitation_page_revokes_invitation(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        repository = SqliteInvitationRepository(runtime.connection)
        invitation = repository.create_invitation()
        client = TestClient(create_admin_api_app(InMemoryAdminRuntime(), invitation_repository=repository))

        page = client.get("/admin/pages/invitations")
        response = client.post(
            f"/admin/pages/invitations/{invitation.id}/revoke",
            follow_redirects=False,
        )
        updated_page = client.get("/admin/pages/invitations")
        revoked = repository.get_by_id(invitation.id)

        assert page.status_code == 200
        assert "초대 코드 회수" in page.text
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/pages/invitations"
        assert revoked is not None
        assert revoked.invite_status_code == INVITATION_STATUS_REVOKED
        assert "revoked" in updated_page.text
        assert "초대 코드 회수" not in updated_page.text
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


def test_admin_audit_api_can_filter_by_result_and_action(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        audit_repository.record_event(
            action_code="admin.follow_up.reply",
            actor_id="admin_local_default",
            result_code=RESULT_SUCCESS,
            source_code="admin.api.reply",
        )
        audit_repository.record_event(
            action_code="admin.access.denied",
            actor_type_code="unknown",
            actor_id=None,
            result_code=RESULT_FAILURE,
            source_code="admin.access.token_gate",
        )
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                admin_audit_repository=audit_repository,
            )
        )

        failed = client.get("/admin/audit-events?result=failure")
        denied = client.get("/admin/audit-events?action=admin.access.denied")
        invalid = client.get("/admin/audit-events?result=unknown")

        assert failed.status_code == 200
        assert [item["action_code"] for item in failed.json()["items"]] == ["admin.access.denied"]
        assert denied.status_code == 200
        assert [item["result_code"] for item in denied.json()["items"]] == [RESULT_FAILURE]
        assert invalid.status_code == 400
        assert invalid.json()["detail"] == "unknown audit result"
    finally:
        runtime.close()


def test_admin_audit_api_can_filter_by_occurred_date(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        audit_repository.record_event(
            action_code="admin.follow_up.reply",
            actor_id="admin_local_default",
            result_code=RESULT_SUCCESS,
            source_code="admin.api.reply",
            occurred_at="2026-04-20T10:00:00+00:00",
        )
        target = audit_repository.record_event(
            action_code="admin.access.denied",
            actor_type_code="unknown",
            actor_id=None,
            result_code=RESULT_FAILURE,
            source_code="admin.access.token_gate",
            occurred_at="2026-04-22T10:00:00+00:00",
        )
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                admin_audit_repository=audit_repository,
            )
        )

        response = client.get("/admin/audit-events?occurred_from=2026-04-22&occurred_to=2026-04-22")
        invalid = client.get("/admin/audit-events?occurred_to=not-a-date")

        assert response.status_code == 200
        assert [item["id"] for item in response.json()["items"]] == [target.id]
        assert invalid.status_code == 400
        assert invalid.json()["detail"] == "invalid occurred_to"
    finally:
        runtime.close()


def test_admin_audit_page_can_filter_by_result_and_action(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        audit_repository.record_event(
            action_code="admin.follow_up.reply",
            actor_id="admin_local_default",
            result_code=RESULT_SUCCESS,
            source_code="admin.api.reply",
        )
        audit_repository.record_event(
            action_code="admin.access.denied",
            actor_type_code="unknown",
            actor_id=None,
            result_code=RESULT_FAILURE,
            source_code="admin.access.token_gate",
        )
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                admin_audit_repository=audit_repository,
            )
        )

        response = client.get("/admin/pages/audit-events?result=failure&action=admin.access.denied")

        assert response.status_code == 200
        assert "성공" in response.text
        assert "실패" in response.text
        assert "admin.access.denied" in response.text
        assert "admin.follow_up.reply" not in response.text
    finally:
        runtime.close()


def test_admin_audit_page_can_filter_by_occurred_date(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        audit_repository.record_event(
            action_code="admin.follow_up.reply",
            actor_id="admin_local_default",
            result_code=RESULT_SUCCESS,
            source_code="admin.api.reply",
            occurred_at="2026-04-20T10:00:00+00:00",
        )
        audit_repository.record_event(
            action_code="admin.access.denied",
            actor_type_code="unknown",
            actor_id=None,
            result_code=RESULT_FAILURE,
            source_code="admin.access.token_gate",
            occurred_at="2026-04-22T10:00:00+00:00",
        )
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                admin_audit_repository=audit_repository,
            )
        )

        response = client.get("/admin/pages/audit-events?result=failure&occurred_from=2026-04-22&occurred_to=2026-04-22")

        assert response.status_code == 200
        assert "admin.access.denied" in response.text
        assert "admin.follow_up.reply" not in response.text
        assert 'name="result" value="failure"' in response.text
        assert 'value="2026-04-22"' in response.text
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


def test_admin_api_lists_and_resolves_field_binding_exceptions(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        field_repository, exception = create_field_binding_exception(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                field_registry_repository=field_repository,
            )
        )

        listed = client.get("/admin/field-binding-exceptions?status=open")
        resolved = client.post(f"/admin/field-binding-exceptions/{exception.id}/resolve", json={})

        assert listed.status_code == 200
        assert listed.json()["items"][0]["id"] == exception.id
        assert listed.json()["items"][0]["exception_status_code"] == FIELD_BINDING_EXCEPTION_STATUS_OPEN
        assert resolved.status_code == 200
        assert resolved.json()["item"]["exception_status_code"] == FIELD_BINDING_EXCEPTION_STATUS_RESOLVED
    finally:
        runtime.close()


def test_admin_field_binding_exception_page_can_mark_item_resolved(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        field_repository, exception = create_field_binding_exception(runtime)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                field_registry_repository=field_repository,
            )
        )

        page = client.get("/admin/pages/field-binding-exceptions")
        response = client.post(
            f"/admin/pages/field-binding-exceptions/{exception.id}/resolve",
            follow_redirects=False,
        )

        assert page.status_code == 200
        assert exception.id in page.text
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/pages/field-binding-exceptions?status=open"
    finally:
        runtime.close()


def test_admin_api_field_binding_exception_resolution_writes_audit_event(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None
    try:
        field_repository, exception = create_field_binding_exception(runtime)
        audit_repository = SqliteAdminAuditRepository(runtime.connection)
        client = TestClient(
            create_admin_api_app(
                InMemoryAdminRuntime(),
                field_registry_repository=field_repository,
                admin_audit_repository=audit_repository,
            )
        )

        response = client.post(f"/admin/field-binding-exceptions/{exception.id}/resolve", json={})
        events = audit_repository.list_events(action_code="admin.field_binding_exception.resolve")

        assert response.status_code == 200
        assert events
        assert events[0].target_id == exception.id
    finally:
        runtime.close()
