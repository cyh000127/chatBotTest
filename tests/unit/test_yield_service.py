from datetime import datetime

from PROJECT.conversations.yield_intake import service
from PROJECT.conversations.yield_intake.states import STATE_YIELD_AMOUNT, STATE_YIELD_CONFIRM, STATE_YIELD_DATE, STATE_YIELD_EDIT_SELECT, STATE_YIELD_FIELD, STATE_YIELD_READY
from PROJECT.i18n.catalogs import ko


def test_prompt_for_yield_steps_exists():
    assert service.prompt_for_state(STATE_YIELD_READY, ko)
    assert service.prompt_for_state(STATE_YIELD_CONFIRM, ko)
    assert service.prompt_for_state(STATE_YIELD_EDIT_SELECT, ko)


def test_yield_confirm_keyboard_exposes_edit_entry():
    layout = service.keyboard_for_state(STATE_YIELD_CONFIRM, ko)

    assert layout[0][0]["text"] == ko.BUTTON_CONFIRM
    assert layout[1][0]["text"] == ko.BUTTON_EDIT


def test_yield_edit_select_keyboard_exposes_field_targets():
    layout = service.keyboard_for_state(STATE_YIELD_EDIT_SELECT, ko)

    assert layout[0][0]["text"] == ko.BUTTON_YIELD_EDIT_READY
    assert layout[0][1]["text"] == ko.BUTTON_YIELD_EDIT_FIELD
    assert layout[1][0]["text"] == ko.BUTTON_YIELD_EDIT_AMOUNT
    assert layout[1][1]["text"] == ko.BUTTON_YIELD_EDIT_DATE


def test_parse_yield_ready_amount_and_date():
    assert service.parse_ready("예") is True
    assert service.parse_ready("아니오") is False
    assert service.parse_amount("320") == (320.0, "kg")
    assert service.parse_amount("1.5톤") == (1.5, "ton")
    assert service.parse_harvest_date("어제", now=datetime(2026, 4, 21, 10, 0, 0)) == "2026-04-20"


def test_yield_confirmation_text_formats_summary():
    draft = service.update_draft(
        service.new_draft(),
        ready=True,
        field_name="A-1",
        amount_value=320.0,
        amount_unit="kg",
        harvest_date="2026-04-21",
    )

    text = service.confirmation_text(draft, ko)

    assert "준비됨" in text
    assert "A-1" in text
    assert "320 kg" in text
    assert "2026-04-21" in text


def test_reset_yield_draft_for_repair_clears_target_and_later_fields():
    draft = service.update_draft(
        service.new_draft(),
        ready=True,
        field_name="A-1",
        amount_value=320.0,
        amount_unit="kg",
        harvest_date="2026-04-21",
    )

    field_repair = service.reset_draft_for_repair(draft, STATE_YIELD_FIELD)
    amount_repair = service.reset_draft_for_repair(draft, STATE_YIELD_AMOUNT)
    date_repair = service.reset_draft_for_repair(draft, STATE_YIELD_DATE)
    ready_repair = service.reset_draft_for_repair(draft, STATE_YIELD_READY)

    assert field_repair.ready is True
    assert field_repair.field_name == ""
    assert field_repair.amount_value is None
    assert field_repair.amount_unit == ""
    assert field_repair.harvest_date == ""
    assert amount_repair.field_name == "A-1"
    assert amount_repair.amount_value is None
    assert amount_repair.harvest_date == ""
    assert date_repair.amount_value == 320.0
    assert date_repair.harvest_date == ""
    assert ready_repair == service.new_draft()
