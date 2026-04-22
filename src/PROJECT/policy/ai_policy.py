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
    if local_ai_gate in {LocalAiGate.DISABLED, LocalAiGate.MANUAL_REVIEW_FALLBACK}:
        return False
    if not current_step or not is_free_text or same_input_seen:
        return False

    if invocation_type == "repair":
        if not local_ai_gate_allows_edit_intent(local_ai_gate):
            return False
        if not (is_structured_step or is_confirm_step):
            return False
        max_calls = MAX_LLM_CALLS_PER_CONFIRM_STEP if is_confirm_step else MAX_LLM_CALLS_PER_STRUCTURED_STEP
        return llm_calls_in_step < max_calls

    if invocation_type == "recovery":
        if not local_ai_gate_allows_recovery_assist(local_ai_gate):
            return False
        if not (is_structured_step or is_confirm_step):
            return False
        max_calls = MAX_LLM_CALLS_PER_CONFIRM_STEP if is_confirm_step else MAX_LLM_CALLS_PER_STRUCTURED_STEP
        return llm_calls_in_step < max_calls

    return False


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
    if validation_reason in UNKNOWN_HANDOFF_REASONS:
        return UnknownInputDisposition.HANDOFF_REQUIRED

    if domain_hint == "profile":
        if use_confirmed or current_step in PROFILE_UNKNOWN_LLM_STATES:
            return UnknownInputDisposition.REPAIR_ASSIST_ALLOWED
        return UnknownInputDisposition.FALLBACK_ONLY

    if domain_hint == "fertilizer":
        if use_confirmed or current_step in FERTILIZER_UNKNOWN_LLM_STATES:
            return UnknownInputDisposition.REPAIR_ASSIST_ALLOWED
        return UnknownInputDisposition.FALLBACK_ONLY

    return UnknownInputDisposition.FALLBACK_ONLY


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
