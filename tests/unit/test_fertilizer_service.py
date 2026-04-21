from datetime import datetime

from PROJECT.conversations.fertilizer_intake import service
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_USED,
)
from PROJECT.i18n.catalogs import ko


def test_prompt_for_fertilizer_steps_exists():
    assert service.prompt_for_state(STATE_FERTILIZER_USED, ko)
    assert service.prompt_for_state(STATE_FERTILIZER_KIND, ko)
    assert service.prompt_for_state(STATE_FERTILIZER_CONFIRM, ko)


def test_parse_used_kind_amount_and_date():
    assert service.parse_used("예") is True
    assert service.parse_used("아니오") is False
    assert service.parse_kind("복합비료") == "compound"
    assert service.parse_amount("20kg") == (20.0, "kg")
    assert service.parse_amount("한 포") == (1.0, "bag")
    assert service.parse_applied_date("어제", now=datetime(2026, 4, 21, 10, 0, 0)) == "2026-04-20"


def test_fertilizer_confirmation_text_formats_summary():
    draft = service.update_draft(
        service.new_draft(),
        used=True,
        kind="compound",
        product_name="한아름 복합비료",
        amount_value=20.0,
        amount_unit="kg",
        applied_date="2026-04-21",
    )

    text = service.confirmation_text(draft, ko)

    assert "복합비료" in text
    assert "한아름 복합비료" in text
    assert "20 kg" in text
    assert "2026-04-21" in text


def test_fertilizer_edit_selection_text_and_repair_confirmation():
    draft = service.update_draft(
        service.new_draft(),
        used=True,
        kind="compound",
        product_name="한아름 복합비료",
        amount_value=20.0,
        amount_unit="kg",
        applied_date="2026-04-21",
    )

    summary = service.edit_selection_text(draft, ko)
    confirmation = service.repair_confirmation_text(STATE_FERTILIZER_KIND, ko)

    assert ko.FERTILIZER_EDIT_MESSAGE in summary
    assert "한아름 복합비료" in summary
    assert ko.BUTTON_FERTILIZER_EDIT_KIND in confirmation
    assert ko.BUTTON_EDIT_START in confirmation
