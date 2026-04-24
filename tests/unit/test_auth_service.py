from PROJECT.auth.service import authenticate_login_id
from PROJECT.dispatch.session_dispatcher import (
    auth_failures,
    authenticate_session,
    confirmed_profile,
    current_user_name,
    increment_auth_failures,
    is_authenticated,
    reset_session,
    set_confirmed_profile,
)


def test_authenticate_login_id_returns_user():
    result = authenticate_login_id("sample-user")
    assert result is not None
    assert result["user_name"] == "테스트 사용자"


def test_authenticate_login_id_returns_none_for_unknown_user():
    assert authenticate_login_id("unknown-user") is None


def test_authenticated_session_survives_reset():
    user_data = {}
    authenticate_session(user_data, login_id="sample-user", user_name="테스트 사용자")
    assert is_authenticated(user_data) is True
    reset_session(user_data)
    assert is_authenticated(user_data) is True
    assert current_user_name(user_data) == "테스트 사용자"


def test_authenticate_session_resets_failure_count():
    user_data = {}
    increment_auth_failures(user_data)
    increment_auth_failures(user_data)
    authenticate_session(user_data, login_id="sample-user", user_name="테스트 사용자")
    assert auth_failures(user_data) == 0


def test_confirmed_profile_survives_reset():
    user_data = {}
    set_confirmed_profile(user_data, {"name": "홍길동"})
    reset_session(user_data)
    assert confirmed_profile(user_data) == {"name": "홍길동"}
