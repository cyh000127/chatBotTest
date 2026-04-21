from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_USED
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU, STATE_WEATHER_MENU
from PROJECT.dispatch.input_fallback import FALLBACK_CANCELLED, FALLBACK_DEFAULT, FALLBACK_WEATHER, fallback_key_for_state


def test_default_fallback():
    assert fallback_key_for_state(STATE_MAIN_MENU) == FALLBACK_DEFAULT


def test_weather_fallback():
    assert fallback_key_for_state(STATE_WEATHER_MENU) == FALLBACK_WEATHER


def test_cancelled_fallback():
    assert fallback_key_for_state(STATE_CANCELLED) == FALLBACK_CANCELLED


def test_fertilizer_fallbacks():
    assert fallback_key_for_state(STATE_FERTILIZER_USED) == "fertilizer_input"
    assert fallback_key_for_state(STATE_FERTILIZER_CONFIRM) == "fertilizer_confirm"
