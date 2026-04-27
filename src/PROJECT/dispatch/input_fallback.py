from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED
from PROJECT.conversations.yield_intake.states import STATE_YIELD_AMOUNT, STATE_YIELD_CONFIRM, STATE_YIELD_DATE, STATE_YIELD_EDIT_SELECT, STATE_YIELD_FIELD, STATE_YIELD_READY

FALLBACK_DEFAULT = "default"
FALLBACK_CANCELLED = "cancelled"


def fallback_key_for_state(state: str) -> str:
    if state == STATE_CANCELLED:
        return FALLBACK_CANCELLED
    if state in {STATE_FERTILIZER_USED, STATE_FERTILIZER_KIND, STATE_FERTILIZER_PRODUCT, STATE_FERTILIZER_AMOUNT, STATE_FERTILIZER_DATE}:
        return "fertilizer_input"
    if state == STATE_FERTILIZER_CONFIRM:
        return "fertilizer_confirm"
    if state in {STATE_YIELD_READY, STATE_YIELD_FIELD, STATE_YIELD_AMOUNT, STATE_YIELD_DATE}:
        return "yield_input"
    if state == STATE_YIELD_CONFIRM:
        return "yield_confirm"
    if state == STATE_YIELD_EDIT_SELECT:
        return "yield_confirm"
    return FALLBACK_DEFAULT
