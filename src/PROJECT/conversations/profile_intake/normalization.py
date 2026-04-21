from PROJECT.rule_engine import (
    CITY_ALIASES,
    DISTRICT_EXAMPLES_BY_CITY,
    DISTRICT_RULES,
    DistrictRule,
    detect_city_alias as resolve_city_alias,
    detect_district_rule as resolve_district_rule,
    normalize_body_text,
)


def normalize_text(text: str) -> str:
    return normalize_body_text(text, locale="ko")


def detect_city(normalized_text: str) -> str | None:
    return resolve_city_alias(normalized_text)


def detect_district_rule(normalized_text: str) -> DistrictRule | None:
    return resolve_district_rule(normalized_text)


def district_examples_for_city(city: str) -> list[str]:
    return DISTRICT_EXAMPLES_BY_CITY.get(city, ["강남구", "서초구", "송파구"])
