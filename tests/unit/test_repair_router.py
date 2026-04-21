from PROJECT.conversations.profile_intake import service
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_EDIT_SELECT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)
from PROJECT.dispatch.repair_router import detect_profile_view_intent, detect_repair_intent


def test_detect_birth_repair_intent():
    decision = detect_repair_intent("생일 잘못 입력했어요")
    assert decision is not None
    assert decision.target_state == STATE_PROFILE_BIRTH_YEAR


def test_detect_name_repair_intent():
    decision = detect_repair_intent("이름 수정할게요")
    assert decision is not None
    assert decision.target_state == STATE_PROFILE_NAME


def test_detect_generic_profile_repair_intent():
    decision = detect_repair_intent("프로필 잘못된거 있어 수정할래")
    assert decision is not None
    assert decision.target_state == STATE_PROFILE_EDIT_SELECT


def test_detect_profile_view_intent():
    assert detect_profile_view_intent("내 프로필 보여줘") is True
    assert detect_profile_view_intent("/프로필") is True


def test_reset_draft_for_birth_repair_clears_only_birth_fields():
    draft = service.update_draft(
        service.new_draft(),
        name="김민수",
        residence="서울 강남",
        city="서울특별시",
        district="강남구",
        birth_year=1998,
        birth_month=4,
        birth_day=20,
    )
    updated = service.reset_draft_for_repair(draft, STATE_PROFILE_BIRTH_YEAR)
    assert updated.name == "김민수"
    assert updated.city == "서울특별시"
    assert updated.birth_year is None
    assert updated.birth_month is None
    assert updated.birth_day is None


def test_reset_draft_for_residence_repair_clears_downstream_fields():
    draft = service.update_draft(
        service.new_draft(),
        name="김민수",
        residence="서울 강남",
        city="서울특별시",
        district="강남구",
        birth_year=1998,
        birth_month=4,
        birth_day=20,
    )
    updated = service.reset_draft_for_repair(draft, STATE_PROFILE_RESIDENCE)
    assert updated.name == "김민수"
    assert updated.residence == ""
    assert updated.city == "서울특별시"
    assert updated.district == "강남구"
    assert updated.birth_year == 1998


def test_reset_draft_for_city_repair_clears_only_city():
    draft = service.update_draft(
        service.new_draft(),
        name="김민수",
        residence="서울 강남",
        city="서울특별시",
        district="강남구",
        birth_year=1998,
        birth_month=4,
        birth_day=20,
    )
    updated = service.reset_draft_for_repair(draft, STATE_PROFILE_CITY)
    assert updated.city == ""
    assert updated.district == "강남구"
    assert updated.birth_year == 1998
