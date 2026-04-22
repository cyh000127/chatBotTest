from PROJECT.policy import RecoveryPolicyLevel, evaluate_recovery_policy
from PROJECT.rule_engine import RecoveryUxReason


def test_recovery_policy_starts_soft_for_simple_input_error():
    decision = evaluate_recovery_policy(
        recovery_attempt_count=1,
        ux_reason=RecoveryUxReason.INPUT_FORMAT_MISMATCH,
    )

    assert decision.level == RecoveryPolicyLevel.SOFT
    assert decision.should_offer_safe_exit is False
    assert decision.should_prioritize_buttons is False


def test_recovery_policy_escalates_to_guided_on_second_attempt():
    decision = evaluate_recovery_policy(
        recovery_attempt_count=2,
        ux_reason=RecoveryUxReason.INPUT_FORMAT_MISMATCH,
    )

    assert decision.level == RecoveryPolicyLevel.GUIDED
    assert decision.should_offer_safe_exit is False
    assert decision.should_prioritize_buttons is True


def test_recovery_policy_prioritizes_escalation_for_repeated_failure():
    decision = evaluate_recovery_policy(
        recovery_attempt_count=1,
        ux_reason=RecoveryUxReason.REPEATED_FAILURE,
    )

    assert decision.level == RecoveryPolicyLevel.ESCALATION_READY
    assert decision.should_offer_safe_exit is True
    assert decision.should_prioritize_buttons is True
