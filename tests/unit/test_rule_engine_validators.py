from PROJECT.rule_engine import (
    PROFILE_PENDING_BIRTH_DATE,
    PROFILE_PENDING_DISTRICT_CHOICE,
    PROFILE_PENDING_DISTRICT_FOR_CITY,
    PROFILE_PENDING_NAME,
    ValidationClassification,
    detect_district_rule,
    validate_profile_candidates,
    validate_profile_followup,
)


def test_validate_profile_candidates_marks_missing_name_first():
    result = validate_profile_candidates(
        name_candidate=None,
        birth_date_candidate="1998-04-20",
        city_candidate="서울특별시",
        district_rule=None,
    )

    assert result.classification == ValidationClassification.REASK
    assert result.metadata["pending_slot"] == PROFILE_PENDING_NAME


def test_validate_profile_candidates_requires_district_when_only_city_known():
    result = validate_profile_candidates(
        name_candidate="김민수",
        birth_date_candidate="1998-04-20",
        city_candidate="서울특별시",
        district_rule=None,
    )

    assert result.classification == ValidationClassification.REASK
    assert result.metadata["pending_slot"] == PROFILE_PENDING_DISTRICT_FOR_CITY


def test_validate_profile_candidates_marks_ambiguous_district_choice():
    result = validate_profile_candidates(
        name_candidate="김민수",
        birth_date_candidate="1998-04-20",
        city_candidate=None,
        district_rule=detect_district_rule("고양 일산"),
    )

    assert result.classification == ValidationClassification.REASK
    assert result.metadata["pending_slot"] == PROFILE_PENDING_DISTRICT_CHOICE
    assert "고양시 일산동구" in result.metadata["followup_options"]


def test_validate_profile_followup_resolves_city_for_district():
    result = validate_profile_followup(
        pending_slot="city_for_district",
        raw_text="서울시",
        district_candidate="강남구",
    )

    assert result.classification == ValidationClassification.RESOLVED
    assert result.metadata["city_candidate"] == "서울특별시"


def test_validate_profile_followup_reasks_for_invalid_district_choice():
    result = validate_profile_followup(
        pending_slot=PROFILE_PENDING_DISTRICT_CHOICE,
        raw_text="아무거나",
        city_candidate="경기도",
        followup_options=("고양시 일산동구", "고양시 일산서구"),
    )

    assert result.classification == ValidationClassification.REASK


def test_validate_profile_candidates_marks_missing_birth_after_name():
    result = validate_profile_candidates(
        name_candidate="김민수",
        birth_date_candidate=None,
        city_candidate="서울특별시",
        district_rule=None,
    )

    assert result.classification == ValidationClassification.REASK
    assert result.metadata["pending_slot"] == PROFILE_PENDING_BIRTH_DATE
