from dataclasses import asdict
from html import escape
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime


class AdminReplyRequest(BaseModel):
    message: str = Field(min_length=1)
    close_after_send: bool = False


class CloseFollowUpRequest(BaseModel):
    reason: str = "admin_resolved"


def _serialize(item) -> dict:
    payload = asdict(item)
    for key, value in list(payload.items()):
        if hasattr(value, "value"):
            payload[key] = value.value
    return payload


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
  <a href="/admin/pages/follow-ups">요청 목록</a>
</div>"""


def _conversation_messages(messages: tuple[str, ...], *, empty_text: str) -> str:
    if not messages:
        return f'<p class="muted">{escape(empty_text)}</p>'
    return "\n".join(f'<div class="message">{escape(message)}</div>' for message in messages)


def create_admin_api_app(runtime: InMemoryAdminRuntime = admin_runtime) -> FastAPI:
    app = FastAPI(title="PROJECT Admin Follow-up API")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/admin", response_class=HTMLResponse)
    def admin_home() -> RedirectResponse:
        return RedirectResponse("/admin/pages/follow-ups", status_code=303)

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
  <p class="muted">사용자: {escape(str(item.user_id or "-"))} / 채팅: {escape(str(item.chat_id))}</p>
  <p class="message">{escape(item.user_message or "사용자 원문 없음")}</p>
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
            runtime.close_follow_up(follow_up_id, source="admin.web.reply_close")
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
            follow_up = runtime.close_follow_up(follow_up_id, source="admin.api.reply_close") or follow_up
        return {
            "follow_up": _serialize(follow_up),
            "outbox_message": _serialize(outbox_message),
        }

    @app.post("/admin/follow-ups/{follow_up_id}/close")
    def close_follow_up(follow_up_id: str, request: CloseFollowUpRequest) -> dict:
        follow_up = runtime.close_follow_up(follow_up_id, source="admin.api.close")
        if follow_up is None:
            raise HTTPException(status_code=404, detail="follow-up not found")
        return {"follow_up": _serialize(follow_up), "reason": request.reason}

    @app.get("/admin/outbox")
    def list_outbox() -> dict:
        return {"items": [_serialize(item) for item in runtime.list_outbox()]}

    return app
