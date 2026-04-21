from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_EDIT_SELECT,
)
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_WEATHER_MENU
from PROJECT.rule_engine.contracts import RuleSource, ValidationClassification, ValidationResult
from PROJECT.rule_engine.normalizer import normalize_body_text

MAX_RECOVERY_ATTEMPTS = 3

SUPPORT_REQUEST_PATTERNS = (
    "상담원",
    "사람 연결",
    "사람이랑",
    "담당자 연결",
    "운영자",
    "직원 연결",
    "human",
    "operator",
    "support",
    "agent",
    "talk to person",
    "និយាយជាមួយមនុស្ស",
)

MANUAL_HANDOFF_PATTERNS = (
    "민원",
    "불만",
    "신고",
    "complaint",
    "manual handoff",
    "operator handoff",
)

STRUCTURED_REASK_STATES = {
    STATE_WEATHER_MENU,
    STATE_CANCELLED,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_EDIT_SELECT,
}


def classify_cheap_gate(
    raw_text: str,
    *,
    current_step: str | None,
    locale: str = "ko",
    recovery_attempt_count: int = 0,
) -> ValidationResult:
    normalized_text = normalize_body_text(raw_text)

    if _contains_any(normalized_text, SUPPORT_REQUEST_PATTERNS):
        return ValidationResult(
            classification=ValidationClassification.NEEDS_HANDOFF,
            source=RuleSource.CHEAP_GATE,
            reason="explicit_support_request",
            human_handoff_reason="user_requested_human_support",
            metadata=_metadata(current_step, locale, recovery_attempt_count),
        )

    if _contains_any(normalized_text, MANUAL_HANDOFF_PATTERNS):
        return ValidationResult(
            classification=ValidationClassification.NEEDS_HANDOFF,
            source=RuleSource.CHEAP_GATE,
            reason="manual_handoff_request",
            human_handoff_reason="manual_handoff_keyword_detected",
            metadata=_metadata(current_step, locale, recovery_attempt_count),
        )

    if recovery_attempt_count >= MAX_RECOVERY_ATTEMPTS:
        return ValidationResult(
            classification=ValidationClassification.NEEDS_HANDOFF,
            source=RuleSource.CHEAP_GATE,
            reason="recovery_retry_limit_exceeded",
            human_handoff_reason="cheap_gate_retry_limit",
            metadata=_metadata(current_step, locale, recovery_attempt_count),
        )

    if not normalized_text:
        return ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="empty_input",
            metadata=_metadata(current_step, locale, recovery_attempt_count),
        )

    if current_step in STRUCTURED_REASK_STATES:
        return ValidationResult(
            classification=ValidationClassification.REASK,
            source=RuleSource.CHEAP_GATE,
            reason="structured_step_mismatch",
            metadata=_metadata(current_step, locale, recovery_attempt_count),
        )

    return ValidationResult(
        classification=ValidationClassification.UNRESOLVED_RECOVERABLE,
        source=RuleSource.CHEAP_GATE,
        reason="unresolved_text",
        metadata=_metadata(current_step, locale, recovery_attempt_count),
    )


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def _metadata(current_step: str | None, locale: str, recovery_attempt_count: int) -> dict[str, str | int | None]:
    return {
        "current_step": current_step,
        "locale": locale,
        "recovery_attempt_count": recovery_attempt_count,
    }
