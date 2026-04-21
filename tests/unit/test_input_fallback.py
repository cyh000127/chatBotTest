from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_PRODUCT, STATE_FERTILIZER_USED
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu.keyboards import fallback_keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU, STATE_WEATHER_MENU
from PROJECT.dispatch.input_fallback import FALLBACK_CANCELLED, FALLBACK_DEFAULT, FALLBACK_WEATHER, fallback_key_for_state
from PROJECT.i18n.translator import get_catalog


def test_default_fallback():
    assert fallback_key_for_state(STATE_MAIN_MENU) == FALLBACK_DEFAULT


def test_weather_fallback():
    assert fallback_key_for_state(STATE_WEATHER_MENU) == FALLBACK_WEATHER


def test_cancelled_fallback():
    assert fallback_key_for_state(STATE_CANCELLED) == FALLBACK_CANCELLED


def test_fertilizer_fallbacks():
    assert fallback_key_for_state(STATE_FERTILIZER_USED) == "fertilizer_input"
    assert fallback_key_for_state(STATE_FERTILIZER_CONFIRM) == "fertilizer_confirm"


def test_default_fallback_keyboard_uses_main_menu_buttons():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(STATE_MAIN_MENU, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_TODAY_DATE
    assert layout[0][1]["text"] == catalog.BUTTON_TODAY_WEATHER


def test_profile_fallback_keyboard_uses_edit_selector_buttons():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(STATE_PROFILE_NAME, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_EDIT_NAME
    assert layout[0][1]["text"] == catalog.BUTTON_EDIT_RESIDENCE


def test_fertilizer_fallback_keyboard_uses_edit_selector_buttons():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(STATE_FERTILIZER_PRODUCT, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_FERTILIZER_EDIT_USED
    assert layout[0][1]["text"] == catalog.BUTTON_FERTILIZER_EDIT_KIND
