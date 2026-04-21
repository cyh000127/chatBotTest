from PROJECT.canonical_intents import registry
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT
from PROJECT.rule_engine import classify_step_local_intent_text


def test_profile_confirm_local_rule_maps_positive_text_to_confirm():
    decision = classify_step_local_intent_text("네 맞아요", current_step=STATE_PROFILE_CONFIRM)

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_CONFIRM


def test_profile_confirm_local_rule_maps_edit_text_to_edit():
    decision = classify_step_local_intent_text("아니요 수정할래요", current_step=STATE_PROFILE_CONFIRM)

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_EDIT


def test_profile_edit_select_local_rule_maps_field_name_without_repair_marker():
    decision = classify_step_local_intent_text("생년월일", current_step=STATE_PROFILE_EDIT_SELECT)

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_PROFILE_EDIT_BIRTH_DATE
