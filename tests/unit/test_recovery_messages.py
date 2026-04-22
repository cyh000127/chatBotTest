from PROJECT.canonical_intents import registry
from PROJECT.conversations.sample_menu import recovery_messages
from PROJECT.conversations.sample_menu.states import STATE_WEATHER_MENU
from PROJECT.i18n.translator import get_catalog
from PROJECT.rule_engine import RuleSource, ValidationClassification, ValidationResult, assemble_recovery_context


def test_render_fallback_message_appends_current_step_guidance():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_WEATHER_MENU,
        latest_user_message="아무거나 날씨 보여줘",
        locale="ko",
        recovery_attempt_count=1,
        canonical_intent=registry.INTENT_UNKNOWN_TEXT,
        validation_result=ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
        ),
        fallback_key="weather",
        selected_city="서울",
    )

    text = recovery_messages.render_fallback_message(
        fallback_key="weather",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert catalog.FALLBACK_MESSAGES["weather"] in text
    assert catalog.RECOVERY_GUIDANCE_GUIDED in text
    assert "오늘 날씨를 확인할 도시를 선택하세요." in text


def test_render_cheap_gate_message_uses_escalation_guidance_when_context_exists():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_WEATHER_MENU,
        latest_user_message="상담원 연결해줘",
        locale="ko",
        recovery_attempt_count=3,
        canonical_intent=registry.INTENT_UNKNOWN_TEXT,
        validation_result=ValidationResult(
            classification=ValidationClassification.NEEDS_HANDOFF,
            source=RuleSource.CHEAP_GATE,
            reason="explicit_support_request",
            human_handoff_reason="user_requested_human_support",
        ),
        fallback_key="weather",
        selected_city="서울",
    )
    result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="explicit_support_request",
        human_handoff_reason="user_requested_human_support",
    )

    text = recovery_messages.render_cheap_gate_message(
        result=result,
        fallback_key="weather",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert "support.escalate" in text
    assert catalog.RECOVERY_GUIDANCE_ESCALATION_READY in text
    assert "오늘 날씨를 확인할 도시를 선택하세요." in text
