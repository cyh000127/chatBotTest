from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4


class SupportHandoffStatus(StrEnum):
    OPEN = "open"
    WAITING_ADMIN_REPLY = "waiting_admin_reply"
    CLOSED = "closed"


@dataclass(frozen=True)
class SupportHandoffState:
    handoff_id: str
    route_hint: str
    status: SupportHandoffStatus
    reason: str
    current_step: str | None
    recent_messages_summary: str
    failure_count: int
    user_message: str
    awaiting_admin_reply: bool = True
    admin_reply_count: int = 0
    closed: bool = False
    user_messages: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "handoff_id": self.handoff_id,
            "route_hint": self.route_hint,
            "status": self.status.value,
            "reason": self.reason,
            "current_step": self.current_step,
            "recent_messages_summary": self.recent_messages_summary,
            "failure_count": self.failure_count,
            "user_message": self.user_message,
            "awaiting_admin_reply": self.awaiting_admin_reply,
            "admin_reply_count": self.admin_reply_count,
            "closed": self.closed,
            "user_messages": list(self.user_messages),
        }


def support_handoff_from_dict(payload: dict | None) -> SupportHandoffState | None:
    if payload is None:
        return None
    return SupportHandoffState(
        handoff_id=str(payload["handoff_id"]),
        route_hint=str(payload["route_hint"]),
        status=SupportHandoffStatus(str(payload["status"])),
        reason=str(payload["reason"]),
        current_step=payload.get("current_step"),
        recent_messages_summary=str(payload.get("recent_messages_summary", "")),
        failure_count=int(payload.get("failure_count", 0)),
        user_message=str(payload.get("user_message", "")),
        awaiting_admin_reply=bool(payload.get("awaiting_admin_reply", True)),
        admin_reply_count=int(payload.get("admin_reply_count", 0)),
        closed=bool(payload.get("closed", False)),
        user_messages=tuple(str(message) for message in payload.get("user_messages", ())),
    )


def new_support_handoff(
    *,
    route_hint: str,
    reason: str,
    current_step: str | None,
    recent_messages_summary: str = "",
    failure_count: int = 0,
    user_message: str = "",
    handoff_id: str | None = None,
) -> SupportHandoffState:
    return SupportHandoffState(
        handoff_id=handoff_id or f"handoff_{uuid4().hex}",
        route_hint=route_hint,
        status=SupportHandoffStatus.WAITING_ADMIN_REPLY,
        reason=reason,
        current_step=current_step,
        recent_messages_summary=recent_messages_summary,
        failure_count=failure_count,
        user_message=user_message,
        user_messages=(user_message,) if user_message else (),
    )
