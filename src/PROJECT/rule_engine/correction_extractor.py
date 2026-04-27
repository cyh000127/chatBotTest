from dataclasses import dataclass
import re

from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)

VALUE_UPDATE_SUFFIX_PATTERN = re.compile(
    r"^\s*(?:은|는|이|가|을|를|도|:)?\s*(?P<value>.+?)\s*"
    r"(?:(?:으로|로)\s*)?"
    r"(?:"
    r"바꿔줘|바꿔주세요|바꿀래|바꿔|바꾸(?:고\s*싶어|고\s*싶어요|고\s*싶다|고\s*싶은데)?|"
    r"수정해줘|수정해주세요|수정할래|수정(?:하고\s*싶어|하고\s*싶어요|하고\s*싶다|하고\s*싶은데)?|"
    r"변경해줘|변경해주세요|변경할래|변경(?:하고\s*싶어|하고\s*싶어요|하고\s*싶다|하고\s*싶은데)?|"
    r"고쳐줘|고쳐주세요|고칠래|고쳐|고치(?:고\s*싶어|고\s*싶어요|고\s*싶다|고\s*싶은데)?"
    r")"
    r"\s*$",
    re.IGNORECASE,
)
TARGET_ONLY_SUFFIX_PATTERN = re.compile(
    r"^\s*(?:은|는|이|가|을|를|도|:)?\s*"
    r"(?:수정|변경|다시\s*입력|바꾸기|바꿀래|바꿔|바꾸(?:고\s*싶어|고\s*싶어요|고\s*싶다|고\s*싶은데)?|"
    r"고치기|고칠래|고쳐|고치(?:고\s*싶어|고\s*싶어요|고\s*싶다|고\s*싶은데)?)"
    r"(?:\s*할래|\s*할게|\s*하고\s*싶어|\s*하고\s*싶어요|\s*하고\s*싶다|\s*하고\s*싶은데|\s*라고)?"
    r"\s*$",
    re.IGNORECASE,
)
PLAIN_VALUE_SUFFIX_PATTERN = re.compile(r"^\s*(?:은|는|이|가|을|를|도|:)?\s*(?P<value>.+?)\s*(?:이야|예요|이에요|입니다)\s*$", re.IGNORECASE)

FERTILIZER_FIELD_CONFIGS = (
    (STATE_FERTILIZER_AMOUNT, ("사용량", "비료량", "양", "수량", "amount", "quantity")),
    (STATE_FERTILIZER_DATE, ("사용일", "날짜", "언제", "date", "day")),
    (STATE_FERTILIZER_PRODUCT, ("제품명", "제품", "상품", "브랜드", "product")),
    (STATE_FERTILIZER_KIND, ("유형", "종류", "타입", "kind", "type")),
    (STATE_FERTILIZER_USED, ("사용 여부", "사용", "안씀", "미사용", "used")),
)


@dataclass(frozen=True)
class CorrectionPatternDecision:
    target_state: str
    candidate_value: str | None
    matched_rule: str


def extract_fertilizer_correction_pattern(text: str) -> CorrectionPatternDecision | None:
    return _extract_pattern(text, FERTILIZER_FIELD_CONFIGS, domain="fertilizer")


def _extract_pattern(
    text: str,
    field_configs: tuple[tuple[str, tuple[str, ...]], ...],
    *,
    domain: str,
) -> CorrectionPatternDecision | None:
    for target_state, markers in field_configs:
        matched_marker = _find_marker(text, markers)
        if matched_marker is None:
            continue
        tail = text[matched_marker.end():]
        candidate_value = _extract_candidate_value(tail)
        if candidate_value:
            return CorrectionPatternDecision(
                target_state=target_state,
                candidate_value=candidate_value,
                matched_rule=f"{domain}_pattern_value",
            )
        if TARGET_ONLY_SUFFIX_PATTERN.fullmatch(tail or ""):
            return CorrectionPatternDecision(
                target_state=target_state,
                candidate_value=None,
                matched_rule=f"{domain}_pattern_target_only",
            )
    return None


def _find_marker(text: str, markers: tuple[str, ...]) -> re.Match[str] | None:
    for marker in sorted(markers, key=len, reverse=True):
        marker_match = re.search(re.escape(marker), text, re.IGNORECASE)
        if marker_match is not None:
            return marker_match
    return None


def _extract_candidate_value(tail: str) -> str | None:
    for pattern in (VALUE_UPDATE_SUFFIX_PATTERN, PLAIN_VALUE_SUFFIX_PATTERN):
        match = pattern.fullmatch(tail)
        if match is None:
            continue
        candidate = _cleanup_candidate(match.group("value"))
        if candidate:
            return candidate
    return None


def _cleanup_candidate(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip()).strip(" .,!?:")
    return cleaned
