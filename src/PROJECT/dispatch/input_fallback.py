from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)
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
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_WEATHER_MENU

FALLBACK_DEFAULT = "default"
FALLBACK_WEATHER = "weather"
FALLBACK_CANCELLED = "cancelled"


def fallback_key_for_state(state: str) -> str:
    if state == STATE_WEATHER_MENU:
        return FALLBACK_WEATHER
    if state == STATE_CANCELLED:
        return FALLBACK_CANCELLED
    if state == STATE_PROFILE_NAME:
        return "profile_input"
    if state == STATE_PROFILE_RESIDENCE:
        return "profile_input"
    if state == STATE_PROFILE_CITY:
        return "profile_input"
    if state == STATE_PROFILE_DISTRICT:
        return "profile_input"
    if state == STATE_PROFILE_BIRTH_YEAR:
        return "profile_input"
    if state == STATE_PROFILE_BIRTH_MONTH:
        return "profile_input"
    if state == STATE_PROFILE_BIRTH_DAY:
        return "profile_followup"
    if state == STATE_PROFILE_CONFIRM:
        return "profile_confirm"
    if state == STATE_PROFILE_EDIT_SELECT:
        return "profile_followup"
    if state in {STATE_FERTILIZER_USED, STATE_FERTILIZER_KIND, STATE_FERTILIZER_PRODUCT, STATE_FERTILIZER_AMOUNT, STATE_FERTILIZER_DATE}:
        return "fertilizer_input"
    if state == STATE_FERTILIZER_CONFIRM:
        return "fertilizer_confirm"
    return FALLBACK_DEFAULT
