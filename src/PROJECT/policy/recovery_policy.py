from dataclasses import dataclass
from enum import StrEnum


class RecoveryPolicyLevel(StrEnum):
    SOFT = "soft"
    GUIDED = "guided"
    ESCALATION_READY = "escalation_ready"


@dataclass(frozen=True)
class RecoveryPolicyDecision:
    level: RecoveryPolicyLevel
    should_offer_safe_exit: bool
    should_prioritize_buttons: bool


ESCALATION_REASONS = frozenset(
    {
        "support_escalation",
        "admin_followup",
        "repeated_failure",
        "manual_resolution",
    }
)

GUIDED_REASONS = frozenset(
    {
        "target_ambiguity",
        "step_scope_mismatch",
        "generic_recoverable",
    }
)


def evaluate_recovery_policy(
    *,
    recovery_attempt_count: int,
    ux_reason,
) -> RecoveryPolicyDecision:
    normalized_reason = getattr(ux_reason, "value", ux_reason)

    if normalized_reason in ESCALATION_REASONS or recovery_attempt_count >= 3:
        return RecoveryPolicyDecision(
            level=RecoveryPolicyLevel.ESCALATION_READY,
            should_offer_safe_exit=True,
            should_prioritize_buttons=True,
        )

    if recovery_attempt_count >= 2 or normalized_reason in GUIDED_REASONS:
        return RecoveryPolicyDecision(
            level=RecoveryPolicyLevel.GUIDED,
            should_offer_safe_exit=False,
            should_prioritize_buttons=True,
        )

    return RecoveryPolicyDecision(
        level=RecoveryPolicyLevel.SOFT,
        should_offer_safe_exit=False,
        should_prioritize_buttons=False,
    )
