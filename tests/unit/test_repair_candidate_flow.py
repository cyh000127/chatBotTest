from types import SimpleNamespace

from PROJECT.channels.telegram.handlers.messages import (
    FERTILIZER_REPAIR_ALLOWED_ACTIONS,
    PROFILE_REPAIR_ALLOWED_ACTIONS,
    llm_edit_intent_policy_enabled,
    llm_repair_guidance_text,
    parse_candidate_changes,
    repair_allowed_actions,
)
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_AMOUNT, STATE_FERTILIZER_CONFIRM, STATE_FERTILIZER_PRODUCT
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_BIRTH_YEAR, STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT, STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu.keyboards import repair_confirmation_keyboard
from PROJECT.dispatch.session_dispatcher import pending_candidate, pending_repair_confirmation, set_pending_candidate, set_pending_repair_confirmation
from PROJECT.i18n.translator import get_catalog
from PROJECT.llm import LlmEditAction, LlmEditIntentResult
from PROJECT.policy import UnknownInputDisposition, classify_unknown_input_disposition


def test_repair_confirmation_keyboard_switches_to_candidate_buttons():
    catalog = get_catalog("ko")

    layout = repair_confirmation_keyboard(
        "fertilizer",
        "confirmed",
        STATE_FERTILIZER_AMOUNT,
        catalog,
        has_candidate=True,
    )

    assert layout[0][0]["text"] == catalog.BUTTON_APPLY_SUGGESTED_VALUE
    assert layout[1][0]["text"] == catalog.BUTTON_ENTER_VALUE_DIRECTLY


def test_parse_profile_birth_candidate_changes():
    changes = parse_candidate_changes("profile", STATE_PROFILE_BIRTH_YEAR, "1998년 4월 20일")

    assert changes == {
        "birth_year": 1998,
        "birth_month": 4,
        "birth_day": 20,
    }


def test_parse_fertilizer_amount_candidate_changes():
    changes = parse_candidate_changes("fertilizer", STATE_FERTILIZER_AMOUNT, "20kg")

    assert changes == {
        "amount_value": 20.0,
        "amount_unit": "kg",
    }


def test_parse_candidate_changes_returns_none_for_invalid_value():
    assert parse_candidate_changes("fertilizer", STATE_FERTILIZER_AMOUNT, "많이") is None


def test_llm_repair_guidance_text_for_unsupported_result():
    catalog = get_catalog("ko")
    result = LlmEditIntentResult(
        action=LlmEditAction.UNSUPPORTED,
        confidence=0.91,
    )

    text = llm_repair_guidance_text(result, catalog)

    assert text == catalog.LLM_REPAIR_UNSUPPORTED_MESSAGE


def test_llm_repair_guidance_text_for_low_confidence_result():
    catalog = get_catalog("ko")
    result = LlmEditIntentResult(
        action=LlmEditAction.FERTILIZER_EDIT_PRODUCT,
        confidence=0.4,
    )

    text = llm_repair_guidance_text(result, catalog)

    assert text == catalog.LLM_REPAIR_LOW_CONFIDENCE_MESSAGE


def test_llm_repair_guidance_text_for_human_review_result():
    catalog = get_catalog("ko")
    result = LlmEditIntentResult(
        action=LlmEditAction.FERTILIZER_EDIT_PRODUCT,
        confidence=0.95,
        needs_human=True,
    )

    text = llm_repair_guidance_text(result, catalog)

    assert text == catalog.LLM_REPAIR_HUMAN_REVIEW_MESSAGE


def test_llm_edit_intent_policy_enabled_requires_explicit_flag():
    disabled_context = SimpleNamespace(bot_data={"settings": SimpleNamespace(enable_llm_edit_intent=False)})
    enabled_context = SimpleNamespace(bot_data={"settings": SimpleNamespace(enable_llm_edit_intent=True)})

    assert llm_edit_intent_policy_enabled(disabled_context) is False
    assert llm_edit_intent_policy_enabled(enabled_context) is True


def test_repair_allowed_actions_are_centralized_by_domain():
    assert repair_allowed_actions("profile") == PROFILE_REPAIR_ALLOWED_ACTIONS
    assert repair_allowed_actions("fertilizer") == FERTILIZER_REPAIR_ALLOWED_ACTIONS


def test_unknown_repair_policy_is_centralized_in_ai_policy():
    assert classify_unknown_input_disposition(
        current_step=STATE_PROFILE_CONFIRM,
        domain_hint="profile",
        use_confirmed=False,
    ) == UnknownInputDisposition.REPAIR_ASSIST_ALLOWED
    assert classify_unknown_input_disposition(
        current_step=STATE_PROFILE_EDIT_SELECT,
        domain_hint="profile",
        use_confirmed=False,
    ) == UnknownInputDisposition.REPAIR_ASSIST_ALLOWED
    assert classify_unknown_input_disposition(
        current_step=STATE_PROFILE_NAME,
        domain_hint="profile",
        use_confirmed=False,
    ) == UnknownInputDisposition.FALLBACK_ONLY
    assert classify_unknown_input_disposition(
        current_step=STATE_FERTILIZER_CONFIRM,
        domain_hint="fertilizer",
        use_confirmed=False,
    ) == UnknownInputDisposition.REPAIR_ASSIST_ALLOWED
    assert classify_unknown_input_disposition(
        current_step=STATE_FERTILIZER_PRODUCT,
        domain_hint="fertilizer",
        use_confirmed=False,
    ) == UnknownInputDisposition.FALLBACK_ONLY
    assert classify_unknown_input_disposition(
        current_step=STATE_FERTILIZER_PRODUCT,
        domain_hint="fertilizer",
        use_confirmed=True,
    ) == UnknownInputDisposition.REPAIR_ASSIST_ALLOWED


def test_pending_candidate_is_stored_separately_from_repair_confirmation():
    user_data = {}
    set_pending_repair_confirmation(user_data, {"domain": "fertilizer", "target_state": STATE_FERTILIZER_AMOUNT, "has_candidate": True})
    set_pending_candidate(user_data, {"domain": "fertilizer", "target_state": STATE_FERTILIZER_AMOUNT, "candidate_value": "20kg"})

    assert pending_repair_confirmation(user_data) == {
        "domain": "fertilizer",
        "target_state": STATE_FERTILIZER_AMOUNT,
        "has_candidate": True,
    }
    assert pending_candidate(user_data) == {
        "domain": "fertilizer",
        "target_state": STATE_FERTILIZER_AMOUNT,
        "candidate_value": "20kg",
    }
