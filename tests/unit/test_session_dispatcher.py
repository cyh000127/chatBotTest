from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.dispatch.session_dispatcher import (
    auth_failures,
    cancel_session,
    confirmed_yield,
    current_state,
    go_back,
    has_confirmed_yield,
    has_active_support_handoff,
    has_seen_llm_input,
    increment_llm_calls_in_step,
    increment_auth_failures,
    llm_calls_in_step,
    last_recovery_context,
    mark_llm_input_seen,
    pending_candidate,
    pending_repair_confirmation,
    reset_session,
    set_support_handoff,
    set_last_recovery_context,
    set_pending_candidate,
    set_pending_repair_confirmation,
    set_confirmed_yield,
    set_state,
    set_yield_draft,
    support_handoff,
    yield_draft,
)
from PROJECT.support_handoff import SupportHandoffStatus, new_support_handoff


def test_reset_session_sets_main_menu():
    user_data = {}
    reset_session(user_data)
    assert current_state(user_data) == STATE_MAIN_MENU


def test_set_state_pushes_history_and_go_back_returns_previous_state():
    user_data = {}
    reset_session(user_data)
    set_state(user_data, STATE_LANGUAGE_SELECT, push_history=True)
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
def test_yield_draft_and_confirmed_helpers_work():
    user_data = {}
    set_yield_draft(user_data, {"field_name": "A-1"})
    set_confirmed_yield(user_data, {"field_name": "A-1"})

    assert yield_draft(user_data) == {"field_name": "A-1"}
    assert has_confirmed_yield(user_data) is True
    assert confirmed_yield(user_data) == {"field_name": "A-1"}


def test_last_recovery_context_is_preserved_across_reset_session():
    user_data = {}
    set_last_recovery_context(user_data, {"current_step": "main_menu"})
    reset_session(user_data)

    assert last_recovery_context(user_data) == {"current_step": "main_menu"}


def test_pending_repair_confirmation_helper_works():
    user_data = {}
    payload = {"domain": "fertilizer", "target_state": "fertilizer_product"}

    set_pending_repair_confirmation(user_data, payload)

    assert pending_repair_confirmation(user_data) == payload


def test_pending_candidate_helper_works():
    user_data = {}
    payload = {"domain": "fertilizer", "target_state": "fertilizer_product", "candidate_value": "한아름"}

    set_pending_candidate(user_data, payload)

    assert pending_candidate(user_data) == payload


def test_reset_session_clears_pending_candidate():
    user_data = {}
    set_pending_candidate(user_data, {"candidate_value": "한아름"})

    reset_session(user_data)

    assert pending_candidate(user_data) is None


def test_support_handoff_helper_stores_contract_payload():
    user_data = {}
    handoff = new_support_handoff(
        handoff_id="handoff-test",
        route_hint="support.escalate",
        reason="explicit_support_request",
        current_step=STATE_MAIN_MENU,
        recent_messages_summary="state=main_menu",
        failure_count=1,
        user_message="관리자 연결해주세요",
    )

    set_support_handoff(user_data, handoff)

    stored = support_handoff(user_data)
    assert stored is not None
    assert stored.handoff_id == "handoff-test"
    assert stored.status == SupportHandoffStatus.WAITING_ADMIN_REPLY
    assert stored.route_hint == "support.escalate"
    assert stored.awaiting_admin_reply is True
    assert stored.user_messages == ("관리자 연결해주세요",)
    assert has_active_support_handoff(user_data) is True


def test_reset_session_clears_support_handoff_contract():
    user_data = {}
    set_support_handoff(
        user_data,
        new_support_handoff(
            route_hint="support.escalate",
            reason="explicit_support_request",
            current_step=STATE_MAIN_MENU,
        ),
    )

    reset_session(user_data)

    assert support_handoff(user_data) is None
    assert has_active_support_handoff(user_data) is False


def test_llm_step_call_counter_tracks_per_step():
    user_data = {}

    increment_llm_calls_in_step(user_data, "fertilizer_confirm")
    increment_llm_calls_in_step(user_data, "fertilizer_confirm")

    assert llm_calls_in_step(user_data, "fertilizer_confirm") == 2
    assert llm_calls_in_step(user_data, "profile_confirm") == 0


def test_llm_seen_input_tracking_marks_cache_key():
    user_data = {}
    cache_key = "ko:fertilizer_confirm:제품명수정할래"

    assert has_seen_llm_input(user_data, cache_key) is False

    mark_llm_input_seen(user_data, cache_key)

    assert has_seen_llm_input(user_data, cache_key) is True
