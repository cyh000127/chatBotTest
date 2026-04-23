from types import SimpleNamespace

from PROJECT.canonical_intents import registry
from PROJECT.channels.telegram.handlers.messages import (
    extract_fertilizer_multi_slot_candidate_changes,
    logical_slot_count,
    repair_candidate_preview_text,
)
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_NAME
from PROJECT.conversations.sample_menu.keyboards import fallback_keyboard_layout_for_state
from PROJECT.conversations.sample_menu.recovery_messages import render_cheap_gate_message, render_fallback_message
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED
from PROJECT.dispatch.session_dispatcher import set_confirmed_fertilizer, set_locale
from PROJECT.i18n.translator import get_catalog
from PROJECT.rule_engine import RuleSource, ValidationClassification, ValidationResult, assemble_recovery_context


def test_cancelled_repeated_failure_recovery_scenario_shows_escalation_guidance():
    catalog = get_catalog("ko")
    validation_result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="recovery_retry_limit_exceeded",
        human_handoff_reason="cheap_gate_retry_limit",
    )
    recovery_context = assemble_recovery_context(
        current_step=STATE_CANCELLED,
        latest_user_message="그냥 알아서 해줘",
        locale="ko",
        recovery_attempt_count=3,
        canonical_intent=registry.INTENT_UNKNOWN_TEXT,
        validation_result=validation_result,
        fallback_key="cancelled",
    )

    text = render_cheap_gate_message(
        result=validation_result,
        fallback_key="cancelled",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert "수동 해결" in text
    assert "운영 검토" in text
    assert catalog.RECOVERY_GUIDANCE_ESCALATION_READY in text
    assert "지금 흐름을 멈췄어요." in text


def test_profile_input_fallback_scenario_keeps_current_step_navigation():
    catalog = get_catalog("ko")

    layout = fallback_keyboard_layout_for_state(STATE_PROFILE_NAME, catalog)
    text = render_fallback_message(
        fallback_key="profile_input",
        catalog=catalog,
    )

    assert layout[0][0]["text"] == catalog.BUTTON_BACK
    assert layout[1][0]["text"] == catalog.BUTTON_RESTART
    assert "프로필 입력을 바로 처리하지 못했어요." in text


def test_fertilizer_confirm_fallback_scenario_exposes_direct_edit_fast_path():
    catalog = get_catalog("ko")

    layout = fallback_keyboard_layout_for_state(STATE_FERTILIZER_CONFIRM, catalog)

    assert layout[0][0]["text"] == catalog.BUTTON_CONFIRM
    assert layout[1][0]["text"] == catalog.BUTTON_FERTILIZER_EDIT_USED
    assert layout[2][0]["text"] == catalog.BUTTON_FERTILIZER_EDIT_PRODUCT


def test_fertilizer_confirm_multi_slot_recovery_scenario_builds_summary_candidate():
    context = SimpleNamespace(user_data={})
    set_locale(context.user_data, "ko")
    set_confirmed_fertilizer(
        context.user_data,
        {
            "used": True,
            "kind": "compound",
            "product_name": "기존 비료",
            "amount_value": 20.0,
            "amount_unit": "kg",
            "applied_date": "2026-04-21",
        },
    )

    changes = extract_fertilizer_multi_slot_candidate_changes("액비 15kg 어제 사용했어요")
    text = repair_candidate_preview_text(
        context,
        domain="fertilizer",
        target_state=STATE_FERTILIZER_CONFIRM,
        changes=changes,
        use_confirmed=True,
    )

    assert changes is not None
    assert logical_slot_count(changes) >= 3
    assert "여러 후보 값을 찾았어요" in text
    assert "현재 저장된 비료 입력입니다." in text
    assert "액비" in text
