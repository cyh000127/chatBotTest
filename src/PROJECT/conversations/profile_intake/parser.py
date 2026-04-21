from dataclasses import asdict, dataclass, field

from PROJECT.conversations.profile_intake.normalization import (
    detect_city,
    detect_district_rule,
    district_examples_for_city,
    normalize_text,
)
from PROJECT.rule_engine import (
    PROFILE_PENDING_CITY_FOR_DISTRICT,
    PROFILE_PENDING_DISTRICT_CHOICE,
    PROFILE_PENDING_DISTRICT_FOR_CITY,
    PROFILE_NAME_STOPWORDS,
    PROFILE_PLACE_TOKENS,
    ValidationClassification,
    extract_birth_date_candidate,
    extract_korean_name_candidate,
    validate_profile_candidates,
    validate_profile_followup,
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


def extract_birth_date(text: str) -> tuple[str | None, str]:
    candidate, remaining = extract_birth_date_candidate(text)
    if candidate is None:
        return None, remaining
    return str(candidate.normalized_value), remaining


def extract_name(text: str) -> tuple[str | None, str]:
    candidate, remaining = extract_korean_name_candidate(
        text,
        stopwords=PROFILE_NAME_STOPWORDS,
        reserved_tokens=PROFILE_PLACE_TOKENS,
    )
    if candidate is None:
        return None, remaining
    return str(candidate.normalized_value), remaining


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

    validation = validate_profile_candidates(
        name_candidate=name,
        birth_date_candidate=birth_date,
        city_candidate=city,
        district_rule=rule,
    )
    metadata = validation.metadata
    city = metadata.get("city_candidate")
    district = metadata.get("district_candidate")
    pending_slot = metadata.get("pending_slot")
    followup_options = metadata.get("followup_options", ())
    followup_keyword = metadata.get("followup_keyword")
    parse_status = PARSE_PARSED if validation.is_resolved else PARSE_NEEDS_FOLLOWUP

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
    validation = validate_profile_followup(
        pending_slot=draft.pending_slot,
        raw_text=text,
        city_candidate=draft.city_candidate,
        district_candidate=draft.district_candidate,
        followup_options=draft.followup_options,
    )

    if validation.classification == ValidationClassification.REASK:
        return ProfileDraft(**{**draft.to_dict(), "retry_count": draft.retry_count + 1})

    if draft.pending_slot == PROFILE_PENDING_CITY_FOR_DISTRICT:
        city = validation.metadata["city_candidate"]
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

    if draft.pending_slot == PROFILE_PENDING_DISTRICT_FOR_CITY:
        district = validation.metadata["district_candidate"]
        return ProfileDraft(
            **{
                **draft.to_dict(),
                "district_candidate": district,
                "parse_status": PARSE_PARSED,
                "pending_slot": None,
                "followup_options": (),
                "retry_count": draft.retry_count + 1,
                "residence_raw": f"{draft.city_candidate} {district}",
            }
        )

    if draft.pending_slot == PROFILE_PENDING_DISTRICT_CHOICE:
        district = validation.metadata["district_candidate"]
        return ProfileDraft(
            **{
                **draft.to_dict(),
                "district_candidate": district,
                "parse_status": PARSE_PARSED,
                "pending_slot": None,
                "followup_options": (),
                "retry_count": draft.retry_count + 1,
                "residence_raw": f"{draft.city_candidate} {district}",
            }
        )

    return draft


def district_examples(city: str) -> list[str]:
    return district_examples_for_city(city)
