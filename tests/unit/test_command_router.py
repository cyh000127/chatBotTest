from PROJECT.canonical_intents import registry
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_USED
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT, STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU, STATE_WEATHER_MENU
from PROJECT.dispatch.command_router import (
    ROUTE_FERTILIZER_FINALIZE,
    ROUTE_OPEN_FERTILIZER,
    ROUTE_OPEN_PROFILE,
    ROUTE_PROFILE_EDIT,
    ROUTE_SHOW_WEATHER,
    ROUTE_SHOW_WEATHER_MENU,
    ROUTE_UNKNOWN_INPUT,
    route_message,
)


def test_weather_menu_button_routes_to_weather_menu():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_OPEN_WEATHER_MENU)
    assert decision.route == ROUTE_SHOW_WEATHER_MENU
    assert decision.next_state == STATE_WEATHER_MENU
    assert decision.push_history is True


def test_city_selection_routes_only_in_weather_state():
    decision = route_message(STATE_WEATHER_MENU, registry.INTENT_SELECT_CITY, {"city": "서울"})
    assert decision.route == ROUTE_SHOW_WEATHER
    assert decision.payload["city"] == "서울"


def test_city_selection_outside_weather_state_falls_back():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_SELECT_CITY, {"city": "서울"})
    assert decision.route == ROUTE_UNKNOWN_INPUT


def test_profile_entry_routes_to_profile_input():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_PROFILE)
    assert decision.route == ROUTE_OPEN_PROFILE
    assert decision.next_state == STATE_PROFILE_NAME


def test_fertilizer_entry_routes_to_fertilizer_input():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_FERTILIZER_INPUT_START)
    assert decision.route == ROUTE_OPEN_FERTILIZER
    assert decision.next_state == STATE_FERTILIZER_USED


def test_profile_confirm_edit_routes_to_edit_selection():
    decision = route_message(STATE_PROFILE_CONFIRM, registry.INTENT_EDIT)
    assert decision.route == ROUTE_PROFILE_EDIT
    assert decision.next_state == STATE_PROFILE_EDIT_SELECT
    assert decision.push_history is True


def test_fertilizer_confirm_routes_to_finalize():
    decision = route_message(STATE_FERTILIZER_CONFIRM, registry.INTENT_CONFIRM)
    assert decision.route == ROUTE_FERTILIZER_FINALIZE
