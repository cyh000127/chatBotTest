from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU


def _default_session() -> dict:
    return {
        "state": STATE_MAIN_MENU,
        "history": [],
        "selected_city": None,
        "profile_draft": None,
        "pending_slot": None,
    }


def get_session(user_data: dict) -> dict:
    return user_data.setdefault("session", _default_session())


def reset_session(user_data: dict) -> dict:
    user_data["session"] = _default_session()
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


def set_pending_slot(user_data: dict, pending_slot: str | None) -> None:
    get_session(user_data)["pending_slot"] = pending_slot


def pending_slot(user_data: dict) -> str | None:
    return get_session(user_data)["pending_slot"]
