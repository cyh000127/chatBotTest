from dataclasses import dataclass
from enum import StrEnum

from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT


class LocalAiGate(StrEnum):
    DISABLED = "disabled"
    REPAIR_ASSIST_ONLY = "repair_assist_only"
    RECOVERY_ASSIST_ONLY = "recovery_assist_only"
    MANUAL_REVIEW_FALLBACK = "manual_review_fallback"


class UnknownInputDisposition(StrEnum):
    FALLBACK_ONLY = "fallback_only"
    REPAIR_ASSIST_ALLOWED = "repair_assist_allowed"
    HANDOFF_REQUIRED = "handoff_required"


class HandoffRoute(StrEnum):
    SUPPORT_ESCALATE = "support.escalate"
    MANUAL_RESOLUTION_REQUIRED = "manual_resolution_required"
    ADMIN_FOLLOWUP_QUEUE = "admin_followup_queue"
    MANUAL_REVIEW_REQUIRED = "manual_resolution_required"
    ADMIN_FOLLOWUP_REQUIRED = "admin_followup_queue"


@dataclass(frozen=True)
class LlmInvocationPolicyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class UnknownInputPolicyDecision:
    disposition: UnknownInputDisposition
    reason: str


MAX_LLM_CALLS_PER_STRUCTURED_STEP = 1
MAX_LLM_CALLS_PER_CONFIRM_STEP = 1
MAX_RECOVERY_ATTEMPTS_BEFORE_HANDOFF = 3

UNKNOWN_HANDOFF_REASONS = frozenset({"explicit_support_request", "manual_handoff_request"})
PROFILE_UNKNOWN_LLM_STATES = frozenset({STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT})
FERTILIZER_UNKNOWN_LLM_STATES = frozenset({STATE_FERTILIZER_CONFIRM})


def parse_local_ai_gate(raw: str | None, *, default: LocalAiGate = LocalAiGate.DISABLED) -> LocalAiGate:
    if raw is None or not raw.strip():
        return default
    normalized = raw.strip().lower()
    try:
        return LocalAiGate(normalized)
    except ValueError as exc:
        raise ValueError(f"지원하지 않는 AI_MODE 입니다: {raw}") from exc


def local_ai_gate_allows_edit_intent(local_ai_gate: LocalAiGate) -> bool:
    return local_ai_gate == LocalAiGate.REPAIR_ASSIST_ONLY


def local_ai_gate_allows_recovery_assist(local_ai_gate: LocalAiGate) -> bool:
    return local_ai_gate == LocalAiGate.RECOVERY_ASSIST_ONLY


def can_invoke_llm(
    *,
    local_ai_gate: LocalAiGate,
    invocation_type: str,
    current_step: str | None,
    is_structured_step: bool,
    is_confirm_step: bool,
    is_free_text: bool,
    llm_calls_in_step: int,
    same_input_seen: bool,
) -> bool:
    return evaluate_llm_invocation_policy(
        local_ai_gate=local_ai_gate,
        invocation_type=invocation_type,
        current_step=current_step,
        is_structured_step=is_structured_step,
        is_confirm_step=is_confirm_step,
        is_free_text=is_free_text,
        llm_calls_in_step=llm_calls_in_step,
        same_input_seen=same_input_seen,
    ).allowed


def evaluate_llm_invocation_policy(
    *,
    local_ai_gate: LocalAiGate,
    invocation_type: str,
    current_step: str | None,
    is_structured_step: bool,
    is_confirm_step: bool,
    is_free_text: bool,
    llm_calls_in_step: int,
    same_input_seen: bool,
) -> LlmInvocationPolicyDecision:
    if local_ai_gate == LocalAiGate.MANUAL_REVIEW_FALLBACK:
        return LlmInvocationPolicyDecision(False, "manual_review_fallback_active")
    if local_ai_gate == LocalAiGate.DISABLED:
        return LlmInvocationPolicyDecision(False, "local_ai_gate_disabled")
    if not current_step:
        return LlmInvocationPolicyDecision(False, "missing_current_step")
    if not is_free_text:
        return LlmInvocationPolicyDecision(False, "not_free_text")
    if same_input_seen:
        return LlmInvocationPolicyDecision(False, "duplicate_input")

    if invocation_type == "repair":
        if not local_ai_gate_allows_edit_intent(local_ai_gate):
            return LlmInvocationPolicyDecision(False, "repair_not_allowed_by_gate")
        if not (is_structured_step or is_confirm_step):
            return LlmInvocationPolicyDecision(False, "repair_requires_structured_or_confirm_step")
        max_calls = MAX_LLM_CALLS_PER_CONFIRM_STEP if is_confirm_step else MAX_LLM_CALLS_PER_STRUCTURED_STEP
        if llm_calls_in_step >= max_calls:
            return LlmInvocationPolicyDecision(False, "step_call_limit")
        return LlmInvocationPolicyDecision(True, "allowed")

    if invocation_type == "recovery":
        if not local_ai_gate_allows_recovery_assist(local_ai_gate):
            return LlmInvocationPolicyDecision(False, "recovery_not_allowed_by_gate")
        if not (is_structured_step or is_confirm_step):
            return LlmInvocationPolicyDecision(False, "recovery_requires_structured_or_confirm_step")
        max_calls = MAX_LLM_CALLS_PER_CONFIRM_STEP if is_confirm_step else MAX_LLM_CALLS_PER_STRUCTURED_STEP
        if llm_calls_in_step >= max_calls:
            return LlmInvocationPolicyDecision(False, "step_call_limit")
        return LlmInvocationPolicyDecision(True, "allowed")

    return LlmInvocationPolicyDecision(False, "unsupported_invocation_type")


def should_handoff(*, recovery_attempt_count: int, explicit_handoff: bool = False) -> bool:
    return explicit_handoff or recovery_attempt_count >= MAX_RECOVERY_ATTEMPTS_BEFORE_HANDOFF


def same_input_cache_key(*, normalized_text: str, current_step: str | None, locale: str) -> str:
    step = current_step or "none"
    return f"{locale}:{step}:{normalized_text}"


def classify_unknown_input_disposition(
    *,
    current_step: str | None,
    domain_hint: str | None = None,
    use_confirmed: bool = False,
    validation_reason: str | None = None,
) -> UnknownInputDisposition:
    return evaluate_unknown_input_policy(
        current_step=current_step,
        domain_hint=domain_hint,
        use_confirmed=use_confirmed,
        validation_reason=validation_reason,
    ).disposition


def evaluate_unknown_input_policy(
    *,
    current_step: str | None,
    domain_hint: str | None = None,
    use_confirmed: bool = False,
    validation_reason: str | None = None,
) -> UnknownInputPolicyDecision:
    if validation_reason in UNKNOWN_HANDOFF_REASONS:
        return UnknownInputPolicyDecision(
            disposition=UnknownInputDisposition.HANDOFF_REQUIRED,
            reason="explicit_handoff_reason",
        )

    if domain_hint == "profile":
        if use_confirmed or current_step in PROFILE_UNKNOWN_LLM_STATES:
            reason = "confirmed_snapshot_repair_allowed" if use_confirmed else "profile_confirm_context_allowed"
            return UnknownInputPolicyDecision(
                disposition=UnknownInputDisposition.REPAIR_ASSIST_ALLOWED,
                reason=reason,
            )
        return UnknownInputPolicyDecision(
            disposition=UnknownInputDisposition.FALLBACK_ONLY,
            reason="profile_outside_allowed_unknown_context",
        )

    if domain_hint == "fertilizer":
        if use_confirmed or current_step in FERTILIZER_UNKNOWN_LLM_STATES:
            reason = "confirmed_snapshot_repair_allowed" if use_confirmed else "fertilizer_confirm_context_allowed"
            return UnknownInputPolicyDecision(
                disposition=UnknownInputDisposition.REPAIR_ASSIST_ALLOWED,
                reason=reason,
            )
        return UnknownInputPolicyDecision(
            disposition=UnknownInputDisposition.FALLBACK_ONLY,
            reason="fertilizer_outside_allowed_unknown_context",
        )

    return UnknownInputPolicyDecision(
        disposition=UnknownInputDisposition.FALLBACK_ONLY,
        reason="domain_not_allowed_for_unknown_repair",
    )


def classify_handoff_route(
    *,
    reason: str | None,
    human_handoff_reason: str | None = None,
    source: str | None = None,
) -> HandoffRoute:
    if reason == "explicit_support_request" or human_handoff_reason == "user_requested_human_support":
        return HandoffRoute.SUPPORT_ESCALATE

    if reason == "manual_handoff_request" or human_handoff_reason == "manual_handoff_keyword_detected":
        return HandoffRoute.ADMIN_FOLLOWUP_QUEUE

    if source == "llm_repair":
        return HandoffRoute.MANUAL_RESOLUTION_REQUIRED

    if reason == "recovery_retry_limit_exceeded" or human_handoff_reason == "cheap_gate_retry_limit":
        return HandoffRoute.MANUAL_RESOLUTION_REQUIRED

    return HandoffRoute.MANUAL_RESOLUTION_REQUIRED


# Backward-compatible aliases while the repo migrates to the "local helper gate" wording.
AiMode = LocalAiGate


def parse_ai_mode(raw: str | None, *, default: LocalAiGate = LocalAiGate.DISABLED) -> LocalAiGate:
    return parse_local_ai_gate(raw, default=default)


def ai_mode_allows_edit_intent(local_ai_gate: LocalAiGate) -> bool:
    return local_ai_gate_allows_edit_intent(local_ai_gate)


def ai_mode_allows_recovery_assist(local_ai_gate: LocalAiGate) -> bool:
    return local_ai_gate_allows_recovery_assist(local_ai_gate)
