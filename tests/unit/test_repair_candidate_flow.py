from PROJECT.channels.telegram.handlers.messages import llm_repair_guidance_text, parse_candidate_changes
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_AMOUNT
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_BIRTH_YEAR
from PROJECT.conversations.sample_menu.keyboards import repair_confirmation_keyboard
from PROJECT.i18n.translator import get_catalog
from PROJECT.llm import LlmEditAction, LlmEditIntentResult


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
