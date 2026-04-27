from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_PRODUCT, STATE_FERTILIZER_USED
from PROJECT.conversations.sample_menu.keyboards import fallback_keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU
from PROJECT.conversations.yield_intake.states import STATE_YIELD_CONFIRM, STATE_YIELD_FIELD
from PROJECT.dispatch.input_fallback import FALLBACK_CANCELLED, FALLBACK_DEFAULT, fallback_key_for_state
from PROJECT.i18n.translator import get_catalog


LEGACY_REMOVED_STATE = "profile_name"
LEGACY_REMOVED_CONFIRM_STATE = "profile_confirm"


def test_default_fallback():
    assert fallback_key_for_state(STATE_MAIN_MENU) == FALLBACK_DEFAULT


def test_removed_profile_states_fall_back_to_default_product_path():
    assert fallback_key_for_state(LEGACY_REMOVED_STATE) == FALLBACK_DEFAULT
    assert fallback_key_for_state(LEGACY_REMOVED_CONFIRM_STATE) == FALLBACK_DEFAULT


def test_cancelled_fallback():
    assert fallback_key_for_state(STATE_CANCELLED) == FALLBACK_CANCELLED


def test_fertilizer_fallbacks():
    assert fallback_key_for_state(STATE_FERTILIZER_USED) == "fertilizer_input"
    assert fallback_key_for_state(STATE_FERTILIZER_CONFIRM) == "fertilizer_confirm"


def test_yield_fallbacks():
    assert fallback_key_for_state(STATE_YIELD_FIELD) == "yield_input"
    assert fallback_key_for_state(STATE_YIELD_CONFIRM) == "yield_confirm"


def test_default_fallback_keyboard_uses_main_menu_buttons():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(STATE_MAIN_MENU, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_FERTILIZER
    assert layout[0][1]["text"] == catalog.BUTTON_YIELD
    assert layout[1][0]["text"] == catalog.BUTTON_MYFIELDS
    assert layout[1][1]["text"] == catalog.BUTTON_INPUT_RESOLVE
    assert layout[2][0]["text"] == catalog.BUTTON_SUPPORT
    assert layout[2][1]["text"] == catalog.BUTTON_HELP
    assert hasattr(catalog, "BUTTON_PROFILE") is False


def test_removed_profile_state_keyboard_uses_default_product_navigation():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(LEGACY_REMOVED_STATE, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_FERTILIZER
    assert layout[0][1]["text"] == catalog.BUTTON_YIELD


def test_removed_profile_confirm_keyboard_uses_default_product_navigation():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(LEGACY_REMOVED_CONFIRM_STATE, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_FERTILIZER
    assert layout[0][1]["text"] == catalog.BUTTON_YIELD


def test_fertilizer_fallback_keyboard_uses_current_step_navigation():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(STATE_FERTILIZER_PRODUCT, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_BACK
    assert layout[1][0]["text"] == catalog.BUTTON_RESTART


def test_fertilizer_confirm_fallback_keyboard_exposes_direct_edit_targets():
    catalog = get_catalog("ko")
    layout = fallback_keyboard_layout_for_state(STATE_FERTILIZER_CONFIRM, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_CONFIRM
    assert layout[1][0]["text"] == catalog.BUTTON_FERTILIZER_EDIT_USED
    assert layout[1][1]["text"] == catalog.BUTTON_FERTILIZER_EDIT_KIND
