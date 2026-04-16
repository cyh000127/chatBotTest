from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_FOLLOWUP, STATE_PROFILE_INPUT
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_WEATHER_MENU

FALLBACK_DEFAULT = "default"
FALLBACK_WEATHER = "weather"
FALLBACK_CANCELLED = "cancelled"


def fallback_key_for_state(state: str) -> str:
    if state == STATE_WEATHER_MENU:
        return FALLBACK_WEATHER
    if state == STATE_CANCELLED:
        return FALLBACK_CANCELLED
    if state == STATE_PROFILE_INPUT:
        return "profile_input"
    if state == STATE_PROFILE_FOLLOWUP:
        return "profile_followup"
    if state == STATE_PROFILE_CONFIRM:
        return "profile_confirm"
    return FALLBACK_DEFAULT
