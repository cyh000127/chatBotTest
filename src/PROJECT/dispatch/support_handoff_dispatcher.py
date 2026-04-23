from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime
from PROJECT.dispatch.session_dispatcher import active_follow_up_id, clear_active_follow_up_id, set_active_follow_up_id, set_support_handoff, support_handoff
from PROJECT.support_handoff import SupportHandoffState, append_admin_reply, append_user_message, close_handoff, new_support_handoff
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import (
    SUPPORT_HANDOFF_ADMIN_REPLY_RECORDED,
    SUPPORT_HANDOFF_CLOSED,
    SUPPORT_HANDOFF_CREATED,
    SUPPORT_HANDOFF_USER_MESSAGE_ADDED,
)


def create_support_handoff_request(
    user_data: dict,
    *,
    route_hint: str,
    reason: str,
    current_step: str | None,
    chat_id: int | None = None,
    user_id: int | None = None,
    locale: str = "ko",
    user_message: str = "",
    failure_count: int = 0,
    recent_messages_summary: str = "",
    source: str = "runtime",
    runtime: InMemoryAdminRuntime = admin_runtime,
) -> SupportHandoffState:
    follow_up_id = None
    if chat_id is not None:
        follow_up = runtime.create_follow_up(
            route_hint=route_hint,
            reason=reason,
            chat_id=chat_id,
            user_id=user_id,
            current_step=current_step,
            locale=locale,
            user_message=user_message,
            failure_count=failure_count,
            recent_messages_summary=recent_messages_summary,
            source=source,
        )
        follow_up_id = follow_up.follow_up_id
        set_active_follow_up_id(user_data, follow_up_id)

    handoff = new_support_handoff(
        route_hint=route_hint,
        reason=reason,
        current_step=current_step,
        recent_messages_summary=recent_messages_summary or f"state={current_step or 'none'}",
        failure_count=failure_count,
        user_message=user_message,
        handoff_id=follow_up_id,
    )
    set_support_handoff(user_data, handoff)
    log_event(
        SUPPORT_HANDOFF_CREATED,
        source=source,
        handoff_id=handoff.handoff_id,
        route_hint=handoff.route_hint,
        reason=handoff.reason,
        state=handoff.current_step,
        failure_count=handoff.failure_count,
    )
    return handoff


def record_support_handoff_user_message(
    user_data: dict,
    *,
    user_message: str,
    source: str = "runtime",
    runtime: InMemoryAdminRuntime = admin_runtime,
) -> SupportHandoffState | None:
    current = support_handoff(user_data)
    if current is None or current.closed:
        return None
    follow_up_id = active_follow_up_id(user_data)
    if follow_up_id is not None:
        runtime.append_user_message(follow_up_id, user_message)
    updated = append_user_message(current, user_message)
    set_support_handoff(user_data, updated)
    log_event(
        SUPPORT_HANDOFF_USER_MESSAGE_ADDED,
        source=source,
        handoff_id=updated.handoff_id,
        route_hint=updated.route_hint,
        state=updated.current_step,
        message_count=len(updated.user_messages),
    )
    return updated


def record_support_handoff_admin_reply(user_data: dict, *, admin_message: str, source: str = "runtime") -> SupportHandoffState | None:
    current = support_handoff(user_data)
    if current is None or current.closed:
        return None
    updated = append_admin_reply(current, admin_message)
    set_support_handoff(user_data, updated)
    log_event(
        SUPPORT_HANDOFF_ADMIN_REPLY_RECORDED,
        source=source,
        handoff_id=updated.handoff_id,
        route_hint=updated.route_hint,
        state=updated.current_step,
        admin_reply_count=updated.admin_reply_count,
    )
    return updated


def close_support_handoff(
    user_data: dict,
    *,
    reason: str,
    source: str = "runtime",
    runtime: InMemoryAdminRuntime = admin_runtime,
) -> SupportHandoffState | None:
    current = support_handoff(user_data)
    if current is None or current.closed:
        return current
    follow_up_id = active_follow_up_id(user_data)
    if follow_up_id is not None:
        runtime.close_follow_up(follow_up_id)
        clear_active_follow_up_id(user_data)
    updated = close_handoff(current)
    set_support_handoff(user_data, updated)
    log_event(
        SUPPORT_HANDOFF_CLOSED,
        source=source,
        handoff_id=updated.handoff_id,
        route_hint=updated.route_hint,
        reason=reason,
        state=updated.current_step,
        user_message_count=len(updated.user_messages),
        admin_reply_count=updated.admin_reply_count,
    )
    return updated
