from PROJECT.rule_engine import (
    detect_city_alias,
    detect_district_rule,
    district_examples_for_city,
    extract_birth_date_candidate,
    extract_korean_name_candidate,
)


def test_extract_birth_date_candidate_normalizes_two_digit_year():
    candidate, remaining = extract_birth_date_candidate("생일은 98년 4월 20일 입니다")

    assert candidate is not None
    assert candidate.field_name == "birth_date"
    assert candidate.normalized_value == "1998-04-20"
    assert "98년 4월 20일" not in remaining


def test_extract_korean_name_candidate_ignores_place_tokens():
    candidate, _ = extract_korean_name_candidate("이름은 김민수이고 서울 강남구에 살아요")

    assert candidate is not None
    assert candidate.field_name == "name"
    assert candidate.normalized_value == "김민수"


def test_detect_city_alias_returns_canonical_city():
    assert detect_city_alias("서울시 강남구") == "서울특별시"


def test_detect_district_rule_supports_ambiguous_alias():
    rule = detect_district_rule("고양 일산")

    assert rule is not None
    assert "고양시 일산동구" in rule.ambiguous_options


def test_district_examples_for_city_returns_examples():
    examples = district_examples_for_city("경기도")

    assert "성남시 분당구" in examples
