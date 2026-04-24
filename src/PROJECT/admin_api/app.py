from dataclasses import asdict
from html import escape
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime
from PROJECT.storage.invitations import (
    DEFAULT_INVITATION_CHANNEL,
    DEFAULT_INVITATION_ROLE,
    DEFAULT_LOCAL_ADMIN_USER_ID,
    DEFAULT_LOCAL_PROJECT_ID,
    SqliteInvitationRepository,
)
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
    .card {{ background: #fffdf7; border: 1px solid #ded6c5; border-radius: 18px; padding: 18px; margin: 14px 0; box-shadow: 0 8px 24px rgba(64, 50, 26, 0.08); }}
    .muted {{ color: #6d675c; font-size: 14px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 999px; background: #e8f2df; color: #2f5f26; font-size: 13px; font-weight: 700; }}
    .closed {{ background: #eee9df; color: #6a6154; }}
    .message {{ white-space: pre-wrap; border-left: 4px solid #d7c49b; padding: 10px 12px; margin: 8px 0; background: #fbf7ed; border-radius: 10px; }}
    label {{ display: block; font-weight: 700; margin-bottom: 8px; }}
    textarea {{ box-sizing: border-box; width: 100%; min-height: 150px; padding: 12px; border: 1px solid #cfc4b2; border-radius: 12px; font: inherit; background: #fffdf9; }}
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


def _topbar(title: str) -> str:
    return f"""<div class="topbar">
  <h1>{escape(title)}</h1>
  <div>
    <a href="/admin/pages/follow-ups">요청 목록</a>
    <a href="/admin/pages/invitations">초대 코드</a>
  </div>
</div>"""


def _conversation_messages(messages: tuple[str, ...], *, empty_text: str) -> str:
    if not messages:
        return f'<p class="muted">{escape(empty_text)}</p>'
    return "\n".join(f'<div class="message">{escape(message)}</div>' for message in messages)


def _latest_user_message(item) -> str:
    if item.user_messages:
        return item.user_messages[-1]
    return item.user_message or "사용자 원문 없음"


def create_admin_api_app(
    runtime: InMemoryAdminRuntime = admin_runtime,
    *,
    invitation_repository: SqliteInvitationRepository | None = None,
    onboarding_admin_repository: SqliteOnboardingAdminRepository | None = None,
) -> FastAPI:
    app = FastAPI(title="PROJECT Admin Follow-up API")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/admin", response_class=HTMLResponse)
    def admin_home() -> RedirectResponse:
        return RedirectResponse("/admin/pages/follow-ups", status_code=303)

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
</section>"""
                for invitation in invitations
            )
        else:
            items = '<section class="card"><p class="muted">생성된 초대 코드가 없습니다.</p></section>'
        form = """<section class="card">
  <h2>새 초대 코드 생성</h2>
  <form method="post" accept-charset="utf-8">
    <button type="submit">초대 코드 생성</button>
  </form>
</section>"""
        return _page("초대 코드", _topbar("초대 코드") + form + items)

    @app.post("/admin/pages/invitations")
    async def submit_invitation_page(request: Request):
        repository = _require_invitation_repository(invitation_repository)
        raw_body = await request.body()
        form = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
        repository.create_invitation(
            project_id=(form.get("project_id") or [DEFAULT_LOCAL_PROJECT_ID])[0] or DEFAULT_LOCAL_PROJECT_ID,
            invited_by_admin_user_id=(form.get("invited_by_admin_user_id") or [DEFAULT_LOCAL_ADMIN_USER_ID])[0]
            or DEFAULT_LOCAL_ADMIN_USER_ID,
            channel_code=(form.get("channel_code") or [DEFAULT_INVITATION_CHANNEL])[0] or DEFAULT_INVITATION_CHANNEL,
            target_participant_role_code=(form.get("target_participant_role_code") or [DEFAULT_INVITATION_ROLE])[0]
            or DEFAULT_INVITATION_ROLE,
        )
        return RedirectResponse("/admin/pages/invitations", status_code=303)

    @app.get("/admin/pages/follow-ups", response_class=HTMLResponse)
    def follow_up_request_page(include_closed: bool = True) -> HTMLResponse:
        follow_ups = runtime.list_follow_ups(include_closed=include_closed)
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
        return _page("지원 이관 요청 목록", _topbar("지원 이관 요청 목록") + items)

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
        if close_after_send:
            runtime.close_follow_up(follow_up_id, source="admin.web.reply_close", notify_user=True)
        return RedirectResponse(f"/admin/pages/follow-ups/{follow_up_id}", status_code=303)

    @app.get("/admin/follow-ups")
    def list_follow_ups(include_closed: bool = True) -> dict:
        return {
            "items": [_serialize(item) for item in runtime.list_follow_ups(include_closed=include_closed)],
        }

    @app.get("/admin/follow-ups/{follow_up_id}")
    def get_follow_up(follow_up_id: str) -> dict:
        follow_up = runtime.get_follow_up(follow_up_id)
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        return _serialize(follow_up)

    @app.post("/admin/follow-ups/{follow_up_id}/reply")
    def reply_to_follow_up(follow_up_id: str, request: AdminReplyRequest) -> dict:
        result = runtime.create_admin_reply(follow_up_id, request.message, source="admin.api.reply")
        if result is None:
            raise HTTPException(status_code=404, detail="open follow-up not found")
        follow_up, outbox_message = result
        if request.close_after_send:
            follow_up = runtime.close_follow_up(follow_up_id, source="admin.api.reply_close", notify_user=True) or follow_up
        return {
            "follow_up": _serialize(follow_up),
            "outbox_message": _serialize(outbox_message),
        }

    @app.post("/admin/follow-ups/{follow_up_id}/close")
    def close_follow_up(follow_up_id: str, request: CloseFollowUpRequest) -> dict:
        follow_up = runtime.close_follow_up(follow_up_id, source="admin.api.close", notify_user=True)
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        return {"follow_up": _serialize(follow_up), "reason": request.reason}

    @app.get("/admin/outbox")
    def list_outbox() -> dict:
        return {"items": [_serialize(item) for item in runtime.list_outbox()]}

    @app.post("/admin/invitations", status_code=201)
    def create_invitation(request: CreateInvitationRequest) -> dict:
        repository = _require_invitation_repository(invitation_repository)
        invitation = repository.create_invitation(
            project_id=request.project_id,
            invited_by_admin_user_id=request.invited_by_admin_user_id,
            channel_code=request.channel_code,
            target_contact_type_code=request.target_contact_type_code,
            target_contact_normalized=request.target_contact_normalized,
            target_contact_raw=request.target_contact_raw,
            target_participant_role_code=request.target_participant_role_code,
            expires_at=request.expires_at,
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

    @app.get("/admin/onboarding/submissions")
    def list_onboarding_submissions() -> dict:
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        return {
            "items": [_serialize(submission) for submission in repository.list_pending_submissions()],
        }

    @app.post("/admin/onboarding/submissions/{onboarding_session_id}/approve")
    def approve_onboarding_submission(onboarding_session_id: str, request: OnboardingApprovalRequest) -> dict:
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        try:
            result = repository.approve_submission(
                onboarding_session_id,
                admin_user_id=request.admin_user_id,
                message_text=request.message,
            )
        except OnboardingApprovalError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "session": _serialize(result.session),
            "participant_id": result.participant_id,
            "contact_id": result.contact_id,
            "identity_id": result.identity_id,
            "enrollment_id": result.enrollment_id,
            "outbox_id": result.outbox_id,
        }

    @app.post("/admin/onboarding/submissions/{onboarding_session_id}/reject")
    def reject_onboarding_submission(onboarding_session_id: str, request: OnboardingRejectionRequest) -> dict:
        repository = _require_onboarding_admin_repository(onboarding_admin_repository)
        try:
            result = repository.reject_submission(
                onboarding_session_id,
                admin_user_id=request.admin_user_id,
                reason_code=request.reason_code,
                message_text=request.message,
            )
        except OnboardingApprovalError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "session": _serialize(result.session),
            "outbox_id": result.outbox_id,
        }

    return app
