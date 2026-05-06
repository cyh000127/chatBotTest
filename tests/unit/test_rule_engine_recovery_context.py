from PROJECT.canonical_intents import registry
from PROJECT.conversations.evidence_submission import service as evidence_service
from PROJECT.conversations.evidence_submission.states import STATE_EVIDENCE_WAITING_DOCUMENT
from PROJECT.conversations.yield_intake.states import STATE_YIELD_AMOUNT
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU
from PROJECT.rule_engine import ValidationClassification, assemble_recovery_context
from PROJECT.rule_engine.contracts import RuleSource, ValidationResult


def test_assemble_recovery_context_for_main_menu():
    validation_result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="recovery_retry_limit_exceeded",
        human_handoff_reason="cheap_gate_retry_limit",
    )

    context = assemble_recovery_context(
        current_step=STATE_MAIN_MENU,
        latest_user_message="그냥 알아서 해줘",
        locale="ko",
        recovery_attempt_count=3,
        canonical_intent=registry.INTENT_UNKNOWN_TEXT,
        validation_result=validation_result,
        fallback_key="default",
    )

    assert context.current_step == STATE_MAIN_MENU
    assert context.expected_input_type == "menu_selection"
    assert context.allowed_value_shape == "one_of:fertilizer|yield|myfields|input_resolve|support|help|restart|cancel|language"
    assert context.recovery_attempt_count == 3
    assert context.metadata["runtime_policy_scope"] == "subordinate_guidance"
    assert context.metadata["fallback_key"] == "default"
    assert context.metadata["validation_reason"] == "recovery_retry_limit_exceeded"
    assert context.metadata["ux_recovery_reason"] == "repeated_failure"
    assert context.metadata["ux_next_action_hint"] == "offer_safe_exit"
    assert context.metadata["recovery_policy_level"] == "escalation_ready"
    assert context.metadata["recovery_should_offer_safe_exit"] is True
    assert context.metadata["recovery_should_prioritize_buttons"] is True
    assert context.metadata["recovery_domain"] == "menu"
    assert context.metadata["recovery_task_hint"] == "main_menu_selection"
    assert context.metadata["recovery_resume_action"] == "choose_menu_action"
    assert context.metadata["recovery_focus_target"] == "menu_action"
    assert context.metadata["runtime_handoff_reason_hint"] == "cheap_gate_retry_limit"
    assert context.metadata["runtime_handoff_route_hint"] == "manual_resolution_required"
    assert "state=main_menu" in context.recent_messages_summary


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
    assert context.metadata["ux_recovery_reason"] == "step_scope_mismatch"
    assert context.metadata["ux_next_action_hint"] == "guide_current_step"
    assert context.metadata["recovery_policy_level"] == "guided"
    assert context.metadata["step_progress"] == "3/4"
    assert context.metadata["input_mode"] == "text_allowed"
    assert context.metadata["recovery_domain"] == "yield"
    assert context.metadata["recovery_task_hint"] == "yield_step_input"
    assert context.metadata["recovery_resume_action"] == "continue_yield_input"
    assert "yield_amount_requires_supported_unit_or_default_kg" in context.hard_constraints
    assert "수확량을 입력하세요" in context.current_question


def test_assemble_recovery_context_for_evidence_step_uses_attachment_mode():
    validation_result = ValidationResult(
        classification=ValidationClassification.REASK,
        source=RuleSource.CHEAP_GATE,
        reason="structured_step_mismatch",
    )
    evidence_draft = evidence_service.update_draft(
        evidence_service.new_draft(
            request_event_id="request-1",
            session_id="session-1",
            request_type_code="field_photo",
            field_label="FIELD-001",
        ),
        accepted_location=True,
    )

    context = assemble_recovery_context(
        current_step=STATE_EVIDENCE_WAITING_DOCUMENT,
        latest_user_message="사진 보냈어요",
        locale="ko",
        recovery_attempt_count=1,
        canonical_intent=registry.INTENT_EVIDENCE_SUBMISSION_START,
        validation_result=validation_result,
        fallback_key="evidence_input",
        evidence_submission_draft_data=evidence_draft.to_dict(),
    )

    assert context.metadata["step_progress"] == "2/2"
    assert context.metadata["input_mode"] == "document_upload"
    assert "document 업로드" in context.current_question
