import pytest

from PROJECT.policy import (
    MAX_LLM_CALLS_PER_CONFIRM_STEP,
    AiMode,
    ai_mode_allows_edit_intent,
    ai_mode_allows_recovery_assist,
    can_invoke_llm,
    parse_ai_mode,
    same_input_cache_key,
    should_handoff,
)


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
