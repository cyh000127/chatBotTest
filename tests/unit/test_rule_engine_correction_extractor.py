from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_PRODUCT
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_BIRTH_YEAR, STATE_PROFILE_NAME
from PROJECT.rule_engine.correction_extractor import (
    extract_fertilizer_correction_pattern,
    extract_profile_correction_pattern,
)


def test_extract_profile_target_only_correction_pattern():
    decision = extract_profile_correction_pattern("생일 수정할래")

    assert decision is not None
    assert decision.target_state == STATE_PROFILE_BIRTH_YEAR
    assert decision.candidate_value is None


def test_extract_profile_value_correction_pattern():
    decision = extract_profile_correction_pattern("이름은 홍길동으로 바꿀래")

    assert decision is not None
    assert decision.target_state == STATE_PROFILE_NAME
    assert decision.candidate_value == "홍길동"


def test_extract_fertilizer_value_correction_pattern():
    decision = extract_fertilizer_correction_pattern("제품명은 한아름 복합비료로 변경하고 싶어")

    assert decision is not None
    assert decision.target_state == STATE_FERTILIZER_PRODUCT
    assert decision.candidate_value == "한아름 복합비료"


def test_extract_fertilizer_target_only_correction_pattern():
    decision = extract_fertilizer_correction_pattern("제품명 변경할래")

    assert decision is not None
    assert decision.target_state == STATE_FERTILIZER_PRODUCT
    assert decision.candidate_value is None
