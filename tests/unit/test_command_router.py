from PROJECT.canonical_intents import registry
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU, STATE_WEATHER_MENU
from PROJECT.dispatch.command_router import ROUTE_OPEN_PROFILE, ROUTE_SHOW_WEATHER, ROUTE_SHOW_WEATHER_MENU, ROUTE_UNKNOWN_INPUT, route_message


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
