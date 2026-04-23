from PROJECT.dispatch.session_dispatcher import set_support_handoff
from PROJECT.support_handoff import SupportHandoffState, new_support_handoff
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import SUPPORT_HANDOFF_CREATED


def create_support_handoff_request(
    user_data: dict,
    *,
    route_hint: str,
    reason: str,
    current_step: str | None,
    user_message: str = "",
    failure_count: int = 0,
    recent_messages_summary: str = "",
    source: str = "runtime",
) -> SupportHandoffState:
    handoff = new_support_handoff(
        route_hint=route_hint,
        reason=reason,
        current_step=current_step,
        recent_messages_summary=recent_messages_summary or f"state={current_step or 'none'}",
        failure_count=failure_count,
        user_message=user_message,
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
