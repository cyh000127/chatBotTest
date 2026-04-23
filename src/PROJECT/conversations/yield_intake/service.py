from dataclasses import asdict, dataclass

from PROJECT.conversations.yield_intake import keyboards
from PROJECT.conversations.yield_intake.states import (
    STATE_YIELD_AMOUNT,
    STATE_YIELD_CONFIRM,
    STATE_YIELD_DATE,
    STATE_YIELD_FIELD,
    STATE_YIELD_READY,
)


@dataclass(frozen=True)
class YieldDraft:
    ready: bool | None = None
    field_name: str = ""
    amount_text: str = ""
    harvest_date: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def new_draft() -> YieldDraft:
    return YieldDraft()


def draft_from_dict(draft_dict: dict | None) -> YieldDraft:
    if not draft_dict:
        return new_draft()
    return YieldDraft(**draft_dict)


def update_draft(draft: YieldDraft, **changes) -> YieldDraft:
    return YieldDraft(**{**draft.to_dict(), **changes})


def prompt_for_state(state: str, catalog) -> str:
    mapping = {
        STATE_YIELD_READY: catalog.YIELD_READY_PROMPT,
        STATE_YIELD_FIELD: catalog.YIELD_FIELD_PROMPT,
        STATE_YIELD_AMOUNT: catalog.YIELD_AMOUNT_PROMPT,
        STATE_YIELD_DATE: catalog.YIELD_DATE_PROMPT,
        STATE_YIELD_CONFIRM: catalog.YIELD_CONFIRM_PROMPT,
    }
    return mapping[state]


def keyboard_for_state(state: str, catalog) -> list[list[dict[str, str]]]:
    if state == STATE_YIELD_READY:
        return keyboards.yield_ready_keyboard(catalog)
    if state == STATE_YIELD_CONFIRM:
        return keyboards.yield_confirm_keyboard(catalog)
    return keyboards.yield_input_keyboard(catalog)
