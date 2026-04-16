from dataclasses import asdict, dataclass, field
import re

from PROJECT.conversations.profile_intake.normalization import (
    CITY_ALIASES,
    DISTRICT_RULES,
    detect_city,
    detect_district_rule,
    district_examples_for_city,
    normalize_text,
)

PARSE_PARSED = "parsed"
PARSE_NEEDS_FOLLOWUP = "needs_followup"


@dataclass(frozen=True)
class ProfileDraft:
    raw_text: str
    name_candidate: str | None = None
    birth_date_candidate: str | None = None
    residence_raw: str | None = None
    city_candidate: str | None = None
    district_candidate: str | None = None
    parse_status: str = PARSE_NEEDS_FOLLOWUP
    pending_slot: str | None = None
    retry_count: int = 0
    followup_options: tuple[str, ...] = field(default_factory=tuple)
    followup_keyword: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


STOPWORDS = {
    "이름", "생일", "생년월일", "거주지", "저는", "전", "저", "살아요", "살고", "입니다",
    "이고", "는", "은", "요", "김", "박", "이",
}
PLACE_TOKENS = set(CITY_ALIASES) | {
    token
    for rule in DISTRICT_RULES
    for token in rule.trigger.split()
}


def _convert_year(year: int) -> int:
    if year >= 100:
        return year
    return 2000 + year if year <= 29 else 1900 + year


def extract_birth_date(text: str) -> tuple[str | None, str]:
    patterns = [
        r"(?P<year>\d{2,4})\s*년\s*(?P<month>\d{1,2})\s*월\s*(?P<day>\d{1,2})\s*일?",
        r"(?P<year>\d{2,4})[.\-/ ](?P<month>\d{1,2})[.\-/ ](?P<day>\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        year = _convert_year(int(match.group("year")))
        month = int(match.group("month"))
        day = int(match.group("day"))
        birth = f"{year:04d}-{month:02d}-{day:02d}"
        return birth, text.replace(match.group(0), " ")
    return None, text


def extract_name(text: str) -> tuple[str | None, str]:
    labeled = re.search(r"이름(?:은|는|이)?\s*([가-힣]{2,4})", text)
    if labeled:
        name = labeled.group(1)
        return name, text.replace(labeled.group(0), " ")

    for token in normalize_text(text).split():
        if not re.fullmatch(r"[가-힣]{2,4}", token):
            continue
        if token in STOPWORDS:
            continue
        if token in PLACE_TOKENS:
            continue
        if token.endswith(("시", "구", "군", "도")):
            continue
        return token, text.replace(token, " ", 1)
    return None, text


def _residence_raw(normalized_text: str, city: str | None, district: str | None, keyword: str | None) -> str | None:
    if city and district:
        return f"{city} {district}"
    if city and keyword:
        return f"{city} {keyword}"
    if keyword:
        return keyword
    if city:
        return city
    return None


def parse_profile_text(text: str) -> ProfileDraft:
    birth_date, without_birth = extract_birth_date(text)
    name, without_name = extract_name(without_birth)
    normalized = normalize_text(without_name)

    city = detect_city(normalized)
    rule = detect_district_rule(normalized)

    district = None
    pending_slot = None
    followup_options: tuple[str, ...] = ()
    followup_keyword = None
    parse_status = PARSE_PARSED

    if rule is not None:
        followup_keyword = rule.trigger
        if rule.ambiguous_options:
            city = city or rule.city
            pending_slot = "district_choice"
            followup_options = rule.ambiguous_options
            parse_status = PARSE_NEEDS_FOLLOWUP
        elif city is None and rule.ask_city_when_missing:
            district = rule.district
            pending_slot = "city_for_district"
            parse_status = PARSE_NEEDS_FOLLOWUP
        else:
            city = city or rule.city
            district = rule.district
    elif city:
        pending_slot = "district_for_city"
        parse_status = PARSE_NEEDS_FOLLOWUP
    else:
        parse_status = PARSE_NEEDS_FOLLOWUP

    if name is None or birth_date is None:
        parse_status = PARSE_NEEDS_FOLLOWUP
        pending_slot = pending_slot or ("name" if name is None else "birth_date")

    residence_raw = _residence_raw(normalized, city, district, followup_keyword)

    return ProfileDraft(
        raw_text=text,
        name_candidate=name,
        birth_date_candidate=birth_date,
        residence_raw=residence_raw,
        city_candidate=city,
        district_candidate=district,
        parse_status=parse_status,
        pending_slot=pending_slot,
        followup_options=followup_options,
        followup_keyword=followup_keyword,
    )


def apply_followup_response(draft: ProfileDraft, text: str) -> ProfileDraft:
    normalized = normalize_text(text)

    if draft.pending_slot == "city_for_district":
        city = detect_city(normalized)
        if city is None:
            return ProfileDraft(**{**draft.to_dict(), "retry_count": draft.retry_count + 1})
        return ProfileDraft(
            **{
                **draft.to_dict(),
                "city_candidate": city,
                "parse_status": PARSE_PARSED,
                "pending_slot": None,
                "followup_options": (),
                "retry_count": draft.retry_count + 1,
                "residence_raw": f"{city} {draft.district_candidate}",
            }
        )

    if draft.pending_slot == "district_for_city":
        rule = detect_district_rule(normalized)
        if rule is None or rule.district is None:
            return ProfileDraft(**{**draft.to_dict(), "retry_count": draft.retry_count + 1})
        return ProfileDraft(
            **{
                **draft.to_dict(),
                "district_candidate": rule.district,
                "parse_status": PARSE_PARSED,
                "pending_slot": None,
                "followup_options": (),
                "retry_count": draft.retry_count + 1,
                "residence_raw": f"{draft.city_candidate} {rule.district}",
            }
        )

    if draft.pending_slot == "district_choice":
        options = {option.replace("고양시 ", ""): option for option in draft.followup_options}
        chosen = options.get(normalized)
        if chosen is None and normalized in draft.followup_options:
            chosen = normalized
        if chosen is None:
            return ProfileDraft(**{**draft.to_dict(), "retry_count": draft.retry_count + 1})
        return ProfileDraft(
            **{
                **draft.to_dict(),
                "district_candidate": chosen,
                "parse_status": PARSE_PARSED,
                "pending_slot": None,
                "followup_options": (),
                "retry_count": draft.retry_count + 1,
                "residence_raw": f"{draft.city_candidate} {chosen}",
            }
        )

    return draft


def district_examples(city: str) -> list[str]:
    return district_examples_for_city(city)
