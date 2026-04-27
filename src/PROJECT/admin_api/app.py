from dataclasses import asdict
from datetime import UTC, datetime
from html import escape
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from PROJECT.admin.follow_up import FollowUpStatus, InMemoryAdminRuntime, OutboxStatus, admin_runtime
from PROJECT.storage.invitations import (
    DEFAULT_INVITATION_CHANNEL,
    DEFAULT_INVITATION_ROLE,
    DEFAULT_LOCAL_ADMIN_USER_ID,
    DEFAULT_LOCAL_PROJECT_ID,
    INVITATION_STATUS_ISSUED,
    SqliteInvitationRepository,
)
from PROJECT.storage.admin_audit import RESULT_FAILURE, RESULT_SUCCESS, SqliteAdminAuditRepository
from PROJECT.storage.onboarding_admin import OnboardingApprovalError, SqliteOnboardingAdminRepository


class AdminReplyRequest(BaseModel):
    message: str = Field(min_length=1)
    close_after_send: bool = False


class CloseFollowUpRequest(BaseModel):
    reason: str = "admin_resolved"


class CreateInvitationRequest(BaseModel):
    project_id: str = DEFAULT_LOCAL_PROJECT_ID
    invited_by_admin_user_id: str = DEFAULT_LOCAL_ADMIN_USER_ID
    channel_code: str = DEFAULT_INVITATION_CHANNEL
    target_contact_type_code: str | None = None
    target_contact_normalized: str | None = None
    target_contact_raw: str | None = None
    target_participant_role_code: str = DEFAULT_INVITATION_ROLE
    expires_at: str | None = None


class OnboardingApprovalRequest(BaseModel):
    admin_user_id: str = DEFAULT_LOCAL_ADMIN_USER_ID
    message: str = "온보딩이 승인되었습니다. 이제 서비스를 이용할 수 있습니다."


class OnboardingRejectionRequest(BaseModel):
    admin_user_id: str = DEFAULT_LOCAL_ADMIN_USER_ID
    reason_code: str = "admin_rejected"
    message: str = "온보딩 신청이 반려되었습니다. 필요한 경우 지원을 요청해주세요."


ADMIN_ACCESS_ROLE_VIEWER = "viewer"
ADMIN_ACCESS_ROLE_OPERATOR = "operator"
ADMIN_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
ADMIN_TOKEN_SLOT_OPEN = "open"
ADMIN_TOKEN_SLOT_CURRENT = "current"
ADMIN_TOKEN_SLOT_PREVIOUS = "previous"


def _serialize(item) -> dict:
    payload = asdict(item)
    for key, value in list(payload.items()):
        if hasattr(value, "value"):
            payload[key] = value.value
    return payload


def _serialize_invitation(invitation) -> dict:
    payload = _serialize(invitation)
    payload["start_command"] = invitation.start_command
    return payload


def _serialize_audit_event(event) -> dict:
    return {
        "id": event.id,
        "actor_type_code": event.actor_type_code,
        "actor_id": event.actor_id,
        "action_code": event.action_code,
        "target_type_code": event.target_type_code,
        "target_id": event.target_id,
        "result_code": event.result_code,
        "source_code": event.source_code,
        "request_path": event.request_path,
        "detail": event.detail,
        "occurred_at": event.occurred_at,
        "created_at": event.created_at,
    }


def _require_invitation_repository(invitation_repository: SqliteInvitationRepository | None) -> SqliteInvitationRepository:
    if invitation_repository is None:
        raise HTTPException(status_code=503, detail="invitation repository unavailable")
    return invitation_repository


def _require_onboarding_admin_repository(
    onboarding_admin_repository: SqliteOnboardingAdminRepository | None,
) -> SqliteOnboardingAdminRepository:
    if onboarding_admin_repository is None:
        raise HTTPException(status_code=503, detail="onboarding admin repository unavailable")
    return onboarding_admin_repository


def _parse_outbox_status(status: str | None) -> OutboxStatus | None:
    if not status:
        return None
    try:
        return OutboxStatus(status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="unknown outbox status") from exc


def _parse_follow_up_status(status: str | None) -> FollowUpStatus | None:
    if not status:
        return None
    try:
        return FollowUpStatus(status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="unknown follow-up status") from exc


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color: #17201b;
      background: #f6f3ea;
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
    }}
    body {{ margin: 0; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 56px; }}
    a {{ color: #286a46; font-weight: 700; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 24px; }}
    .admin-nav {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
    .admin-nav a {{ display: inline-block; padding: 8px 12px; border-radius: 999px; background: #e8f2df; color: #2f5f26; }}
    .admin-nav form {{ margin: 0; }}
    .admin-nav button {{ margin: 0; padding: 8px 12px; border-radius: 999px; background: #eee9df; color: #5c4b30; }}
    .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
    .dashboard .card {{ margin: 0; }}
    .card {{ background: #fffdf7; border: 1px solid #ded6c5; border-radius: 18px; padding: 18px; margin: 14px 0; box-shadow: 0 8px 24px rgba(64, 50, 26, 0.08); }}
    .muted {{ color: #6d675c; font-size: 14px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 999px; background: #e8f2df; color: #2f5f26; font-size: 13px; font-weight: 700; }}
    .closed {{ background: #eee9df; color: #6a6154; }}
    .message {{ white-space: pre-wrap; border-left: 4px solid #d7c49b; padding: 10px 12px; margin: 8px 0; background: #fbf7ed; border-radius: 10px; }}
    label {{ display: block; font-weight: 700; margin-bottom: 8px; }}
    input, textarea {{ box-sizing: border-box; width: 100%; padding: 12px; border: 1px solid #cfc4b2; border-radius: 12px; font: inherit; background: #fffdf9; }}
    textarea {{ min-height: 150px; }}
    button {{ margin-top: 12px; padding: 11px 16px; border: 0; border-radius: 999px; background: #286a46; color: white; font-weight: 800; cursor: pointer; }}
    button:hover {{ background: #1f5438; }}
    .error {{ color: #9d2f1f; font-weight: 700; }}
  </style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>"""
    )


def _login_page(*, error: str = "") -> HTMLResponse:
    error_block = f'<p class="error">{escape(error)}</p>' if error else ""
    return _page(
        "Admin Login",
        f"""<section class="card">
  <h1>Admin Login</h1>
  <p class="muted">관리자 access token을 입력하세요.</p>
  {error_block}
  <form method="post" action="/admin/login" accept-charset="utf-8">
    <label for="access_token">Access token</label>
    <input id="access_token" name="access_token" type="password" required>
    <button type="submit">로그인</button>
  </form>
</section>""",
    )


def _topbar(title: str) -> str:
    return f"""<div class="topbar">
  <h1>{escape(title)}</h1>
  <nav class="admin-nav" aria-label="Admin navigation">
    <a href="/admin">Admin 홈</a>
    <a href="/admin/pages/follow-ups">지원 이관</a>
    <a href="/admin/pages/invitations">초대 코드</a>
    <a href="/admin/pages/onboarding/submissions">온보딩 승인</a>
    <a href="/admin/pages/outbox">발송 대기</a>
    <a href="/admin/pages/audit-events">감사 로그</a>
    <a href="/admin/pages/security">보안 상태</a>
    <form method="post" action="/admin/logout" accept-charset="utf-8">
      <button type="submit">로그아웃</button>
    </form>
  </nav>
</div>"""


def _dashboard_card(title: str, value: str | int, href: str, description: str) -> str:
    return f"""<section class="card">
  <h2><a href="{escape(href)}">{escape(title)}</a></h2>
  <p class="badge">{escape(str(value))}</p>
  <p class="muted">{escape(description)}</p>
</section>"""


def _boolean_label(value: bool) -> str:
    return "yes" if value else "no"


def _security_status_card(label: str, value: str | bool | None, description: str) -> str:
    if isinstance(value, bool):
        display = _boolean_label(value)
    elif value is None:
        display = "-"
    else:
        display = value
    return f"""<section class="card">
  <h2>{escape(label)}</h2>
  <p class="badge">{escape(display)}</p>
  <p class="muted">{escape(description)}</p>
</section>"""


def _conversation_messages(messages: tuple[str, ...], *, empty_text: str) -> str:
    if not messages:
        return f'<p class="muted">{escape(empty_text)}</p>'
    return "\n".join(f'<div class="message">{escape(message)}</div>' for message in messages)


def _outbox_requeue_form(outbox_id: str, status: OutboxStatus) -> str:
    if status != OutboxStatus.MANUAL_REVIEW:
        return ""
    return f"""<form method="post" action="/admin/pages/outbox/{escape(outbox_id)}/requeue" accept-charset="utf-8">
    <button type="submit">다시 발송 대기열로 이동</button>
  </form>"""


def _follow_up_close_form(follow_up_id: str, *, closed: bool) -> str:
    if closed:
        return '<p class="muted">이미 종료된 요청입니다.</p>'
    return f"""<form method="post" action="/admin/pages/follow-ups/{escape(follow_up_id)}/close" accept-charset="utf-8">
    <label for="reason">종료 사유 코드</label>
    <input id="reason" name="reason" value="admin_resolved" required>
    <p class="muted">종료 안내는 outbox에 기록되며, 실제 전송은 봇 delivery loop가 처리합니다.</p>
    <button type="submit">요청 종료</button>
  </form>"""


def _invitation_revoke_form(invitation_id: str, status: str) -> str:
    if status != INVITATION_STATUS_ISSUED:
        return ""
    return f"""<form method="post" action="/admin/pages/invitations/{escape(invitation_id)}/revoke" accept-charset="utf-8">
    <button type="submit">초대 코드 회수</button>
  </form>"""


def _normalize_invitation_expires_at(expires_at: str | None) -> str | None:
    if expires_at is None:
        return None
    value = expires_at.strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("expires_at은 ISO-8601 형식이어야 합니다.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat()


def _latest_user_message(item) -> str:
    if item.user_messages:
        return item.user_messages[-1]
    return item.user_message or "사용자 원문 없음"


def _normalize_admin_access_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized in {ADMIN_ACCESS_ROLE_VIEWER, ADMIN_ACCESS_ROLE_OPERATOR}:
        return normalized
    return ADMIN_ACCESS_ROLE_OPERATOR


def _admin_role_can_write(role: str) -> bool:
    return _normalize_admin_access_role(role) == ADMIN_ACCESS_ROLE_OPERATOR


def _coerce_expires_at(expires_at: datetime | str | None) -> datetime | None:
    if expires_at is None:
        return None
    if isinstance(expires_at, datetime):
        parsed = expires_at
    else:
        value = expires_at.strip()
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def create_admin_api_app(
    runtime: InMemoryAdminRuntime = admin_runtime,
    *,
    invitation_repository: SqliteInvitationRepository | None = None,
    onboarding_admin_repository: SqliteOnboardingAdminRepository | None = None,
    admin_audit_repository: SqliteAdminAuditRepository | None = None,
    admin_access_token: str = "",
    admin_previous_access_token: str = "",
    admin_previous_access_token_expires_at: datetime | str | None = None,
    admin_access_role: str = ADMIN_ACCESS_ROLE_OPERATOR,
) -> FastAPI:
    app = FastAPI(title="PROJECT Admin Follow-up API")
    resolved_admin_access_role = _normalize_admin_access_role(admin_access_role)
    previous_access_token_expires_at = _coerce_expires_at(admin_previous_access_token_expires_at)

    def admin_actor_id(request: Request, *, fallback: str = DEFAULT_LOCAL_ADMIN_USER_ID) -> str:
        return request.headers.get("x-admin-user-id") or fallback

    def record_admin_audit(
        request: Request,
        *,
        action_code: str,
        source_code: str,
        target_type_code: str | None = None,
        target_id: str | None = None,
        result_code: str = RESULT_SUCCESS,
        actor_type_code: str = "admin",
        actor_id: str | None = None,
        detail: dict | None = None,
    ) -> None:
        if admin_audit_repository is None:
            return
        admin_audit_repository.record_event(
            action_code=action_code,
            actor_type_code=actor_type_code,
            actor_id=actor_id if actor_id is not None else admin_actor_id(request),
            target_type_code=target_type_code,
            target_id=target_id,
            result_code=result_code,
            source_code=source_code,
            request_path=request.url.path,
            detail=detail,
        )

    def admin_access_required() -> bool:
        return bool(admin_access_token or admin_previous_access_token)

    def previous_access_token_active() -> bool:
        if not admin_previous_access_token or previous_access_token_expires_at is None:
            return False
        return previous_access_token_expires_at > datetime.now(UTC)

    def request_access_token(request: Request) -> str:
        authorization = request.headers.get("authorization", "")
        bearer_prefix = "Bearer "
        if authorization.startswith(bearer_prefix):
            return authorization[len(bearer_prefix):]
        return request.headers.get("x-admin-token") or request.cookies.get("admin_access_token") or ""

    def admin_token_slot_for_value(token: str) -> str | None:
        if not admin_access_required():
            return ADMIN_TOKEN_SLOT_OPEN
        if token and admin_access_token and token == admin_access_token:
            return ADMIN_TOKEN_SLOT_CURRENT
        if token and previous_access_token_active() and token == admin_previous_access_token:
            return ADMIN_TOKEN_SLOT_PREVIOUS
        return None

    def admin_request_token_slot(request: Request) -> str | None:
        return admin_token_slot_for_value(request_access_token(request))

    def admin_request_authorized(request: Request) -> bool:
        return admin_request_token_slot(request) is not None

    def wants_html(request: Request) -> bool:
        accept = request.headers.get("accept", "")
        return (
            "text/html" in accept
            or request.url.path.startswith("/admin/pages")
            or request.url.path in {"/admin", "/admin/login", "/admin/logout"}
        )

    def admin_write_request_blocked(request: Request) -> bool:
        if request.url.path in {"/admin/login", "/admin/logout"}:
            return False
        return request.method.upper() in ADMIN_WRITE_METHODS and not _admin_role_can_write(resolved_admin_access_role)

    def admin_role_denied_response(request: Request):
        record_admin_audit(
            request,
            action_code="admin.rbac.denied",
            source_code="admin.access.role_gate",
            result_code=RESULT_FAILURE,
            detail={
                "method": request.method.upper(),
                "role": resolved_admin_access_role,
            },
        )
        if wants_html(request):
            response = _page(
                "권한 없음",
                _topbar("권한 없음")
                + '<section class="card"><p class="error">현재 관리자 역할은 쓰기 작업을 수행할 수 없습니다.</p></section>',
            )
            response.status_code = 403
            return response
        return JSONResponse({"detail": "admin write access required"}, status_code=403)

    def record_admin_access_denied(request: Request, *, html_response: bool) -> None:
        record_admin_audit(
            request,
            action_code="admin.access.denied",
            source_code="admin.access.token_gate",
            result_code=RESULT_FAILURE,
            actor_type_code="unknown",
            actor_id="unknown",
            target_type_code="admin_route",
            detail={
                "method": request.method.upper(),
                "html_response": html_response,
                "token_present": bool(request_access_token(request)),
                "role": resolved_admin_access_role,
            },
        )

    @app.middleware("http")
    async def require_admin_access(request: Request, call_next):
        path = request.url.path
        if not path.startswith("/admin") or path == "/admin/login":
            return await call_next(request)
        if admin_request_authorized(request):
            if admin_write_request_blocked(request):
                return admin_role_denied_response(request)
            return await call_next(request)
        html_response = wants_html(request)
        record_admin_access_denied(request, html_response=html_response)
        if html_response:
            return RedirectResponse("/admin/login", status_code=303)
        return JSONResponse({"detail": "admin authentication required"}, status_code=401)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/admin/login", response_class=HTMLResponse)
    def admin_login_page() -> HTMLResponse:
        return _login_page()

    @app.post("/admin/login")
    async def submit_admin_login(request: Request):
        if not admin_access_required():
            return RedirectResponse("/admin", status_code=303)
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        access_token = (form.get("access_token") or [""])[0]
        token_slot = admin_token_slot_for_value(access_token)
        if token_slot is None:
            record_admin_audit(
                request,
                action_code="admin.login",
                source_code="admin.web.login",
                result_code=RESULT_FAILURE,
                actor_type_code="unknown",
                actor_id=None,
            )
            response = _login_page(error="Access token이 올바르지 않습니다.")
            response.status_code = 401
            return response
        record_admin_audit(
            request,
            action_code="admin.login",
            source_code="admin.web.login",
            target_type_code="admin_session",
            result_code=RESULT_SUCCESS,
            detail={"role": resolved_admin_access_role, "token_slot": token_slot},
        )
        response = RedirectResponse("/admin", status_code=303)
        response.set_cookie(
            "admin_access_token",
            access_token,
            httponly=True,
            samesite="lax",
        )
        return response

    @app.post("/admin/logout")
    def submit_admin_logout(request: Request):
        if not admin_access_required():
            return RedirectResponse("/admin", status_code=303)
        record_admin_audit(
            request,
            action_code="admin.logout",
            source_code="admin.web.logout",
            target_type_code="admin_session",
            result_code=RESULT_SUCCESS,
            detail={
                "role": resolved_admin_access_role,
                "token_slot": admin_request_token_slot(request) or "unknown",
            },
        )
        response = RedirectResponse("/admin/login", status_code=303)
        response.delete_cookie("admin_access_token")
        return response

    def admin_security_status() -> dict:
        return {
            "auth_model": "local_access_token",
            "admin_access_required": admin_access_required(),
            "admin_access_role": resolved_admin_access_role,
            "current_access_token_configured": bool(admin_access_token),
            "previous_access_token_configured": bool(admin_previous_access_token),
            "previous_access_token_active": previous_access_token_active(),
            "previous_access_token_expires_at": (
                previous_access_token_expires_at.isoformat() if previous_access_token_expires_at else None
            ),
            "production_identity_provider_connected": False,
            "remaining_production_hardening": [
                "real_admin_identity_provider",
                "token_rotation_policy",
            ],
        }

    @app.get("/admin", response_class=HTMLResponse)
    def admin_home() -> HTMLResponse:
        follow_ups = runtime.list_follow_ups(include_closed=True)
        open_follow_up_count = sum(1 for item in follow_ups if not item.closed)
        waiting_follow_up_count = sum(1 for item in follow_ups if item.awaiting_admin_reply and not item.closed)

        pending_outbox_count = len(runtime.list_outbox(status=OutboxStatus.PENDING))
        failed_outbox_count = len(runtime.list_outbox(status=OutboxStatus.FAILED))
        manual_review_outbox_count = len(runtime.list_outbox(status=OutboxStatus.MANUAL_REVIEW))

        invitation_count: str | int = "비활성"
        if invitation_repository is not None:
            invitation_count = len(invitation_repository.list_invitations())

        pending_onboarding_count: str | int = "비활성"
        if onboarding_admin_repository is not None:
            pending_onboarding_count = len(onboarding_admin_repository.list_pending_submissions())

        audit_count: str | int = "비활성"
        if admin_audit_repository is not None:
            audit_count = len(admin_audit_repository.list_events(limit=20))

        body = _topbar("Admin Dashboard") + f"""<section class="card">
  <p>로컬 관리자 기능의 현재 상태를 확인하고 필요한 작업 화면으로 이동합니다.</p>
  <p class="muted">이 화면은 운영 검증용 요약이며, 관리자 답변은 outbox를 거쳐 기존 챗봇 대화창으로 중계됩니다.</p>
</section>
<section class="dashboard" aria-label="Admin dashboard summary">
  {_dashboard_card("지원 이관", f"{open_follow_up_count} open / {waiting_follow_up_count} waiting", "/admin/pages/follow-ups", "사용자 지원 이관 요청과 대화 내역을 확인합니다.")}
  {_dashboard_card("초대 코드", invitation_count, "/admin/pages/invitations", "사용자가 /start 코드로 진입할 수 있는 초대 코드를 관리합니다.")}
  {_dashboard_card("온보딩 승인", pending_onboarding_count, "/admin/pages/onboarding/submissions", "제출된 온보딩 신청을 승인하거나 반려합니다.")}
  {_dashboard_card("발송 대기", f"{pending_outbox_count} pending / {failed_outbox_count} failed", "/admin/pages/outbox", "봇 전송 계층으로 전달될 메시지 상태를 확인합니다.")}
  {_dashboard_card("운영 검토", manual_review_outbox_count, "/admin/pages/outbox?status=manual_review", "재시도 한도를 초과한 outbox 메시지를 점검합니다.")}
  {_dashboard_card("감사 로그", audit_count, "/admin/pages/audit-events", "관리자 쓰기 작업과 접근 제어 이벤트를 확인합니다.")}
  {_dashboard_card("보안 상태", "local token", "/admin/pages/security", "로컬 인증 경계와 운영 전환 하드닝 상태를 확인합니다.")}
</section>"""
        return _page("Admin Dashboard", body)

    @app.get("/admin/security-status")
    def get_admin_security_status() -> dict:
        return admin_security_status()

    @app.get("/admin/pages/security", response_class=HTMLResponse)
    def admin_security_page() -> HTMLResponse:
        status = admin_security_status()
        remaining_items = "\n".join(
            f"<li>{escape(item)}</li>" for item in status["remaining_production_hardening"]
        )
        body = _topbar("보안 상태") + f"""<section class="card">
  <h2>로컬 관리자 인증 경계</h2>
  <p>현재 관리자 인증은 운영 IDP가 아니라 로컬 access token gate입니다.</p>
  <p class="muted">이 화면은 토큰 값을 표시하지 않고, 운영 전환에 필요한 하드닝 상태만 보여줍니다.</p>
</section>
<section class="dashboard" aria-label="Admin security status">
  {_security_status_card("인증 모델", status["auth_model"], "운영 IDP가 아닌 로컬 토큰 모드입니다.")}
  {_security_status_card("토큰 게이트", status["admin_access_required"], "관리자 route 접근에 access token이 필요한지 표시합니다.")}
  {_security_status_card("관리자 역할", status["admin_access_role"], "viewer는 읽기 전용, operator는 로컬 쓰기 작업 가능입니다.")}
  {_security_status_card("현재 토큰 설정", status["current_access_token_configured"], "값 자체는 표시하지 않고 설정 여부만 보여줍니다.")}
  {_security_status_card("이전 토큰 활성", status["previous_access_token_active"], "회전 기간 동안만 yes가 됩니다.")}
  {_security_status_card("이전 토큰 만료", status["previous_access_token_expires_at"], "토큰 값은 표시하지 않습니다.")}
  {_security_status_card("운영 IDP 연결", status["production_identity_provider_connected"], "아직 연결하지 않았습니다.")}
</section>
<section class="card">
  <h2>남은 production hardening</h2>
  <ul>
    {remaining_items}
  </ul>
</section>"""
        return _page("보안 상태", body)

    @app.get("/admin/pages/invitations", response_class=HTMLResponse)
    def invitation_page() -> HTMLResponse:
        if invitation_repository is None:
            return _page(
                "초대 코드",
                _topbar("초대 코드")
                + '<section class="card"><p class="error">SQLite 저장소가 켜져 있지 않아 초대 코드를 생성할 수 없습니다.</p></section>',
            )
        invitations = invitation_repository.list_invitations()
        if invitations:
            items = "\n".join(
                f"""<section class="card">
  <div>
    <span class="badge">{escape(invitation.invite_status_code)}</span>
    <span class="muted"> {escape(invitation.issued_at)}</span>
  </div>
  <h2>{escape(invitation.invite_code)}</h2>
  <p class="message">{escape(invitation.start_command)}</p>
  <p class="muted">프로젝트: {escape(invitation.project_id)} / 채널: {escape(invitation.channel_code)} / 역할: {escape(invitation.target_participant_role_code)}</p>
  <p class="muted">만료: {escape(invitation.expires_at or "-")} / 회수: {escape(invitation.revoked_at or "-")}</p>
  {_invitation_revoke_form(invitation.id, invitation.invite_status_code)}
</section>"""
                for invitation in invitations
            )
        else:
            items = '<section class="card"><p class="muted">생성된 초대 코드가 없습니다.</p></section>'
        form = """<section class="card">
  <h2>새 초대 코드 생성</h2>
  <form method="post" accept-charset="utf-8">
    <label for="expires_at">만료 시각 선택 입력</label>
    <input id="expires_at" name="expires_at" placeholder="예: 2999-01-01T00:00:00+00:00">
    <p class="muted">비워두면 만료 시각 없이 생성합니다. 입력할 때는 ISO-8601 형식을 사용합니다.</p>
    <button type="submit">초대 코드 생성</button>
  </form>
</section>"""
        return _page("초대 코드", _topbar("초대 코드") + form + items)

    @app.get("/admin/pages/onboarding/submissions", response_class=HTMLResponse)
    def onboarding_submission_page() -> HTMLResponse:
        if onboarding_admin_repository is None:
            return _page(
                "온보딩 승인",
                _topbar("온보딩 승인")
                + '<section class="card"><p class="error">SQLite 저장소가 켜져 있지 않아 온보딩 신청을 조회할 수 없습니다.</p></section>',
            )
        submissions = onboarding_admin_repository.list_pending_submissions()
        if submissions:
            items = "\n".join(
                f"""<section class="card">
  <div>
    <span class="badge">pending approval</span>
    <span class="muted"> {escape(submission.submitted_at or submission.created_at)}</span>
  </div>
  <h2>{escape(submission.name)}</h2>
  <p class="message">전화번호: {escape(submission.phone_normalized)}\n언어: {escape(submission.preferred_locale_code)}\nTelegram: {escape(submission.provider_user_id)}</p>
  <form method="post" action="/admin/pages/onboarding/submissions/{escape(submission.onboarding_session_id)}/approve" accept-charset="utf-8">
    <input type="hidden" name="message" value="온보딩이 승인되었습니다. 이제 서비스를 이용할 수 있습니다.">
    <button type="submit">승인</button>
  </form>
  <form method="post" action="/admin/pages/onboarding/submissions/{escape(submission.onboarding_session_id)}/reject" accept-charset="utf-8">
    <input type="hidden" name="reason_code" value="admin_rejected">
    <input type="hidden" name="message" value="온보딩 신청이 반려되었습니다. 필요한 경우 지원을 요청해주세요.">
    <button type="submit">반려</button>
  </form>
</section>"""
                for submission in submissions
            )
        else:
            items = '<section class="card"><p class="muted">승인 대기 중인 온보딩 신청이 없습니다.</p></section>'
        return _page("온보딩 승인", _topbar("온보딩 승인") + items)

    @app.get("/admin/pages/outbox", response_class=HTMLResponse)
    def outbox_page(status: str | None = None) -> HTMLResponse:
        selected_status = _parse_outbox_status(status)
        messages = runtime.list_outbox(status=selected_status)
        filter_links = """<section class="card">
  <a href="/admin/pages/outbox">전체</a>
  <a href="/admin/pages/outbox?status=pending">대기</a>
  <a href="/admin/pages/outbox?status=failed">재시도 실패</a>
  <a href="/admin/pages/outbox?status=manual_review">운영 검토</a>
</section>"""
        if messages:
            items = "\n".join(
                f"""<section class="card">
  <div>
    <span class="badge">{escape(message.status.value)}</span>
    <span class="muted"> {escape(message.created_at.isoformat())}</span>
  </div>
  <h2>{escape(message.outbox_id)}</h2>
  <p class="muted">follow-up: {escape(message.follow_up_id or "-")} / chat: {escape(str(message.chat_id))} / source: {escape(message.source)}</p>
  <p class="message">{escape(message.text)}</p>
  <p class="muted">오류: {escape(message.error_message or "-")}</p>
  {_outbox_requeue_form(message.outbox_id, message.status)}
</section>"""
                for message in messages
            )
        else:
            items = '<section class="card"><p class="muted">발송 대기 또는 발송 이력 메시지가 없습니다.</p></section>'
        return _page("발송 대기", _topbar("발송 대기") + filter_links + items)

    @app.post("/admin/pages/outbox/{outbox_id}/requeue")
    def submit_outbox_requeue_page(outbox_id: str, request: Request):
        outbox_message = runtime.requeue_manual_review_outbox(outbox_id, source="admin.web.outbox.requeue")
        if outbox_message is None:
            raise HTTPException(status_code=404, detail="manual review outbox not found")
        record_admin_audit(
            request,
            action_code="admin.outbox.requeue",
            source_code="admin.web.outbox.requeue",
            target_type_code="outbox_message",
            target_id=outbox_id,
        )
        return RedirectResponse("/admin/pages/outbox?status=manual_review", status_code=303)

    @app.get("/admin/pages/audit-events", response_class=HTMLResponse)
    def audit_event_page(limit: int = 100) -> HTMLResponse:
        if admin_audit_repository is None:
            return _page(
                "감사 로그",
                _topbar("감사 로그")
                + '<section class="card"><p class="error">SQLite 저장소가 켜져 있지 않아 감사 로그를 조회할 수 없습니다.</p></section>',
            )
        events = admin_audit_repository.list_events(limit=limit)
        if events:
            items = "\n".join(
                f"""<section class="card">
  <div>
    <span class="badge">{escape(event.result_code)}</span>
    <span class="muted"> {escape(event.occurred_at)}</span>
  </div>
  <h2>{escape(event.action_code)}</h2>
  <p class="muted">actor: {escape(event.actor_type_code)} / {escape(event.actor_id or "-")}</p>
  <p class="muted">target: {escape(event.target_type_code or "-")} / {escape(event.target_id or "-")}</p>
  <p class="muted">source: {escape(event.source_code)} / path: {escape(event.request_path or "-")}</p>
</section>"""
                for event in events
            )
        else:
            items = '<section class="card"><p class="muted">기록된 감사 로그가 없습니다.</p></section>'
        return _page("감사 로그", _topbar("감사 로그") + items)

    @app.post("/admin/pages/onboarding/submissions/{onboarding_session_id}/approve")
    async def submit_onboarding_approval_page(onboarding_session_id: str, request: Request):
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        message = (form.get("message") or ["온보딩이 승인되었습니다. 이제 서비스를 이용할 수 있습니다."])[0]
        try:
            repository.approve_submission(onboarding_session_id, message_text=message)
        except OnboardingApprovalError as exc:
            return _page(
                "온보딩 승인 실패",
                _topbar("온보딩 승인") + f'<section class="card"><p class="error">{escape(str(exc))}</p></section>',
            )
        record_admin_audit(
            request,
            action_code="admin.onboarding.approve",
            source_code="admin.web.onboarding.approve",
            target_type_code="onboarding_session",
            target_id=onboarding_session_id,
        )
        return RedirectResponse("/admin/pages/onboarding/submissions", status_code=303)

    @app.post("/admin/pages/onboarding/submissions/{onboarding_session_id}/reject")
    async def submit_onboarding_rejection_page(onboarding_session_id: str, request: Request):
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        reason_code = (form.get("reason_code") or ["admin_rejected"])[0] or "admin_rejected"
        message = (form.get("message") or ["온보딩 신청이 반려되었습니다. 필요한 경우 지원을 요청해주세요."])[0]
        try:
            repository.reject_submission(
                onboarding_session_id,
                reason_code=reason_code,
                message_text=message,
            )
        except OnboardingApprovalError as exc:
            return _page(
                "온보딩 반려 실패",
                _topbar("온보딩 승인") + f'<section class="card"><p class="error">{escape(str(exc))}</p></section>',
            )
        record_admin_audit(
            request,
            action_code="admin.onboarding.reject",
            source_code="admin.web.onboarding.reject",
            target_type_code="onboarding_session",
            target_id=onboarding_session_id,
            detail={"reason_code": reason_code},
        )
        return RedirectResponse("/admin/pages/onboarding/submissions", status_code=303)

    @app.post("/admin/pages/invitations")
    async def submit_invitation_page(request: Request):
        repository = _require_invitation_repository(invitation_repository)
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        try:
            expires_at = _normalize_invitation_expires_at((form.get("expires_at") or [""])[0])
        except ValueError as exc:
            return _page(
                "초대 코드 생성 실패",
                _topbar("초대 코드") + f'<section class="card"><p class="error">{escape(str(exc))}</p></section>',
            )
        invitation = repository.create_invitation(
            project_id=(form.get("project_id") or [DEFAULT_LOCAL_PROJECT_ID])[0] or DEFAULT_LOCAL_PROJECT_ID,
            invited_by_admin_user_id=(form.get("invited_by_admin_user_id") or [DEFAULT_LOCAL_ADMIN_USER_ID])[0]
            or DEFAULT_LOCAL_ADMIN_USER_ID,
            channel_code=(form.get("channel_code") or [DEFAULT_INVITATION_CHANNEL])[0] or DEFAULT_INVITATION_CHANNEL,
            target_participant_role_code=(form.get("target_participant_role_code") or [DEFAULT_INVITATION_ROLE])[0]
            or DEFAULT_INVITATION_ROLE,
            expires_at=expires_at,
        )
        record_admin_audit(
            request,
            action_code="admin.invitation.create",
            source_code="admin.web.invitation.create",
            target_type_code="project_invitation",
            target_id=invitation.id,
            actor_id=invitation.invited_by_admin_user_id,
            detail={
                "project_id": invitation.project_id,
                "channel_code": invitation.channel_code,
                "target_participant_role_code": invitation.target_participant_role_code,
                "expires_at": invitation.expires_at,
            },
        )
        return RedirectResponse("/admin/pages/invitations", status_code=303)

    @app.post("/admin/pages/invitations/{invitation_id}/revoke")
    def submit_invitation_revoke_page(invitation_id: str, request: Request):
        repository = _require_invitation_repository(invitation_repository)
        invitation = repository.revoke_invitation(invitation_id)
        if invitation is None:
            raise HTTPException(status_code=404, detail="issued invitation not found")
        record_admin_audit(
            request,
            action_code="admin.invitation.revoke",
            source_code="admin.web.invitation.revoke",
            target_type_code="project_invitation",
            target_id=invitation.id,
            actor_id=admin_actor_id(request),
            detail={"invite_status_code": invitation.invite_status_code},
        )
        return RedirectResponse("/admin/pages/invitations", status_code=303)

    @app.get("/admin/pages/follow-ups", response_class=HTMLResponse)
    def follow_up_request_page(include_closed: bool = True, status: str | None = None) -> HTMLResponse:
        selected_status = _parse_follow_up_status(status)
        follow_ups = runtime.list_follow_ups(
            include_closed=include_closed,
            status=selected_status,
        )
        filter_links = """<section class="card">
  <a href="/admin/pages/follow-ups">전체</a>
  <a href="/admin/pages/follow-ups?status=waiting_admin_reply">답변 대기</a>
  <a href="/admin/pages/follow-ups?status=open">진행 중</a>
  <a href="/admin/pages/follow-ups?status=closed">종료</a>
</section>"""
        if follow_ups:
            items = "\n".join(
                f"""<section class="card">
  <div>
    <span class="badge{' closed' if item.closed else ''}">{escape(item.status.value)}</span>
    <span class="muted"> {escape(item.created_at.isoformat())}</span>
  </div>
  <h2><a href="/admin/pages/follow-ups/{escape(item.follow_up_id)}">{escape(item.follow_up_id)}</a></h2>
  <p>사유: {escape(item.reason)} / 단계: {escape(item.current_step or "-")}</p>
  <p class="muted">사용자: {escape(str(item.user_id or "-"))} / 채팅: {escape(str(item.chat_id))} / 사용자 메시지 {len(item.user_messages)}개</p>
  <p class="muted">최근 사용자 메시지</p>
  <p class="message">{escape(_latest_user_message(item))}</p>
  <a href="/admin/pages/follow-ups/{escape(item.follow_up_id)}">전체 대화 보기</a>
  <a href="/admin/pages/follow-ups/{escape(item.follow_up_id)}/reply">응답하기</a>
</section>"""
                for item in follow_ups
            )
        else:
            items = '<section class="card"><p class="muted">들어온 지원 이관 요청이 없습니다.</p></section>'
        return _page("지원 이관 요청 목록", _topbar("지원 이관 요청 목록") + filter_links + items)

    @app.get("/admin/pages/follow-ups/{follow_up_id}", response_class=HTMLResponse)
    def follow_up_detail_page(follow_up_id: str) -> HTMLResponse:
        follow_up = runtime.get_follow_up(follow_up_id)
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        body = f"""{_topbar("사용자 대화 내용")}
<section class="card">
  <h2>{escape(follow_up.follow_up_id)}</h2>
  <p><span class="badge{' closed' if follow_up.closed else ''}">{escape(follow_up.status.value)}</span></p>
  <p>사유: {escape(follow_up.reason)} / 단계: {escape(follow_up.current_step or "-")}</p>
  <p class="muted">사용자: {escape(str(follow_up.user_id or "-"))} / 채팅: {escape(str(follow_up.chat_id))} / 언어: {escape(follow_up.locale)}</p>
  <p class="muted">최근 요약: {escape(follow_up.recent_messages_summary or "-")}</p>
  <a href="/admin/pages/follow-ups/{escape(follow_up.follow_up_id)}/reply">이 사용자에게 응답하기</a>
</section>
<section class="card">
  <h2>사용자 메시지</h2>
  {_conversation_messages(follow_up.user_messages, empty_text="저장된 사용자 메시지가 없습니다.")}
</section>
<section class="card">
  <h2>운영자 응답</h2>
  {_conversation_messages(follow_up.admin_messages, empty_text="아직 운영자 응답이 없습니다.")}
</section>
<section class="card">
  <h2>요청 종료</h2>
  {_follow_up_close_form(follow_up.follow_up_id, closed=follow_up.closed)}
</section>"""
        return _page("사용자 대화 내용", body)

    @app.get("/admin/pages/follow-ups/{follow_up_id}/reply", response_class=HTMLResponse)
    def follow_up_reply_page(follow_up_id: str) -> HTMLResponse:
        follow_up = runtime.get_follow_up(follow_up_id)
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        disabled = " disabled" if follow_up.closed else ""
        closed_notice = '<p class="error">이미 종료된 요청이라 응답할 수 없습니다.</p>' if follow_up.closed else ""
        body = f"""{_topbar("사용자에게 응답")}
<section class="card">
  <h2>{escape(follow_up.follow_up_id)}</h2>
  <p><span class="badge{' closed' if follow_up.closed else ''}">{escape(follow_up.status.value)}</span></p>
  <p class="message">{escape(follow_up.user_messages[-1] if follow_up.user_messages else follow_up.user_message or "사용자 원문 없음")}</p>
  <a href="/admin/pages/follow-ups/{escape(follow_up.follow_up_id)}">대화 내용 보기</a>
</section>
<section class="card">
  {closed_notice}
  <form method="post" accept-charset="utf-8">
    <label for="message">응답 메시지</label>
    <textarea id="message" name="message" required{disabled}></textarea>
    <label><input type="checkbox" name="close_after_send" value="true"{disabled}> 응답 후 요청 종료</label>
    <button type="submit"{disabled}>보내기</button>
  </form>
</section>"""
        return _page("사용자에게 응답", body)

    @app.post("/admin/pages/follow-ups/{follow_up_id}/reply")
    async def submit_follow_up_reply_page(follow_up_id: str, request: Request):
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        message = (form.get("message") or [""])[0].strip()
        close_after_send = (form.get("close_after_send") or [""])[0].lower() == "true"
        if not message:
            return _page(
                "응답 메시지 필요",
                _topbar("사용자에게 응답")
                + '<section class="card"><p class="error">응답 메시지를 입력해주세요.</p></section>',
            )
        result = runtime.create_admin_reply(follow_up_id, message, source="admin.web.reply")
        if result is None:
            raise HTTPException(status_code=404, detail="open follow-up not found")
        record_admin_audit(
            request,
            action_code="admin.follow_up.reply",
            source_code="admin.web.reply",
            target_type_code="admin_follow_up_queue",
            target_id=follow_up_id,
            detail={"close_after_send": close_after_send},
        )
        if close_after_send:
            runtime.close_follow_up(follow_up_id, source="admin.web.reply_close", notify_user=True)
            record_admin_audit(
                request,
                action_code="admin.follow_up.close",
                source_code="admin.web.reply_close",
                target_type_code="admin_follow_up_queue",
                target_id=follow_up_id,
                detail={"reason": "close_after_send"},
            )
        return RedirectResponse(f"/admin/pages/follow-ups/{follow_up_id}", status_code=303)

    @app.post("/admin/pages/follow-ups/{follow_up_id}/close")
    async def submit_follow_up_close_page(follow_up_id: str, request: Request):
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        reason = (form.get("reason") or ["admin_resolved"])[0].strip() or "admin_resolved"
        follow_up = runtime.close_follow_up(follow_up_id, source="admin.web.close", notify_user=True)
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        record_admin_audit(
            request,
            action_code="admin.follow_up.close",
            source_code="admin.web.close",
            target_type_code="admin_follow_up_queue",
            target_id=follow_up_id,
            detail={"reason": reason},
        )
        return RedirectResponse(f"/admin/pages/follow-ups/{follow_up_id}", status_code=303)

    @app.get("/admin/follow-ups")
    def list_follow_ups(include_closed: bool = True, status: str | None = None) -> dict:
        selected_status = _parse_follow_up_status(status)
        return {
            "items": [
                _serialize(item)
                for item in runtime.list_follow_ups(
                    include_closed=include_closed,
                    status=selected_status,
                )
            ],
        }

    @app.get("/admin/follow-ups/{follow_up_id}")
    def get_follow_up(follow_up_id: str) -> dict:
        follow_up = runtime.get_follow_up(follow_up_id)
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        return _serialize(follow_up)

    @app.post("/admin/follow-ups/{follow_up_id}/reply")
    def reply_to_follow_up(follow_up_id: str, payload: AdminReplyRequest, request: Request) -> dict:
        result = runtime.create_admin_reply(follow_up_id, payload.message, source="admin.api.reply")
        if result is None:
            raise HTTPException(status_code=404, detail="open follow-up not found")
        follow_up, outbox_message = result
        record_admin_audit(
            request,
            action_code="admin.follow_up.reply",
            source_code="admin.api.reply",
            target_type_code="admin_follow_up_queue",
            target_id=follow_up_id,
            detail={"close_after_send": payload.close_after_send},
        )
        if payload.close_after_send:
            follow_up = runtime.close_follow_up(follow_up_id, source="admin.api.reply_close", notify_user=True) or follow_up
            record_admin_audit(
                request,
                action_code="admin.follow_up.close",
                source_code="admin.api.reply_close",
                target_type_code="admin_follow_up_queue",
                target_id=follow_up_id,
                detail={"reason": "close_after_send"},
            )
        return {
            "follow_up": _serialize(follow_up),
            "outbox_message": _serialize(outbox_message),
        }

    @app.post("/admin/follow-ups/{follow_up_id}/close")
    def close_follow_up(follow_up_id: str, payload: CloseFollowUpRequest, request: Request) -> dict:
        follow_up = runtime.close_follow_up(follow_up_id, source="admin.api.close", notify_user=True)
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        record_admin_audit(
            request,
            action_code="admin.follow_up.close",
            source_code="admin.api.close",
            target_type_code="admin_follow_up_queue",
            target_id=follow_up_id,
            detail={"reason": payload.reason},
        )
        return {"follow_up": _serialize(follow_up), "reason": payload.reason}

    @app.get("/admin/outbox")
    def list_outbox(status: str | None = None) -> dict:
        return {"items": [_serialize(item) for item in runtime.list_outbox(status=_parse_outbox_status(status))]}

    @app.post("/admin/outbox/{outbox_id}/requeue")
    def requeue_outbox(outbox_id: str, request: Request) -> dict:
        outbox_message = runtime.requeue_manual_review_outbox(outbox_id, source="admin.api.outbox.requeue")
        if outbox_message is None:
            raise HTTPException(status_code=404, detail="manual review outbox not found")
        record_admin_audit(
            request,
            action_code="admin.outbox.requeue",
            source_code="admin.api.outbox.requeue",
            target_type_code="outbox_message",
            target_id=outbox_id,
        )
        return {"outbox_message": _serialize(outbox_message)}

    @app.get("/admin/audit-events")
    def list_audit_events(limit: int = 100) -> dict:
        if admin_audit_repository is None:
            raise HTTPException(status_code=503, detail="admin audit repository unavailable")
        return {"items": [_serialize_audit_event(event) for event in admin_audit_repository.list_events(limit=limit)]}

    @app.post("/admin/invitations", status_code=201)
    def create_invitation(payload: CreateInvitationRequest, request: Request) -> dict:
        repository = _require_invitation_repository(invitation_repository)
        try:
            expires_at = _normalize_invitation_expires_at(payload.expires_at)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        invitation = repository.create_invitation(
            project_id=payload.project_id,
            invited_by_admin_user_id=payload.invited_by_admin_user_id,
            channel_code=payload.channel_code,
            target_contact_type_code=payload.target_contact_type_code,
            target_contact_normalized=payload.target_contact_normalized,
            target_contact_raw=payload.target_contact_raw,
            target_participant_role_code=payload.target_participant_role_code,
            expires_at=expires_at,
        )
        record_admin_audit(
            request,
            action_code="admin.invitation.create",
            source_code="admin.api.invitation.create",
            target_type_code="project_invitation",
            target_id=invitation.id,
            actor_id=invitation.invited_by_admin_user_id,
            detail={
                "project_id": invitation.project_id,
                "channel_code": invitation.channel_code,
                "target_participant_role_code": invitation.target_participant_role_code,
                "expires_at": invitation.expires_at,
            },
        )
        return {"invitation": _serialize_invitation(invitation)}

    @app.get("/admin/invitations")
    def list_invitations(status: str | None = None) -> dict:
        repository = _require_invitation_repository(invitation_repository)
        return {
            "items": [
                _serialize_invitation(invitation)
                for invitation in repository.list_invitations(status=status)
            ],
        }

    @app.post("/admin/invitations/{invitation_id}/revoke")
    def revoke_invitation(invitation_id: str, request: Request) -> dict:
        repository = _require_invitation_repository(invitation_repository)
        invitation = repository.revoke_invitation(invitation_id)
        if invitation is None:
            raise HTTPException(status_code=404, detail="issued invitation not found")
        record_admin_audit(
            request,
            action_code="admin.invitation.revoke",
            source_code="admin.api.invitation.revoke",
            target_type_code="project_invitation",
            target_id=invitation.id,
            actor_id=admin_actor_id(request),
            detail={"invite_status_code": invitation.invite_status_code},
        )
        return {"invitation": _serialize_invitation(invitation)}

    @app.get("/admin/onboarding/submissions")
    def list_onboarding_submissions() -> dict:
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        return {
            "items": [_serialize(submission) for submission in repository.list_pending_submissions()],
        }

    @app.post("/admin/onboarding/submissions/{onboarding_session_id}/approve")
    def approve_onboarding_submission(
        onboarding_session_id: str,
        payload: OnboardingApprovalRequest,
        request: Request,
    ) -> dict:
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        try:
            result = repository.approve_submission(
                onboarding_session_id,
                admin_user_id=payload.admin_user_id,
                message_text=payload.message,
            )
        except OnboardingApprovalError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        record_admin_audit(
            request,
            action_code="admin.onboarding.approve",
            source_code="admin.api.onboarding.approve",
            target_type_code="onboarding_session",
            target_id=onboarding_session_id,
            actor_id=payload.admin_user_id,
        )
        return {
            "session": _serialize(result.session),
            "participant_id": result.participant_id,
            "contact_id": result.contact_id,
            "identity_id": result.identity_id,
            "enrollment_id": result.enrollment_id,
            "outbox_id": result.outbox_id,
        }

    @app.post("/admin/onboarding/submissions/{onboarding_session_id}/reject")
    def reject_onboarding_submission(
        onboarding_session_id: str,
        payload: OnboardingRejectionRequest,
        request: Request,
    ) -> dict:
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        try:
            result = repository.reject_submission(
                onboarding_session_id,
                admin_user_id=payload.admin_user_id,
                reason_code=payload.reason_code,
                message_text=payload.message,
            )
        except OnboardingApprovalError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        record_admin_audit(
            request,
            action_code="admin.onboarding.reject",
            source_code="admin.api.onboarding.reject",
            target_type_code="onboarding_session",
            target_id=onboarding_session_id,
            actor_id=payload.admin_user_id,
            detail={"reason_code": payload.reason_code},
        )
        return {
            "session": _serialize(result.session),
            "outbox_id": result.outbox_id,
        }

    return app
