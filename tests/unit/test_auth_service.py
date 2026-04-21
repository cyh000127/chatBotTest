from PROJECT.auth.service import authenticate_login_id
from PROJECT.dispatch.session_dispatcher import (
    auth_failures,
    authenticate_session,
    current_user_name,
    increment_auth_failures,
    is_authenticated,
    reset_session,
)


def test_authenticate_login_id_returns_user():
    result = authenticate_login_id("okccc5")
    assert result is not None
    assert result["user_name"] == "최윤혁"


def test_authenticate_login_id_returns_none_for_unknown_user():
    assert authenticate_login_id("unknown-user") is None


def test_authenticated_session_survives_reset():
    user_data = {}
    authenticate_session(user_data, login_id="okccc5", user_name="최윤혁")
    assert is_authenticated(user_data) is True
    reset_session(user_data)
    assert is_authenticated(user_data) is True
    assert current_user_name(user_data) == "최윤혁"


def test_authenticate_session_resets_failure_count():
    user_data = {}
    increment_auth_failures(user_data)
    increment_auth_failures(user_data)
    authenticate_session(user_data, login_id="okccc5", user_name="최윤혁")
    assert auth_failures(user_data) == 0
