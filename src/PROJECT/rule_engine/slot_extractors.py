import re

from PROJECT.rule_engine.aliases import CITY_ALIASES, DISTRICT_RULES
from PROJECT.rule_engine.contracts import ResolutionCandidate, RuleSource
from PROJECT.rule_engine.normalizer import normalize_body_text

PROFILE_NAME_STOPWORDS = {
    "이름",
    "생일",
    "생년월일",
    "거주지",
    "저는",
    "전",
    "저",
    "살아요",
    "살고",
    "입니다",
    "이고",
    "는",
    "은",
    "요",
    "김",
    "박",
    "이",
}

PROFILE_PLACE_TOKENS = set(CITY_ALIASES) | {
    token
    for rule in DISTRICT_RULES
    for token in rule.trigger.split()
}


def _convert_year(year: int) -> int:
    if year >= 100:
        return year
    return 2000 + year if year <= 29 else 1900 + year


def extract_birth_date_candidate(text: str) -> tuple[ResolutionCandidate | None, str]:
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
        return (
            ResolutionCandidate(
                field_name="birth_date",
                raw_value=match.group(0),
                candidate_type="date",
                source=RuleSource.SLOT_EXTRACTOR,
                normalized_value=birth,
            ),
            text.replace(match.group(0), " "),
        )
    return None, text


def extract_korean_name_candidate(
    text: str,
    *,
    stopwords: set[str] | None = None,
    reserved_tokens: set[str] | None = None,
) -> tuple[ResolutionCandidate | None, str]:
    stopwords = stopwords or PROFILE_NAME_STOPWORDS
    reserved_tokens = reserved_tokens or PROFILE_PLACE_TOKENS

    labeled = re.search(r"이름(?:은|는|이)?\s*([가-힣]{2,4})", text)
    if labeled:
        candidate = labeled.group(1)
        return (
            ResolutionCandidate(
                field_name="name",
                raw_value=candidate,
                candidate_type="person_name",
                source=RuleSource.SLOT_EXTRACTOR,
                normalized_value=candidate,
            ),
            text.replace(labeled.group(0), " "),
        )

    for token in normalize_body_text(text, locale="ko").split():
        if not re.fullmatch(r"[가-힣]{2,4}", token):
            continue
        if token in stopwords:
            continue
        if token in reserved_tokens:
            continue
        if token.endswith(("시", "구", "군", "도")):
            continue
        return (
            ResolutionCandidate(
                field_name="name",
                raw_value=token,
                candidate_type="person_name",
                source=RuleSource.SLOT_EXTRACTOR,
                normalized_value=token,
            ),
            text.replace(token, " ", 1),
        )

    return None, text
