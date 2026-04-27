from dataclasses import dataclass
import re

from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)
from PROJECT.rule_engine.correction_extractor import extract_fertilizer_correction_pattern

UPDATE_MARKERS = (
    "수정",
    "잘못",
    "틀렸",
    "다시",
    "변경",
    "고칠",
    "바꿔",
    "바꾸",
    "고쳐",
    "말고",
    "아니고",
    "대신",
    "edit",
    "change",
    "fix",
)

FERTILIZER_USED_MARKERS = ("사용 여부", "사용", "안씀", "미사용", "used")
FERTILIZER_KIND_MARKERS = ("유형", "종류", "타입", "kind", "type")
FERTILIZER_PRODUCT_MARKERS = ("제품명", "제품", "상품", "브랜드", "product", "name")
FERTILIZER_AMOUNT_MARKERS = ("사용량", "비료량", "양", "수량", "amount", "quantity")
FERTILIZER_DATE_MARKERS = ("사용일", "날짜", "언제", "date", "day")

TRAILING_UPDATE_PATTERN = re.compile(
    r"\s*(?:은|는|이|가|을|를|도|:)?\s*"
    r"(?:"
    r"(?:으로|로)?\s*(?:바꿔줘|바꿔주세요|바꿀래|바꿀게|바꾸고싶어|바꾸고싶어요|바꾸고싶다|바꾸고싶은데|바꿔볼래|바꿔|수정해줘|수정해주세요|수정할래|수정할게|수정하고싶어|수정하고싶어요|수정하고싶다|수정하고싶은데|수정|변경해줘|변경해주세요|변경할래|변경할게|변경하고싶어|변경하고싶어요|변경하고싶다|변경하고싶다고|변경하고싶은데|변경|고쳐줘|고쳐주세요|고칠래|고칠게|고치고싶어|고치고싶어요|고치고싶다|고치고싶은데|고쳐|다시입력해줘|다시입력해주세요)"
    r"|(?:이야|예요|이에요|입니다)"
    r")\s*$",
    re.IGNORECASE,
)

LEADING_PARTICLE_PATTERN = re.compile(r"^(?:은|는|이|가|을|를|:)\s*")
ACTION_ONLY_PATTERN = re.compile(
    r"^(?:"
    r"(?:다시\s*)?(?:입력|수정|변경)"
    r"(?:\s*하(?:고)?)?"
    r"(?:\s*고\s*싶(?:어|어요|다|은데|다고))?"
    r"(?:\s*할(?:래|게))?"
    r"|(?:바꾸|바꿔|고치|고쳐)"
    r"(?:\s*고\s*싶(?:어|어요|다|은데|다고))?"
    r"(?:\s*볼래|\s*줘|\s*주세요|\s*할(?:래|게))?"
    r")$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DirectUpdateDecision:
    target_state: str
    changes: dict[str, object]
    matched_rule: str


def detect_fertilizer_direct_update(text: str, *, allow_implicit: bool = False) -> DirectUpdateDecision | None:
    if not allow_implicit and not _has_update_signal(text):
        return None

    correction_pattern = extract_fertilizer_correction_pattern(text)
    if correction_pattern is not None and correction_pattern.candidate_value is not None:
        candidate_value = correction_pattern.candidate_value
        if correction_pattern.target_state == STATE_FERTILIZER_USED:
            used = fertilizer_service.parse_used(candidate_value)
            if used is not None:
                return DirectUpdateDecision(
                    target_state=STATE_FERTILIZER_USED,
                    changes={"used": used},
                    matched_rule=correction_pattern.matched_rule,
                )
        if correction_pattern.target_state == STATE_FERTILIZER_AMOUNT:
            amount = fertilizer_service.parse_amount(candidate_value)
            if amount is not None:
                return DirectUpdateDecision(
                    target_state=STATE_FERTILIZER_AMOUNT,
                    changes={"amount_value": amount[0], "amount_unit": amount[1]},
                    matched_rule=correction_pattern.matched_rule,
                )
        if correction_pattern.target_state == STATE_FERTILIZER_DATE:
            applied_date = fertilizer_service.parse_applied_date(candidate_value)
            if applied_date is not None:
                return DirectUpdateDecision(
                    target_state=STATE_FERTILIZER_DATE,
                    changes={"applied_date": applied_date},
                    matched_rule=correction_pattern.matched_rule,
                )
        if correction_pattern.target_state == STATE_FERTILIZER_KIND:
            kind = fertilizer_service.parse_kind(candidate_value)
            if kind is not None:
                return DirectUpdateDecision(
                    target_state=STATE_FERTILIZER_KIND,
                    changes={"kind": kind},
                    matched_rule=correction_pattern.matched_rule,
                )
        if correction_pattern.target_state == STATE_FERTILIZER_PRODUCT:
            product_name = fertilizer_service.parse_product_name(candidate_value)
            if product_name is not None:
                return DirectUpdateDecision(
                    target_state=STATE_FERTILIZER_PRODUCT,
                    changes={"product_name": product_name},
                    matched_rule=correction_pattern.matched_rule,
                )

    used = fertilizer_service.parse_used(text)
    if used is not None and (_contains_any(text, FERTILIZER_USED_MARKERS) or allow_implicit):
        return DirectUpdateDecision(
            target_state=STATE_FERTILIZER_USED,
            changes={"used": used},
            matched_rule="fertilizer_direct_used",
        )

    negated_candidate = _extract_negated_candidate(text)

    amount_candidate = _extract_field_value(text, FERTILIZER_AMOUNT_MARKERS) or negated_candidate
    amount_input = amount_candidate or (text if allow_implicit else "")
    amount = fertilizer_service.parse_amount(amount_input)
    if amount is not None and (_contains_any(text, FERTILIZER_AMOUNT_MARKERS) or negated_candidate is not None or allow_implicit):
        value, unit = amount
        return DirectUpdateDecision(
            target_state=STATE_FERTILIZER_AMOUNT,
            changes={"amount_value": value, "amount_unit": unit},
            matched_rule="fertilizer_direct_amount",
        )

    applied_date_candidate = _extract_field_value(text, FERTILIZER_DATE_MARKERS) or negated_candidate
    applied_date_input = applied_date_candidate or (text if allow_implicit else "")
    applied_date = fertilizer_service.parse_applied_date(applied_date_input)
    if applied_date is not None and (_contains_any(text, FERTILIZER_DATE_MARKERS) or negated_candidate is not None or allow_implicit):
        return DirectUpdateDecision(
            target_state=STATE_FERTILIZER_DATE,
            changes={"applied_date": applied_date},
            matched_rule="fertilizer_direct_date",
        )

    kind_candidate = _extract_field_value(text, FERTILIZER_KIND_MARKERS) or negated_candidate
    kind_input = kind_candidate or (text if allow_implicit else "")
    kind = fertilizer_service.parse_kind(kind_input)
    if kind is not None and (_contains_any(text, FERTILIZER_KIND_MARKERS) or negated_candidate is not None or allow_implicit):
        return DirectUpdateDecision(
            target_state=STATE_FERTILIZER_KIND,
            changes={"kind": kind},
            matched_rule="fertilizer_direct_kind",
        )

    product_candidate = _extract_field_value(text, FERTILIZER_PRODUCT_MARKERS)
    product_name = fertilizer_service.parse_product_name(product_candidate) if product_candidate else None
    if product_name is not None:
        return DirectUpdateDecision(
            target_state=STATE_FERTILIZER_PRODUCT,
            changes={"product_name": product_name},
            matched_rule="fertilizer_direct_product",
        )

    return None


def _has_update_signal(text: str) -> bool:
    collapsed = _collapse(text)
    return any(marker in collapsed for marker in UPDATE_MARKERS)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    collapsed = _collapse(text)
    return any(_collapse(marker) in collapsed for marker in markers)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", "", text.strip().lower())


def _extract_field_value(text: str, markers: tuple[str, ...]) -> str | None:
    for marker in sorted(markers, key=len, reverse=True):
        marker_match = re.search(re.escape(marker), text, re.IGNORECASE)
        if marker_match is None:
            continue
        candidate = _clean_value(text[marker_match.end():])
        if candidate:
            return candidate
        return None
    return None


def _extract_negated_candidate(text: str) -> str | None:
    match = re.search(r"(?:아니고|말고|대신)\s*(?P<value>.+)$", text)
    if match is None:
        return None
    return _clean_value(match.group("value"))


def _clean_value(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip())
    normalized = LEADING_PARTICLE_PATTERN.sub("", normalized)
    if any(marker in normalized for marker in ("아니고", "말고", "대신")):
        negated = _extract_negated_candidate(normalized)
        if negated:
            normalized = negated
    normalized = TRAILING_UPDATE_PATTERN.sub("", normalized).strip(" .,!?:")
    collapsed = _collapse(normalized)
    if collapsed and ACTION_ONLY_PATTERN.fullmatch(collapsed):
        return ""
    return normalized
