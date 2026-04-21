from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU, STATE_WEATHER_MENU
from PROJECT.dispatch.session_dispatcher import (
    auth_failures,
    cancel_session,
    current_state,
    go_back,
    increment_auth_failures,
    reset_session,
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
