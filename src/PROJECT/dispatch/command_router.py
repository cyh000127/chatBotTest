from dataclasses import dataclass, field

from PROJECT.canonical_intents import registry
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_FOLLOWUP,
    STATE_PROFILE_INPUT,
)
from PROJECT.conversations.sample_menu.states import STATE_WEATHER_MENU

ROUTE_HELP = "help"
ROUTE_MAIN_MENU = "main_menu"
ROUTE_CANCEL = "cancel"
ROUTE_OPEN_PROFILE = "open_profile"
ROUTE_PARSE_PROFILE = "parse_profile"
ROUTE_PROFILE_FOLLOWUP = "profile_followup"
ROUTE_PROFILE_CONFIRM = "profile_confirm"
ROUTE_PROFILE_EDIT = "profile_edit"
ROUTE_PROFILE_FINALIZE = "profile_finalize"
ROUTE_GO_BACK = "go_back"
ROUTE_SHOW_DATE = "show_date"
ROUTE_SHOW_WEATHER_MENU = "show_weather_menu"
ROUTE_SHOW_WEATHER = "show_weather"
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
        return RouteDecision(ROUTE_OPEN_PROFILE, next_state=STATE_PROFILE_INPUT)
    if intent == registry.INTENT_CANCEL:
        return RouteDecision(ROUTE_CANCEL)
    if intent == registry.INTENT_BACK:
        return RouteDecision(ROUTE_GO_BACK)
    if state == STATE_PROFILE_INPUT and intent == registry.INTENT_UNKNOWN_TEXT:
        return RouteDecision(ROUTE_PARSE_PROFILE, next_state=STATE_PROFILE_INPUT, payload=payload)
    if state == STATE_PROFILE_FOLLOWUP and intent in {registry.INTENT_UNKNOWN_TEXT, registry.INTENT_SELECT_CITY}:
        return RouteDecision(ROUTE_PROFILE_FOLLOWUP, next_state=STATE_PROFILE_FOLLOWUP, payload=payload)
    if state == STATE_PROFILE_FOLLOWUP and intent == registry.INTENT_EDIT:
        return RouteDecision(ROUTE_PROFILE_EDIT, next_state=STATE_PROFILE_INPUT)
    if state == STATE_PROFILE_CONFIRM and intent == registry.INTENT_CONFIRM:
        return RouteDecision(ROUTE_PROFILE_FINALIZE)
    if state == STATE_PROFILE_CONFIRM and intent == registry.INTENT_EDIT:
        return RouteDecision(ROUTE_PROFILE_EDIT, next_state=STATE_PROFILE_INPUT)
    if intent == registry.INTENT_SHOW_TODAY_DATE:
        return RouteDecision(ROUTE_SHOW_DATE)
    if intent == registry.INTENT_OPEN_WEATHER_MENU:
        return RouteDecision(
            ROUTE_SHOW_WEATHER_MENU,
            next_state=STATE_WEATHER_MENU,
            push_history=state != STATE_WEATHER_MENU,
        )
    if intent == registry.INTENT_SELECT_CITY and state == STATE_WEATHER_MENU:
        return RouteDecision(ROUTE_SHOW_WEATHER, payload=payload)
    return RouteDecision(ROUTE_UNKNOWN_INPUT)
