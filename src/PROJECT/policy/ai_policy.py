from enum import StrEnum


class AiMode(StrEnum):
    DISABLED = "disabled"
    REPAIR_ASSIST_ONLY = "repair_assist_only"
    RECOVERY_ASSIST_ONLY = "recovery_assist_only"
    MANUAL_REVIEW_FALLBACK = "manual_review_fallback"


MAX_LLM_CALLS_PER_STRUCTURED_STEP = 1
MAX_LLM_CALLS_PER_CONFIRM_STEP = 1
MAX_RECOVERY_ATTEMPTS_BEFORE_HANDOFF = 3


def parse_ai_mode(raw: str | None, *, default: AiMode = AiMode.DISABLED) -> AiMode:
    if raw is None or not raw.strip():
        return default
    normalized = raw.strip().lower()
    try:
        return AiMode(normalized)
    except ValueError as exc:
        raise ValueError(f"지원하지 않는 AI_MODE 입니다: {raw}") from exc


def ai_mode_allows_edit_intent(ai_mode: AiMode) -> bool:
    return ai_mode == AiMode.REPAIR_ASSIST_ONLY


def ai_mode_allows_recovery_assist(ai_mode: AiMode) -> bool:
    return ai_mode == AiMode.RECOVERY_ASSIST_ONLY


def can_invoke_llm(
    *,
    ai_mode: AiMode,
    invocation_type: str,
    current_step: str | None,
    is_structured_step: bool,
    is_confirm_step: bool,
    is_free_text: bool,
    llm_calls_in_step: int,
    same_input_seen: bool,
) -> bool:
    if ai_mode in {AiMode.DISABLED, AiMode.MANUAL_REVIEW_FALLBACK}:
        return False
    if not current_step or not is_free_text or same_input_seen:
        return False

    if invocation_type == "repair":
        if not ai_mode_allows_edit_intent(ai_mode):
            return False
        if not (is_structured_step or is_confirm_step):
            return False
        max_calls = MAX_LLM_CALLS_PER_CONFIRM_STEP if is_confirm_step else MAX_LLM_CALLS_PER_STRUCTURED_STEP
        return llm_calls_in_step < max_calls

    if invocation_type == "recovery":
        if not ai_mode_allows_recovery_assist(ai_mode):
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
