from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU
from PROJECT.i18n.translator import DEFAULT_LOCALE


def _default_session() -> dict:
    return {
        "state": STATE_MAIN_MENU,
        "history": [],
        "selected_city": None,
        "profile_draft": None,
        "confirmed_profile": None,
        "pending_slot": None,
        "locale": DEFAULT_LOCALE,
        "authenticated": False,
        "login_id": None,
        "user_name": None,
        "auth_failures": 0,
    }


def get_session(user_data: dict) -> dict:
    return user_data.setdefault("session", _default_session())


def reset_session(user_data: dict) -> dict:
    locale = get_session(user_data).get("locale", DEFAULT_LOCALE) if "session" in user_data else DEFAULT_LOCALE
    authenticated = get_session(user_data).get("authenticated", False) if "session" in user_data else False
    login_id = get_session(user_data).get("login_id") if "session" in user_data else None
    user_name = get_session(user_data).get("user_name") if "session" in user_data else None
    confirmed_profile = get_session(user_data).get("confirmed_profile") if "session" in user_data else None
    user_data["session"] = _default_session()
    user_data["session"]["locale"] = locale
    user_data["session"]["authenticated"] = authenticated
    user_data["session"]["login_id"] = login_id
    user_data["session"]["user_name"] = user_name
    user_data["session"]["confirmed_profile"] = confirmed_profile
    return user_data["session"]


def cancel_session(user_data: dict) -> dict:
    session = reset_session(user_data)
    session["state"] = STATE_CANCELLED
    return session


def current_state(user_data: dict) -> str:
    return get_session(user_data)["state"]


def set_state(user_data: dict, new_state: str, *, push_history: bool = False) -> dict:
    session = get_session(user_data)
    current = session["state"]
    if push_history and current != new_state:
        session["history"].append(current)
    session["state"] = new_state
    return session


def go_back(user_data: dict) -> str | None:
    session = get_session(user_data)
    if not session["history"]:
        return None
    previous_state = session["history"].pop()
    session["state"] = previous_state
    return previous_state


def set_selected_city(user_data: dict, city: str) -> None:
    get_session(user_data)["selected_city"] = city


def selected_city(user_data: dict) -> str | None:
    return get_session(user_data)["selected_city"]


def set_profile_draft(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["profile_draft"] = draft


def profile_draft(user_data: dict) -> dict | None:
    return get_session(user_data)["profile_draft"]


def set_confirmed_profile(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["confirmed_profile"] = draft


def confirmed_profile(user_data: dict) -> dict | None:
    return get_session(user_data)["confirmed_profile"]


def has_confirmed_profile(user_data: dict) -> bool:
    return confirmed_profile(user_data) is not None


def set_pending_slot(user_data: dict, pending_slot: str | None) -> None:
    get_session(user_data)["pending_slot"] = pending_slot


def pending_slot(user_data: dict) -> str | None:
    return get_session(user_data)["pending_slot"]


def set_locale(user_data: dict, locale: str) -> None:
    get_session(user_data)["locale"] = locale


def current_locale(user_data: dict) -> str:
    return get_session(user_data)["locale"]


def is_authenticated(user_data: dict) -> bool:
    return bool(get_session(user_data)["authenticated"])


def authenticate_session(user_data: dict, *, login_id: str, user_name: str) -> None:
    session = get_session(user_data)
    session["authenticated"] = True
    session["login_id"] = login_id
    session["user_name"] = user_name
    session["auth_failures"] = 0


def current_user_name(user_data: dict) -> str | None:
    return get_session(user_data)["user_name"]


def current_login_id(user_data: dict) -> str | None:
    return get_session(user_data)["login_id"]


def auth_failures(user_data: dict) -> int:
    return int(get_session(user_data).get("auth_failures", 0))


def increment_auth_failures(user_data: dict) -> int:
    session = get_session(user_data)
    session["auth_failures"] = int(session.get("auth_failures", 0)) + 1
    return session["auth_failures"]


def reset_auth_failures(user_data: dict) -> None:
    get_session(user_data)["auth_failures"] = 0
