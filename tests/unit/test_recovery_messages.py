from PROJECT.canonical_intents import registry
from PROJECT.conversations.evidence_submission.states import STATE_EVIDENCE_WAITING_DOCUMENT
from PROJECT.conversations.field_binding.states import STATE_FIELD_BINDING_CODE
from PROJECT.conversations.input_resolve.states import STATE_INPUT_RESOLVE_RAW_INPUT
from PROJECT.conversations.sample_menu import recovery_messages
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_KIND
from PROJECT.i18n.translator import get_catalog
from PROJECT.rule_engine import RuleSource, ValidationClassification, ValidationResult, assemble_recovery_context


def test_render_fallback_message_appends_current_step_guidance():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_CANCELLED,
        latest_user_message="아무거나",
        locale="ko",
        recovery_attempt_count=1,
        canonical_intent=registry.INTENT_UNKNOWN_TEXT,
        validation_result=ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
        ),
        fallback_key="cancelled",
    )

    text = recovery_messages.render_fallback_message(
        fallback_key="cancelled",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert catalog.FALLBACK_MESSAGES["cancelled"] in text
    assert catalog.RECOVERY_GUIDANCE_GUIDED in text
    assert "현재 흐름이 종료되었습니다." in text


def test_render_cheap_gate_message_uses_escalation_guidance_when_context_exists():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_CANCELLED,
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
        fallback_key="cancelled",
    )
    result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="explicit_support_request",
        human_handoff_reason="user_requested_human_support",
    )

    text = recovery_messages.render_cheap_gate_message(
        result=result,
        fallback_key="cancelled",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert "지원 이관" in text
    assert "이 대화창" in text
    assert catalog.RECOVERY_GUIDANCE_ESCALATION_READY in text
    assert "현재 흐름이 종료되었습니다." in text


def test_render_fallback_message_includes_step_and_input_mode_hint_for_structured_step():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_FERTILIZER_KIND,
        latest_user_message="그냥 바꿔줘",
        locale="ko",
        recovery_attempt_count=2,
        canonical_intent=registry.INTENT_AGRI_INPUT_START,
        validation_result=ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
        ),
        fallback_key="fertilizer_input",
    )

    text = recovery_messages.render_fallback_message(
        fallback_key="fertilizer_input",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert "현재 단계: 2/5" in text
    assert catalog.RECOVERY_BUTTON_ONLY_HINT in text
    assert "비료 유형을 선택하세요." in text
    assert catalog.FERTILIZER_KIND_FALLBACK in text
    assert f"{catalog.RECOVERY_QUICK_ACTIONS_LABEL}: [{catalog.BUTTON_FERTILIZER_KIND_COMPOUND}]" in text


def test_render_fallback_message_includes_fast_path_for_myfields_code_step():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_FIELD_BINDING_CODE,
        latest_user_message="뭔지 모르겠어",
        locale="ko",
        recovery_attempt_count=2,
        canonical_intent=registry.INTENT_FIELD_LIST,
        validation_result=ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
        ),
        fallback_key="myfields_input",
    )

    text = recovery_messages.render_fallback_message(
        fallback_key="myfields_input",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert catalog.MYFIELDS_CODE_PROMPT in text
    assert f"{catalog.RECOVERY_QUICK_ACTIONS_LABEL}: [{catalog.BUTTON_FIELD_LOOKUP_LOCATION}]" in text


def test_render_fallback_message_includes_fast_path_for_input_resolve_raw_input():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_INPUT_RESOLVE_RAW_INPUT,
        latest_user_message="그냥 알아서 해줘",
        locale="ko",
        recovery_attempt_count=2,
        canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
        validation_result=ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
        ),
        fallback_key="input_resolve_input",
    )

    text = recovery_messages.render_fallback_message(
        fallback_key="input_resolve_input",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert catalog.INPUT_RESOLVE_RAW_INPUT_FALLBACK in text
    assert f"{catalog.RECOVERY_QUICK_ACTIONS_LABEL}: [{catalog.BUTTON_BACK}], [{catalog.BUTTON_CANCEL}]" in text


def test_render_fallback_message_includes_fast_path_for_evidence_document_step():
    catalog = get_catalog("ko")
    recovery_context = assemble_recovery_context(
        current_step=STATE_EVIDENCE_WAITING_DOCUMENT,
        latest_user_message="사진 보냄",
        locale="ko",
        recovery_attempt_count=2,
        canonical_intent=registry.INTENT_EVIDENCE_SUBMISSION_START,
        validation_result=ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
        ),
        fallback_key="evidence_input",
        evidence_submission_draft_data={
            "request_event_id": "request-1",
            "session_id": "session-1",
            "request_type_code": "field_photo",
            "field_label": "FIELD-001",
            "accepted_location": True,
        },
    )

    text = recovery_messages.render_fallback_message(
        fallback_key="evidence_input",
        catalog=catalog,
        recovery_context=recovery_context,
    )

    assert catalog.EVIDENCE_DOCUMENT_FALLBACK in text
    assert f"{catalog.RECOVERY_QUICK_ACTIONS_LABEL}: [{catalog.BUTTON_SUPPORT}], [{catalog.BUTTON_BACK}], [{catalog.BUTTON_CANCEL}]" in text
