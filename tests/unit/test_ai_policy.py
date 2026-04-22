import pytest

from PROJECT.policy import (
    MAX_LLM_CALLS_PER_CONFIRM_STEP,
    AiMode,
    HandoffRoute,
    UnknownInputDisposition,
    ai_mode_allows_edit_intent,
    ai_mode_allows_recovery_assist,
    can_invoke_llm,
    classify_handoff_route,
    classify_unknown_input_disposition,
    parse_ai_mode,
    same_input_cache_key,
    should_handoff,
)
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT, STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU


def test_parse_ai_mode_defaults_to_disabled():
    assert parse_ai_mode("") == AiMode.DISABLED


def test_parse_ai_mode_rejects_unknown_value():
    with pytest.raises(ValueError):
        parse_ai_mode("unknown-mode")


def test_ai_mode_allows_only_the_expected_invocation_type():
    assert ai_mode_allows_edit_intent(AiMode.REPAIR_ASSIST_ONLY) is True
    assert ai_mode_allows_edit_intent(AiMode.RECOVERY_ASSIST_ONLY) is False
    assert ai_mode_allows_recovery_assist(AiMode.RECOVERY_ASSIST_ONLY) is True
    assert ai_mode_allows_recovery_assist(AiMode.REPAIR_ASSIST_ONLY) is False


def test_can_invoke_llm_allows_repair_in_confirm_step():
    allowed = can_invoke_llm(
        ai_mode=AiMode.REPAIR_ASSIST_ONLY,
        invocation_type="repair",
        current_step="fertilizer_confirm",
        is_structured_step=False,
        is_confirm_step=True,
        is_free_text=True,
        llm_calls_in_step=0,
        same_input_seen=False,
    )

    assert allowed is True


def test_can_invoke_llm_blocks_repeat_input_and_limit_overflow():
    repeated = can_invoke_llm(
        ai_mode=AiMode.REPAIR_ASSIST_ONLY,
        invocation_type="repair",
        current_step="fertilizer_confirm",
        is_structured_step=False,
        is_confirm_step=True,
        is_free_text=True,
        llm_calls_in_step=0,
        same_input_seen=True,
    )
    over_limit = can_invoke_llm(
        ai_mode=AiMode.REPAIR_ASSIST_ONLY,
        invocation_type="repair",
        current_step="fertilizer_confirm",
        is_structured_step=False,
        is_confirm_step=True,
        is_free_text=True,
        llm_calls_in_step=MAX_LLM_CALLS_PER_CONFIRM_STEP,
        same_input_seen=False,
    )

    assert repeated is False
    assert over_limit is False


def test_same_input_cache_key_includes_locale_and_step():
    key = same_input_cache_key(normalized_text="제품명수정할래", current_step="fertilizer_confirm", locale="ko")

    assert key == "ko:fertilizer_confirm:제품명수정할래"


def test_should_handoff_after_retry_limit():
    assert should_handoff(recovery_attempt_count=3) is True


def test_unknown_input_disposition_allows_profile_and_fertilizer_confirm_contexts():
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
        current_step=STATE_FERTILIZER_CONFIRM,
        domain_hint="fertilizer",
        use_confirmed=False,
    ) == UnknownInputDisposition.REPAIR_ASSIST_ALLOWED


def test_unknown_input_disposition_stays_fallback_only_outside_confirm_context():
    assert classify_unknown_input_disposition(
        current_step=STATE_PROFILE_NAME,
        domain_hint="profile",
        use_confirmed=False,
    ) == UnknownInputDisposition.FALLBACK_ONLY
    assert classify_unknown_input_disposition(
        current_step=STATE_MAIN_MENU,
        domain_hint=None,
        use_confirmed=False,
    ) == UnknownInputDisposition.FALLBACK_ONLY


def test_unknown_input_disposition_allows_confirmed_snapshot_repair():
    disposition = classify_unknown_input_disposition(
        current_step=STATE_MAIN_MENU,
        domain_hint="fertilizer",
        use_confirmed=True,
    )

    assert disposition == UnknownInputDisposition.REPAIR_ASSIST_ALLOWED


def test_unknown_input_disposition_marks_support_requests_as_handoff():
    disposition = classify_unknown_input_disposition(
        current_step=STATE_MAIN_MENU,
        domain_hint="profile",
        validation_reason="explicit_support_request",
    )

    assert disposition == UnknownInputDisposition.HANDOFF_REQUIRED


def test_classify_handoff_route_maps_operational_vocabularies():
    assert classify_handoff_route(reason="explicit_support_request", source="cheap_gate") == HandoffRoute.SUPPORT_ESCALATE
    assert classify_handoff_route(reason="manual_handoff_request", source="cheap_gate") == HandoffRoute.ADMIN_FOLLOWUP_REQUIRED
    assert classify_handoff_route(reason="recovery_retry_limit_exceeded", source="cheap_gate") == HandoffRoute.MANUAL_REVIEW_REQUIRED
    assert classify_handoff_route(reason="needs_human", source="llm_repair") == HandoffRoute.MANUAL_REVIEW_REQUIRED
