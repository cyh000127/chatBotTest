from fastapi.testclient import TestClient

from PROJECT.admin.follow_up import InMemoryAdminRuntime, OutboxStatus
from PROJECT.admin_api.app import create_admin_api_app


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
    client = TestClient(create_admin_api_app(runtime))

    response = client.get("/admin/pages/follow-ups")

    assert response.status_code == 200
    assert "지원 이관 요청 목록" in response.text
    assert follow_up.follow_up_id in response.text
    assert "상담원 연결해주세요" in response.text


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
