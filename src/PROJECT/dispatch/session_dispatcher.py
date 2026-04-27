from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU
from PROJECT.i18n.translator import DEFAULT_LOCALE
from PROJECT.support_handoff import SupportHandoffState, support_handoff_from_dict


def _default_session() -> dict:
    return {
        "started": False,
        "state": STATE_MAIN_MENU,
        "history": [],
        "selected_city": None,
        "fertilizer_draft": None,
        "yield_draft": None,
        "confirmed_fertilizer": None,
        "confirmed_yield": None,
        "pending_slot": None,
        "locale": DEFAULT_LOCALE,
        "authenticated": False,
        "login_id": None,
        "user_name": None,
        "auth_failures": 0,
        "onboarding_session_id": None,
        "onboarding_invite_code": None,
        "onboarding_project_id": None,
        "onboarding_status": None,
        "onboarding_step": None,
        "onboarding_draft": None,
        "field_binding_draft": None,
        "input_resolution_draft": None,
        "recovery_attempts": 0,
        "last_recovery_context": None,
        "pending_repair_confirmation": None,
        "pending_candidate": None,
        "support_handoff": None,
        "active_follow_up_id": None,
        "llm_step_call_counts": {},
        "llm_seen_inputs": {},
    }


def get_session(user_data: dict) -> dict:
    return user_data.setdefault("session", _default_session())


def reset_session(user_data: dict) -> dict:
    started = get_session(user_data).get("started", False) if "session" in user_data else False
    locale = get_session(user_data).get("locale", DEFAULT_LOCALE) if "session" in user_data else DEFAULT_LOCALE
    authenticated = get_session(user_data).get("authenticated", False) if "session" in user_data else False
    login_id = get_session(user_data).get("login_id") if "session" in user_data else None
    user_name = get_session(user_data).get("user_name") if "session" in user_data else None
    onboarding_session_id = get_session(user_data).get("onboarding_session_id") if "session" in user_data else None
    onboarding_invite_code = get_session(user_data).get("onboarding_invite_code") if "session" in user_data else None
    onboarding_project_id = get_session(user_data).get("onboarding_project_id") if "session" in user_data else None
    onboarding_status = get_session(user_data).get("onboarding_status") if "session" in user_data else None
    onboarding_step = get_session(user_data).get("onboarding_step") if "session" in user_data else None
    onboarding_draft = get_session(user_data).get("onboarding_draft") if "session" in user_data else None
    field_binding_draft = get_session(user_data).get("field_binding_draft") if "session" in user_data else None
    input_resolution_draft = get_session(user_data).get("input_resolution_draft") if "session" in user_data else None
    confirmed_fertilizer = get_session(user_data).get("confirmed_fertilizer") if "session" in user_data else None
    confirmed_yield = get_session(user_data).get("confirmed_yield") if "session" in user_data else None
    last_context = get_session(user_data).get("last_recovery_context") if "session" in user_data else None
    user_data["session"] = _default_session()
    user_data["session"]["started"] = started
    user_data["session"]["locale"] = locale
    user_data["session"]["authenticated"] = authenticated
    user_data["session"]["login_id"] = login_id
    user_data["session"]["user_name"] = user_name
    user_data["session"]["onboarding_session_id"] = onboarding_session_id
    user_data["session"]["onboarding_invite_code"] = onboarding_invite_code
    user_data["session"]["onboarding_project_id"] = onboarding_project_id
    user_data["session"]["onboarding_status"] = onboarding_status
    user_data["session"]["onboarding_step"] = onboarding_step
    user_data["session"]["onboarding_draft"] = onboarding_draft
    user_data["session"]["field_binding_draft"] = field_binding_draft
    user_data["session"]["input_resolution_draft"] = input_resolution_draft
    user_data["session"]["confirmed_fertilizer"] = confirmed_fertilizer
    user_data["session"]["confirmed_yield"] = confirmed_yield
    user_data["session"]["last_recovery_context"] = last_context
    return user_data["session"]


def cancel_session(user_data: dict) -> dict:
    session = reset_session(user_data)
    session["state"] = STATE_CANCELLED
    return session


def current_state(user_data: dict) -> str:
    return get_session(user_data)["state"]


def mark_started(user_data: dict) -> None:
    get_session(user_data)["started"] = True


def has_started(user_data: dict) -> bool:
    return bool(get_session(user_data)["started"])


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

def set_fertilizer_draft(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["fertilizer_draft"] = draft


def fertilizer_draft(user_data: dict) -> dict | None:
    return get_session(user_data)["fertilizer_draft"]


def set_yield_draft(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["yield_draft"] = draft


def yield_draft(user_data: dict) -> dict | None:
    return get_session(user_data)["yield_draft"]

def set_confirmed_fertilizer(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["confirmed_fertilizer"] = draft


def confirmed_fertilizer(user_data: dict) -> dict | None:
    return get_session(user_data)["confirmed_fertilizer"]


def has_confirmed_fertilizer(user_data: dict) -> bool:
    return confirmed_fertilizer(user_data) is not None


def set_confirmed_yield(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["confirmed_yield"] = draft


def confirmed_yield(user_data: dict) -> dict | None:
    return get_session(user_data)["confirmed_yield"]


def has_confirmed_yield(user_data: dict) -> bool:
    return confirmed_yield(user_data) is not None


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
    session["started"] = True
    session["authenticated"] = True
    session["login_id"] = login_id
    session["user_name"] = user_name
    session["auth_failures"] = 0


def current_user_name(user_data: dict) -> str | None:
    return get_session(user_data)["user_name"]


def current_login_id(user_data: dict) -> str | None:
    return get_session(user_data)["login_id"]


def set_onboarding_session(
    user_data: dict,
    *,
    onboarding_session_id: str,
    invite_code: str,
    project_id: str | None,
    status: str,
    step: str,
    draft: dict | None = None,
) -> None:
    session = get_session(user_data)
    session["authenticated"] = False
    session["onboarding_session_id"] = onboarding_session_id
    session["onboarding_invite_code"] = invite_code
    session["onboarding_project_id"] = project_id
    session["onboarding_status"] = status
    session["onboarding_step"] = step
    session["onboarding_draft"] = draft


def set_onboarding_progress(
    user_data: dict,
    *,
    status: str,
    step: str,
    draft: dict | None = None,
) -> None:
    session = get_session(user_data)
    session["onboarding_status"] = status
    session["onboarding_step"] = step
    if draft is not None:
        session["onboarding_draft"] = draft


def current_onboarding_session_id(user_data: dict) -> str | None:
    return get_session(user_data).get("onboarding_session_id")


def current_onboarding_status(user_data: dict) -> str | None:
    return get_session(user_data).get("onboarding_status")


def current_onboarding_step(user_data: dict) -> str | None:
    return get_session(user_data).get("onboarding_step")


def onboarding_draft(user_data: dict) -> dict | None:
    return get_session(user_data).get("onboarding_draft")


def clear_onboarding_session(user_data: dict) -> None:
    session = get_session(user_data)
    session["onboarding_session_id"] = None
    session["onboarding_invite_code"] = None
    session["onboarding_project_id"] = None
    session["onboarding_status"] = None
    session["onboarding_step"] = None
    session["onboarding_draft"] = None


def set_field_binding_draft(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["field_binding_draft"] = draft


def field_binding_draft(user_data: dict) -> dict | None:
    return get_session(user_data).get("field_binding_draft")


def clear_field_binding_draft(user_data: dict) -> None:
    get_session(user_data)["field_binding_draft"] = None


def set_input_resolution_draft(user_data: dict, draft: dict | None) -> None:
    get_session(user_data)["input_resolution_draft"] = draft


def input_resolution_draft(user_data: dict) -> dict | None:
    return get_session(user_data).get("input_resolution_draft")


def clear_input_resolution_draft(user_data: dict) -> None:
    get_session(user_data)["input_resolution_draft"] = None


def auth_failures(user_data: dict) -> int:
    return int(get_session(user_data).get("auth_failures", 0))


def increment_auth_failures(user_data: dict) -> int:
    session = get_session(user_data)
    session["auth_failures"] = int(session.get("auth_failures", 0)) + 1
    return session["auth_failures"]


def reset_auth_failures(user_data: dict) -> None:
    get_session(user_data)["auth_failures"] = 0


def recovery_attempts(user_data: dict) -> int:
    return int(get_session(user_data).get("recovery_attempts", 0))


def increment_recovery_attempts(user_data: dict) -> int:
    session = get_session(user_data)
    session["recovery_attempts"] = int(session.get("recovery_attempts", 0)) + 1
    return session["recovery_attempts"]


def reset_recovery_attempts(user_data: dict) -> None:
    get_session(user_data)["recovery_attempts"] = 0


def set_last_recovery_context(user_data: dict, recovery_context: dict | None) -> None:
    get_session(user_data)["last_recovery_context"] = recovery_context


def last_recovery_context(user_data: dict) -> dict | None:
    return get_session(user_data).get("last_recovery_context")


def set_pending_repair_confirmation(user_data: dict, payload: dict | None) -> None:
    get_session(user_data)["pending_repair_confirmation"] = payload


def pending_repair_confirmation(user_data: dict) -> dict | None:
    return get_session(user_data).get("pending_repair_confirmation")


def set_pending_candidate(user_data: dict, payload: dict | None) -> None:
    get_session(user_data)["pending_candidate"] = payload


def pending_candidate(user_data: dict) -> dict | None:
    return get_session(user_data).get("pending_candidate")


def clear_pending_candidate(user_data: dict) -> None:
    set_pending_candidate(user_data, None)


def set_support_handoff(user_data: dict, handoff: SupportHandoffState | dict | None) -> None:
    if isinstance(handoff, SupportHandoffState):
        get_session(user_data)["support_handoff"] = handoff.to_dict()
        return
    get_session(user_data)["support_handoff"] = handoff


def support_handoff(user_data: dict) -> SupportHandoffState | None:
    return support_handoff_from_dict(get_session(user_data).get("support_handoff"))


def has_active_support_handoff(user_data: dict) -> bool:
    handoff = support_handoff(user_data)
    return handoff is not None and not handoff.closed


def clear_support_handoff(user_data: dict) -> None:
    set_support_handoff(user_data, None)
    clear_active_follow_up_id(user_data)


def set_active_follow_up_id(user_data: dict, follow_up_id: str | None) -> None:
    get_session(user_data)["active_follow_up_id"] = follow_up_id


def active_follow_up_id(user_data: dict) -> str | None:
    return get_session(user_data).get("active_follow_up_id")


def clear_active_follow_up_id(user_data: dict) -> None:
    get_session(user_data)["active_follow_up_id"] = None


def llm_calls_in_step(user_data: dict, step: str | None) -> int:
    if step is None:
        return 0
    counts = get_session(user_data).get("llm_step_call_counts", {})
    return int(counts.get(step, 0))


def increment_llm_calls_in_step(user_data: dict, step: str | None) -> int:
    if step is None:
        return 0
    session = get_session(user_data)
    counts = session.setdefault("llm_step_call_counts", {})
    counts[step] = int(counts.get(step, 0)) + 1
    return counts[step]


def has_seen_llm_input(user_data: dict, cache_key: str) -> bool:
    seen_inputs = get_session(user_data).get("llm_seen_inputs", {})
    return bool(seen_inputs.get(cache_key))


def mark_llm_input_seen(user_data: dict, cache_key: str) -> None:
    session = get_session(user_data)
    seen_inputs = session.setdefault("llm_seen_inputs", {})
    seen_inputs[cache_key] = True
