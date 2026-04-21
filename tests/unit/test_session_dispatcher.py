from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU, STATE_WEATHER_MENU
from PROJECT.dispatch.session_dispatcher import (
    auth_failures,
    cancel_session,
    confirmed_profile,
    current_state,
    go_back,
    has_confirmed_profile,
    increment_auth_failures,
    last_recovery_context,
    reset_session,
    set_last_recovery_context,
    set_confirmed_profile,
    set_selected_city,
    set_state,
)


def test_reset_session_sets_main_menu():
    user_data = {}
    reset_session(user_data)
    assert current_state(user_data) == STATE_MAIN_MENU


def test_set_state_pushes_history_and_go_back_returns_previous_state():
    user_data = {}
    reset_session(user_data)
    set_state(user_data, STATE_WEATHER_MENU, push_history=True)
    previous_state = go_back(user_data)
    assert previous_state == STATE_MAIN_MENU
    assert current_state(user_data) == STATE_MAIN_MENU


def test_cancel_session_moves_to_cancelled_state():
    user_data = {}
    cancel_session(user_data)
    assert current_state(user_data) == STATE_CANCELLED


def test_reset_session_clears_auth_failures():
    user_data = {}
    increment_auth_failures(user_data)
    increment_auth_failures(user_data)
    reset_session(user_data)
    assert auth_failures(user_data) == 0


def test_confirmed_profile_helpers_work():
    user_data = {}
    assert has_confirmed_profile(user_data) is False
    set_confirmed_profile(user_data, {"name": "최윤혁"})
    assert has_confirmed_profile(user_data) is True
    assert confirmed_profile(user_data) == {"name": "최윤혁"}


def test_last_recovery_context_is_preserved_across_reset_session():
    user_data = {}
    set_last_recovery_context(user_data, {"current_step": "weather_menu"})
    reset_session(user_data)

    assert last_recovery_context(user_data) == {"current_step": "weather_menu"}
