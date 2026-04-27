from PROJECT.canonical_intents import registry
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_USED
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.conversations.yield_intake.states import STATE_YIELD_CONFIRM, STATE_YIELD_EDIT_SELECT, STATE_YIELD_READY
from PROJECT.dispatch.command_router import (
    ROUTE_FERTILIZER_FINALIZE,
    ROUTE_OPEN_FERTILIZER,
    ROUTE_OPEN_INPUT_RESOLVE,
    ROUTE_OPEN_MYFIELDS,
    ROUTE_OPEN_YIELD,
    ROUTE_YIELD_EDIT,
    ROUTE_SUPPORT_GUIDANCE,
    ROUTE_UNKNOWN_INPUT,
    route_message,
)

def test_removed_profile_like_intent_stays_unknown_from_main_menu():
    decision = route_message(STATE_MAIN_MENU, "profile")
    assert decision.route == ROUTE_UNKNOWN_INPUT


def test_fertilizer_entry_routes_to_fertilizer_input():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_AGRI_INPUT_START)
    assert decision.route == ROUTE_OPEN_FERTILIZER
    assert decision.next_state == STATE_FERTILIZER_USED


def test_myfields_entry_routes_to_self_lookup_entry():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_FIELD_LIST)
    assert decision.route == ROUTE_OPEN_MYFIELDS


def test_yield_entry_routes_to_yield_input():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_YIELD_INPUT_START)
    assert decision.route == ROUTE_OPEN_YIELD
    assert decision.next_state == STATE_YIELD_READY


def test_input_resolve_entry_routes_to_resolve_entry():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_INPUT_RESOLVE_START)
    assert decision.route == ROUTE_OPEN_INPUT_RESOLVE


def test_support_entry_routes_to_support_guidance():
    decision = route_message(STATE_MAIN_MENU, registry.INTENT_SUPPORT_ESCALATE)
    assert decision.route == ROUTE_SUPPORT_GUIDANCE


def test_yield_confirm_edit_routes_to_edit_selection_entry():
    decision = route_message(STATE_YIELD_CONFIRM, registry.INTENT_EDIT)
    assert decision.route == ROUTE_YIELD_EDIT
    assert decision.next_state == STATE_YIELD_EDIT_SELECT
    assert decision.push_history is True


def test_fertilizer_confirm_routes_to_finalize():
    decision = route_message(STATE_FERTILIZER_CONFIRM, registry.INTENT_CONFIRM)
    assert decision.route == ROUTE_FERTILIZER_FINALIZE
