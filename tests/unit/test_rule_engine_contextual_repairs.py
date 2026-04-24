from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_USED,
)
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_NAME,
)
from PROJECT.rule_engine import detect_fertilizer_direct_update, detect_profile_direct_update


def test_detect_profile_direct_birth_update():
    decision = detect_profile_direct_update("생일은 1999년 9월 17일로 바꿔줘")

    assert decision is not None
    assert decision.target_state == STATE_PROFILE_BIRTH_YEAR
    assert decision.changes == {
        "birth_year": 1999,
        "birth_month": 9,
        "birth_day": 17,
    }


def test_detect_profile_direct_name_update():
    decision = detect_profile_direct_update("이름은 홍길동으로 수정할게")

    assert decision is not None
    assert decision.target_state == STATE_PROFILE_NAME
    assert decision.changes["name"] == "홍길동"


def test_detect_profile_negation_update_with_confirm_context():
    decision = detect_profile_direct_update("강남구 아니고 송파구", allow_implicit=True)

    assert decision is not None
    assert decision.target_state == STATE_PROFILE_DISTRICT
    assert decision.changes["district"] == "송파구"


def test_detect_fertilizer_direct_amount_update():
    decision = detect_fertilizer_direct_update("비료 사용량은 10kg로 바꿔줘")

    assert decision is not None
    assert decision.target_state == STATE_FERTILIZER_AMOUNT
    assert decision.changes["amount_value"] == 10.0
    assert decision.changes["amount_unit"] == "kg"


def test_detect_fertilizer_direct_date_update():
    decision = detect_fertilizer_direct_update("사용일은 2026-04-20으로 변경")

    assert decision is not None
    assert decision.target_state == STATE_FERTILIZER_DATE
    assert decision.changes["applied_date"] == "2026-04-20"


def test_detect_fertilizer_implicit_used_update_in_confirm_context():
    decision = detect_fertilizer_direct_update("안씀", allow_implicit=True)

    assert decision is not None
    assert decision.target_state == STATE_FERTILIZER_USED
    assert decision.changes["used"] is False


def test_detect_fertilizer_product_edit_request_is_not_treated_as_value():
    assert detect_fertilizer_direct_update("제품명 변경할래", allow_implicit=True) is None
    assert detect_fertilizer_direct_update("아니 제품명을 변경하고 싶다고", allow_implicit=True) is None


def test_detect_fertilizer_product_direct_value_update():
    decision = detect_fertilizer_direct_update("제품명은 한아름 복합비료로 변경할래", allow_implicit=True)

    assert decision is not None
    assert decision.changes["product_name"] == "한아름 복합비료"


def test_direct_update_requires_signal_without_context():
    assert detect_profile_direct_update("송파구") is None
    assert detect_fertilizer_direct_update("20kg") is None
