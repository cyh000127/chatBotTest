from dataclasses import dataclass
from enum import StrEnum

from PROJECT.rule_engine.contracts import ValidationResult


class RecoveryUxReason(StrEnum):
    EMPTY_INPUT = "empty_input"
    MISSING_REQUIRED_VALUE = "missing_required_value"
    INPUT_FORMAT_MISMATCH = "input_format_mismatch"
    TARGET_AMBIGUITY = "target_ambiguity"
    STEP_SCOPE_MISMATCH = "step_scope_mismatch"
    GENERIC_RECOVERABLE = "generic_recoverable"
    REPEATED_FAILURE = "repeated_failure"
    SUPPORT_ESCALATION = "support_escalation"
    ADMIN_FOLLOWUP = "admin_followup"
    MANUAL_RESOLUTION = "manual_resolution"


@dataclass(frozen=True)
class RecoveryUxDecision:
    reason: RecoveryUxReason
    next_action_hint: str


def classify_recovery_ux(validation_result: ValidationResult | None) -> RecoveryUxDecision:
    if validation_result is None:
        return RecoveryUxDecision(
            reason=RecoveryUxReason.GENERIC_RECOVERABLE,
            next_action_hint="offer_related_actions",
        )

    reason = validation_result.reason or ""

    if reason == "explicit_support_request":
        return RecoveryUxDecision(
            reason=RecoveryUxReason.SUPPORT_ESCALATION,
            next_action_hint="show_support_guidance",
        )

    if reason == "manual_handoff_request":
        return RecoveryUxDecision(
            reason=RecoveryUxReason.ADMIN_FOLLOWUP,
            next_action_hint="show_admin_followup_guidance",
        )

    if reason == "recovery_retry_limit_exceeded":
        return RecoveryUxDecision(
            reason=RecoveryUxReason.REPEATED_FAILURE,
            next_action_hint="offer_safe_exit",
        )

    if reason == "empty_input":
        return RecoveryUxDecision(
            reason=RecoveryUxReason.EMPTY_INPUT,
            next_action_hint="retry_same_step",
        )

    if reason in {"structured_step_mismatch", "unsupported_followup_slot"}:
        return RecoveryUxDecision(
            reason=RecoveryUxReason.STEP_SCOPE_MISMATCH,
            next_action_hint="guide_current_step",
        )

    if reason.startswith("missing_or_ambiguous_"):
        return RecoveryUxDecision(
            reason=RecoveryUxReason.MISSING_REQUIRED_VALUE,
            next_action_hint="request_required_value",
        )

    if reason in {"invalid_city_followup", "invalid_district_followup"}:
        return RecoveryUxDecision(
            reason=RecoveryUxReason.INPUT_FORMAT_MISMATCH,
            next_action_hint="show_input_example",
        )

    if reason == "invalid_district_choice_followup":
        return RecoveryUxDecision(
            reason=RecoveryUxReason.TARGET_AMBIGUITY,
            next_action_hint="offer_choice_buttons",
        )

    if reason in {"needs_human", "manual_candidate_review_required"}:
        return RecoveryUxDecision(
            reason=RecoveryUxReason.MANUAL_RESOLUTION,
            next_action_hint="offer_manual_resolution_path",
        )

    return RecoveryUxDecision(
        reason=RecoveryUxReason.GENERIC_RECOVERABLE,
        next_action_hint="offer_related_actions",
    )
