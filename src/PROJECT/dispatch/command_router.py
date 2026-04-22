from dataclasses import dataclass, field

from PROJECT.canonical_intents import registry
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_USED
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_EDIT_SELECT,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)

ROUTE_HELP = "help"
ROUTE_MAIN_MENU = "main_menu"
ROUTE_CANCEL = "cancel"
ROUTE_OPEN_PROFILE = "open_profile"
ROUTE_OPEN_FERTILIZER = "open_fertilizer"
ROUTE_PROFILE_EDIT = "profile_edit"
ROUTE_PROFILE_FINALIZE = "profile_finalize"
ROUTE_FERTILIZER_FINALIZE = "fertilizer_finalize"
ROUTE_GO_BACK = "go_back"
ROUTE_UNKNOWN_INPUT = "unknown_input"


@dataclass(frozen=True)
class RouteDecision:
    route: str
    next_state: str | None = None
    push_history: bool = False
    payload: dict = field(default_factory=dict)


def route_message(state: str, intent: str, payload: dict | None = None) -> RouteDecision:
    payload = payload or {}

    if intent == registry.INTENT_HELP:
        return RouteDecision(ROUTE_HELP)
    if intent in {registry.INTENT_START, registry.INTENT_MENU, registry.INTENT_RESTART}:
        return RouteDecision(ROUTE_MAIN_MENU)
    if intent == registry.INTENT_PROFILE:
        return RouteDecision(ROUTE_OPEN_PROFILE, next_state=STATE_PROFILE_NAME)
    if intent == registry.INTENT_FERTILIZER_INPUT_START:
        return RouteDecision(ROUTE_OPEN_FERTILIZER, next_state=STATE_FERTILIZER_USED)
    if intent == registry.INTENT_CANCEL:
        return RouteDecision(ROUTE_CANCEL)
    if intent == registry.INTENT_BACK:
        return RouteDecision(ROUTE_GO_BACK)
    if state == STATE_PROFILE_CONFIRM and intent == registry.INTENT_CONFIRM:
        return RouteDecision(ROUTE_PROFILE_FINALIZE)
    if state == STATE_FERTILIZER_CONFIRM and intent == registry.INTENT_CONFIRM:
        return RouteDecision(ROUTE_FERTILIZER_FINALIZE)
    if state == STATE_PROFILE_CONFIRM and intent == registry.INTENT_EDIT:
        return RouteDecision(ROUTE_PROFILE_EDIT, next_state=STATE_PROFILE_EDIT_SELECT, push_history=True)
    return RouteDecision(ROUTE_UNKNOWN_INPUT)
