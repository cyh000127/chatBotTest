from PROJECT.rule_engine import RecoveryUxReason, ValidationClassification, classify_recovery_ux
from PROJECT.rule_engine.contracts import RuleSource, ValidationResult


def test_classify_recovery_ux_for_support_request():
    decision = classify_recovery_ux(
        ValidationResult(
            classification=ValidationClassification.NEEDS_HANDOFF,
            source=RuleSource.CHEAP_GATE,
            reason="explicit_support_request",
        )
    )

    assert decision.reason == RecoveryUxReason.SUPPORT_ESCALATION
    assert decision.next_action_hint == "show_support_guidance"


def test_classify_recovery_ux_for_missing_required_value():
    decision = classify_recovery_ux(
        ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.VALIDATOR,
            reason="missing_or_ambiguous_birth_date",
        )
    )

    assert decision.reason == RecoveryUxReason.MISSING_REQUIRED_VALUE
    assert decision.next_action_hint == "request_required_value"


def test_classify_recovery_ux_for_scope_mismatch():
    decision = classify_recovery_ux(
        ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
        )
    )

    assert decision.reason == RecoveryUxReason.STEP_SCOPE_MISMATCH
    assert decision.next_action_hint == "guide_current_step"


def test_classify_recovery_ux_for_invalid_followup_choice():
    decision = classify_recovery_ux(
        ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.VALIDATOR,
            reason="invalid_district_choice_followup",
        )
    )

    assert decision.reason == RecoveryUxReason.TARGET_AMBIGUITY
    assert decision.next_action_hint == "offer_choice_buttons"
