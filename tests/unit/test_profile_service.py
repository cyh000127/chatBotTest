from PROJECT.conversations.profile_intake import service
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)


def test_new_draft_has_year_page():
    draft = service.new_draft()
    assert draft.year_page_start == service.datetime.now().year


def test_prompt_for_each_step_exists():
    assert service.prompt_for_state(STATE_PROFILE_NAME)
    assert service.prompt_for_state(STATE_PROFILE_RESIDENCE)
    assert service.prompt_for_state(STATE_PROFILE_CITY)
    assert service.prompt_for_state(STATE_PROFILE_DISTRICT)
    assert service.prompt_for_state(STATE_PROFILE_BIRTH_YEAR)
    assert service.prompt_for_state(STATE_PROFILE_BIRTH_MONTH)
    assert service.prompt_for_state(STATE_PROFILE_BIRTH_DAY)
    assert service.prompt_for_state(STATE_PROFILE_CONFIRM)


def test_button_parsers():
    assert service.parse_year_button("1998년") == 1998
    assert service.parse_month_button("4월") == 4
    assert service.parse_day_button("20일") == 20


def test_confirmation_text_formats_birth_date():
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
    text = service.confirmation_text(draft)
    assert "김민수" in text
    assert "서울특별시" in text
    assert "1998-04-20" in text
