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
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)

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

PROFILE_NAME_MARKERS = ("이름", "성함", "name")
PROFILE_RESIDENCE_MARKERS = ("거주지", "주소", "residence", "address")
PROFILE_CITY_MARKERS = ("시/도", "시도", "province", "city province")
PROFILE_DISTRICT_MARKERS = ("구/군/시", "구군시", "district")
PROFILE_BIRTH_MARKERS = ("생년월일", "생일", "birthday", "birthdate")

FERTILIZER_USED_MARKERS = ("사용 여부", "사용", "안씀", "미사용", "used")
FERTILIZER_KIND_MARKERS = ("유형", "종류", "타입", "kind", "type")
FERTILIZER_PRODUCT_MARKERS = ("제품명", "제품", "상품", "브랜드", "product", "name")
FERTILIZER_AMOUNT_MARKERS = ("사용량", "비료량", "양", "수량", "amount", "quantity")
FERTILIZER_DATE_MARKERS = ("사용일", "날짜", "언제", "date", "day")

TRAILING_UPDATE_PATTERN = re.compile(
    r"\s*(?:은|는|이|가|을|를|도|:)?\s*"
    r"(?:"
    r"(?:으로|로)?\s*(?:바꿔줘|바꿔주세요|바꿔|수정해줘|수정해주세요|수정할게|수정|변경해줘|변경해주세요|변경할게|변경|고쳐줘|고쳐주세요|고쳐|다시입력해줘|다시입력해주세요)"
    r"|(?:이야|예요|이에요|입니다)"
    r")\s*$",
    re.IGNORECASE,
)

LEADING_PARTICLE_PATTERN = re.compile(r"^(?:은|는|이|가|을|를|:)\s*")


@dataclass(frozen=True)
class DirectUpdateDecision:
    target_state: str
    changes: dict[str, object]
    matched_rule: str


def detect_profile_direct_update(text: str, *, allow_implicit: bool = False) -> DirectUpdateDecision | None:
    if not allow_implicit and not _has_update_signal(text):
        return None

    birth_date = profile_service.parse_birth_date_text(text)
    if birth_date and (_contains_any(text, PROFILE_BIRTH_MARKERS) or allow_implicit):
        year, month, day = birth_date
        return DirectUpdateDecision(
            target_state=STATE_PROFILE_BIRTH_YEAR,
            changes={"birth_year": year, "birth_month": month, "birth_day": day},
            matched_rule="profile_direct_birth_date",
        )

    name_candidate = _extract_field_value(text, PROFILE_NAME_MARKERS)
    name = profile_service.parse_name(name_candidate) if name_candidate else None
    if name is not None:
        return DirectUpdateDecision(
            target_state=STATE_PROFILE_NAME,
            changes={"name": name},
            matched_rule="profile_direct_name",
        )

    residence_candidate = _extract_field_value(text, PROFILE_RESIDENCE_MARKERS)
    residence = profile_service.parse_free_text(residence_candidate) if residence_candidate else None
    if residence is not None:
        return DirectUpdateDecision(
            target_state=STATE_PROFILE_RESIDENCE,
            changes={"residence": residence},
            matched_rule="profile_direct_residence",
        )

    city_candidate = _extract_field_value(text, PROFILE_CITY_MARKERS)
    city = profile_service.parse_free_text(city_candidate) if city_candidate else None
    if city is not None:
        return DirectUpdateDecision(
            target_state=STATE_PROFILE_CITY,
            changes={"city": city},
            matched_rule="profile_direct_city",
        )

    district_candidate = _extract_field_value(text, PROFILE_DISTRICT_MARKERS)
    district = profile_service.parse_free_text(district_candidate) if district_candidate else None
    if district is not None:
        return DirectUpdateDecision(
            target_state=STATE_PROFILE_DISTRICT,
            changes={"district": district},
            matched_rule="profile_direct_district",
        )

    inferred = _extract_negated_candidate(text)
    if inferred is None and allow_implicit:
        inferred = _clean_value(text)

    if inferred:
        if _looks_like_district(inferred):
            district = profile_service.parse_free_text(inferred)
            if district is not None:
                return DirectUpdateDecision(
                    target_state=STATE_PROFILE_DISTRICT,
                    changes={"district": district},
                    matched_rule="profile_inferred_district",
                )
        if _looks_like_city(inferred):
            city = profile_service.parse_free_text(inferred)
            if city is not None:
                return DirectUpdateDecision(
                    target_state=STATE_PROFILE_CITY,
                    changes={"city": city},
                    matched_rule="profile_inferred_city",
                )

    return None


def detect_fertilizer_direct_update(text: str, *, allow_implicit: bool = False) -> DirectUpdateDecision | None:
    if not allow_implicit and not _has_update_signal(text):
        return None

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
    for marker in markers:
        marker_match = re.search(re.escape(marker), text, re.IGNORECASE)
        if marker_match is None:
            continue
        candidate = _clean_value(text[marker_match.end():])
        if candidate:
            return candidate
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
    return normalized


def _looks_like_city(value: str) -> bool:
    return bool(re.search(r"(특별시|광역시|특별자치시|특별자치도|도|시)$", value)) and not _looks_like_district(value)


def _looks_like_district(value: str) -> bool:
    return bool(re.search(r"(구|군|읍|면|동|리|시)$", value)) and not re.search(r"(특별시|광역시|특별자치시)$", value)
