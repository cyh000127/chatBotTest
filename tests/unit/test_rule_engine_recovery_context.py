from PROJECT.canonical_intents import registry
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.yield_intake.states import STATE_YIELD_AMOUNT
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM
from PROJECT.conversations.sample_menu.states import STATE_WEATHER_MENU
from PROJECT.rule_engine import ValidationClassification, assemble_recovery_context
from PROJECT.rule_engine.contracts import RuleSource, ValidationResult


def test_assemble_recovery_context_for_weather_menu():
    validation_result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="recovery_retry_limit_exceeded",
        human_handoff_reason="cheap_gate_retry_limit",
    )

    context = assemble_recovery_context(
        current_step=STATE_WEATHER_MENU,
        latest_user_message="날씨 그냥 알아서 보여줘",
        locale="ko",
        recovery_attempt_count=3,
        canonical_intent=registry.INTENT_UNKNOWN_TEXT,
        validation_result=validation_result,
        fallback_key="weather",
        selected_city="서울",
    )

    assert context.current_step == STATE_WEATHER_MENU
    assert context.expected_input_type == "city_selection"
    assert context.allowed_value_shape == "one_of:supported_weather_city"
    assert context.recovery_attempt_count == 3
    assert context.metadata["fallback_key"] == "weather"
    assert context.metadata["validation_reason"] == "recovery_retry_limit_exceeded"
    assert "selected_city=서울" in context.recent_messages_summary


def test_assemble_recovery_context_for_profile_confirm_includes_draft_summary():
    draft = profile_service.update_draft(
        profile_service.new_draft(),
        name="최윤혁",
        residence="서울",
        city="서울특별시",
        district="강남구",
        birth_year=1999,
        birth_month=9,
        birth_day=17,
    )
    validation_result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="explicit_support_request",
        human_handoff_reason="user_requested_human_support",
    )

    context = assemble_recovery_context(
        current_step=STATE_PROFILE_CONFIRM,
        latest_user_message="프로필 이거 사람한테 물어보고 싶어요",
        locale="ko",
        recovery_attempt_count=1,
        canonical_intent=registry.INTENT_UNKNOWN_TEXT,
        validation_result=validation_result,
        fallback_key="profile_confirm",
        profile_draft_data=draft.to_dict(),
        pending_slot=None,
    )

    assert context.expected_input_type == "confirmation_action"
    assert context.allowed_value_shape == "one_of:confirm|edit"
    assert "all_profile_fields_must_be_present_before_finalize" in context.hard_constraints
    assert "profile_draft_fields=name,residence,city,district,birth_date" in context.recent_messages_summary
    assert "- 이름: 최윤혁" in context.current_question


def test_assemble_recovery_context_for_yield_step_uses_shared_schema():
    validation_result = ValidationResult(
        classification=ValidationClassification.REASK,
        source=RuleSource.CHEAP_GATE,
        reason="structured_step_mismatch",
    )

    context = assemble_recovery_context(
        current_step=STATE_YIELD_AMOUNT,
        latest_user_message="세 포대쯤 돼요",
        locale="ko",
        recovery_attempt_count=2,
        canonical_intent=registry.INTENT_YIELD_INPUT_START,
        validation_result=validation_result,
        fallback_key="default",
    )

    assert context.current_step == STATE_YIELD_AMOUNT
    assert context.expected_input_type == "yield_amount"
    assert context.allowed_value_shape == "numeric_or_numeric_with_supported_unit"
    assert "yield_amount_requires_supported_unit_or_default_kg" in context.hard_constraints
    assert "수확량을 입력해주세요" in context.current_question
