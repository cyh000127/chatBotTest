from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import re

from PROJECT.conversations.yield_intake import keyboards
from PROJECT.conversations.yield_intake.states import (
    STATE_YIELD_AMOUNT,
    STATE_YIELD_CONFIRM,
    STATE_YIELD_DATE,
    STATE_YIELD_EDIT_SELECT,
    STATE_YIELD_FIELD,
    STATE_YIELD_READY,
)


@dataclass(frozen=True)
class YieldDraft:
    ready: bool | None = None
    field_name: str = ""
    amount_value: float | None = None
    amount_unit: str = ""
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
        STATE_YIELD_EDIT_SELECT: catalog.YIELD_EDIT_MESSAGE,
    }
    return mapping[state]


def keyboard_for_state(state: str, catalog) -> list[list[dict[str, str]]]:
    if state == STATE_YIELD_READY:
        return keyboards.yield_ready_keyboard(catalog)
    if state == STATE_YIELD_CONFIRM:
        return keyboards.yield_confirm_keyboard(catalog)
    if state == STATE_YIELD_EDIT_SELECT:
        return keyboards.yield_edit_select_keyboard(catalog)
    return keyboards.yield_input_keyboard(catalog)


KST = timezone(timedelta(hours=9), name="KST")
YES_ALIASES = {"예", "네", "응", "yes", "y", "준비", "준비됨", "ready"}
NO_ALIASES = {"아니오", "아니요", "no", "n", "미준비", "준비안됨", "not ready"}
UNIT_ALIASES = {
    "kg": ("kg", "킬로", "킬로그램"),
    "ton": ("t", "ton", "tons", "톤"),
}


def parse_ready(text: str) -> bool | None:
    normalized = _normalize(text)
    if normalized in YES_ALIASES:
        return True
    if normalized in NO_ALIASES:
        return False
    return None


def parse_field_name(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return None
    if len(normalized) > 60:
        return None
    return normalized


def parse_amount(text: str) -> tuple[float, str] | None:
    normalized = _normalize(text).replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|킬로|킬로그램|t|ton|tons|톤)?", normalized)
    if match is None:
        return None
    value = float(match.group(1))
    unit = match.group(2) or "kg"
    canonical_unit = _canonical_unit(unit)
    if canonical_unit is None:
        return None
    return value, canonical_unit


def parse_harvest_date(text: str, *, now: datetime | None = None) -> str | None:
    current = now or datetime.now(KST)
    normalized = text.strip().lower()
    if normalized in {"오늘", "today"}:
        return current.strftime("%Y-%m-%d")
    if normalized in {"어제", "yesterday"}:
        return (current - timedelta(days=1)).strftime("%Y-%m-%d")

    for pattern in (
        r"(?P<year>\d{4})[.\-/ ](?P<month>\d{1,2})[.\-/ ](?P<day>\d{1,2})",
        r"(?P<year>\d{4})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일?",
    ):
        match = re.search(pattern, text)
        if match:
            return f"{int(match.group('year')):04d}-{int(match.group('month')):02d}-{int(match.group('day')):02d}"

    short_match = re.search(r"(?P<month>\d{1,2})[.\-/ ](?P<day>\d{1,2})", text)
    if short_match:
        return f"{current.year:04d}-{int(short_match.group('month')):02d}-{int(short_match.group('day')):02d}"
    return None


def confirmation_text(draft: YieldDraft, catalog) -> str:
    return catalog.format_yield_confirmation(
        ready=draft.ready,
        field_name=draft.field_name or "-",
        amount_text=format_amount(draft),
        harvest_date=draft.harvest_date or "-",
    )


def confirmed_text(catalog) -> str:
    return catalog.YIELD_CONFIRMED_MESSAGE


def fallback_text_for_state(state: str, catalog) -> str:
    mapping = {
        STATE_YIELD_READY: catalog.YIELD_READY_FALLBACK,
        STATE_YIELD_FIELD: catalog.YIELD_FIELD_FALLBACK,
        STATE_YIELD_AMOUNT: catalog.YIELD_AMOUNT_FALLBACK,
        STATE_YIELD_DATE: catalog.YIELD_DATE_FALLBACK,
        STATE_YIELD_CONFIRM: catalog.YIELD_CONFIRM_FALLBACK,
        STATE_YIELD_EDIT_SELECT: catalog.YIELD_EDIT_SELECT_FALLBACK,
    }
    return mapping[state]


def format_amount(draft: YieldDraft) -> str:
    if draft.amount_value is None or not draft.amount_unit:
        return "-"
    value = int(draft.amount_value) if draft.amount_value.is_integer() else draft.amount_value
    return f"{value} {draft.amount_unit}"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _canonical_unit(unit: str) -> str | None:
    for canonical, aliases in UNIT_ALIASES.items():
        if unit in aliases:
            return canonical
    return None
