from PROJECT.conversations.profile_intake import service
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_EDIT_SELECT,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)
from PROJECT.i18n.catalogs import ko


def test_new_draft_has_year_page():
    draft = service.new_draft()
    assert draft.year_page_start == service.datetime.now().year


def test_prompt_for_each_step_exists():
    assert service.prompt_for_state(STATE_PROFILE_NAME, ko)
    assert service.prompt_for_state(STATE_PROFILE_RESIDENCE, ko)
    assert service.prompt_for_state(STATE_PROFILE_CITY, ko)
    assert service.prompt_for_state(STATE_PROFILE_DISTRICT, ko)
    assert service.prompt_for_state(STATE_PROFILE_BIRTH_YEAR, ko)
    assert service.prompt_for_state(STATE_PROFILE_BIRTH_MONTH, ko)
    assert service.prompt_for_state(STATE_PROFILE_BIRTH_DAY, ko)
    assert service.prompt_for_state(STATE_PROFILE_CONFIRM, ko)
    assert service.prompt_for_state(STATE_PROFILE_EDIT_SELECT, ko)


def test_button_parsers():
    assert service.parse_year_button("1998년") == 1998
    assert service.parse_year_button("1998") == 1998
    assert service.parse_month_button("4월") == 4
    assert service.parse_month_button("4") == 4
    assert service.parse_day_button("20일") == 20
    assert service.parse_day_button("20") == 20


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
    text = service.confirmation_text(draft, ko)
    assert "김민수" in text
    assert "서울특별시" in text
    assert "1998-04-20" in text


def test_edit_select_keyboard_contains_profile_fields():
    keyboard = service.keyboard_for_state(STATE_PROFILE_EDIT_SELECT, service.new_draft(), ko)
    labels = {button["text"] for row in keyboard for button in row}
    assert ko.BUTTON_EDIT_NAME in labels
    assert ko.BUTTON_EDIT_RESIDENCE in labels
    assert ko.BUTTON_EDIT_CITY in labels
    assert ko.BUTTON_EDIT_DISTRICT in labels
    assert ko.BUTTON_EDIT_BIRTH_DATE in labels


def test_profile_repair_confirmation_text_mentions_target_field():
    text = service.repair_confirmation_text(STATE_PROFILE_NAME, ko)

    assert ko.BUTTON_EDIT_NAME in text
    assert ko.BUTTON_EDIT_START in text


def test_profile_change_preview_text_shows_before_and_after():
    before = service.update_draft(service.new_draft(), name="김민수")
    after = service.update_draft(before, name="홍길동")

    text = service.change_preview_text(before, after, STATE_PROFILE_NAME, ko)

    assert "이전" in text
    assert "변경" in text
    assert "김민수" in text
    assert "홍길동" in text
