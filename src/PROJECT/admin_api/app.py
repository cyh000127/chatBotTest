from dataclasses import asdict

from fastapi import FastAPI, HTTPException
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


def create_admin_api_app(runtime: InMemoryAdminRuntime = admin_runtime) -> FastAPI:
    app = FastAPI(title="PROJECT Admin Follow-up API")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

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
