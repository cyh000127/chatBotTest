from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import re

from PROJECT.conversations import guided_runtime_ux as guided_ux
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


def prompt_for_state(state: str, catalog, draft: YieldDraft | None = None) -> str:
    if state == STATE_YIELD_EDIT_SELECT:
        return edit_selection_text(draft or new_draft(), catalog)
    mapping = {
        STATE_YIELD_READY: catalog.YIELD_READY_PROMPT,
        STATE_YIELD_FIELD: _text_prompt_for_state(STATE_YIELD_FIELD, catalog),
        STATE_YIELD_AMOUNT: _text_prompt_for_state(STATE_YIELD_AMOUNT, catalog),
        STATE_YIELD_DATE: _text_prompt_for_state(STATE_YIELD_DATE, catalog),
        STATE_YIELD_CONFIRM: catalog.YIELD_CONFIRM_PROMPT,
    }
    progress_label, input_mode = _step_meta(catalog, state)
    return guided_ux.format_guided_message(
        catalog,
        flow_label=catalog.GUIDED_FLOW_YIELD,
        progress_label=progress_label,
        input_mode=input_mode,
        prompt_text=mapping[state],
        draft_summary=_draft_summary(draft, catalog),
    )


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
    return guided_ux.format_guided_message(
        catalog,
        flow_label=catalog.GUIDED_FLOW_YIELD,
        progress_label=catalog.GUIDED_REVIEW_STAGE_LABEL,
        input_mode=guided_ux.BUTTON_ONLY,
        prompt_text=catalog.format_yield_confirmation(
            ready=draft.ready,
            field_name=draft.field_name or "-",
            amount_text=format_amount(draft),
            harvest_date=draft.harvest_date or "-",
        ),
    )


def confirmed_text(catalog) -> str:
    return catalog.YIELD_CONFIRMED_MESSAGE


def edit_selection_text(draft: YieldDraft, catalog) -> str:
    return guided_ux.format_guided_message(
        catalog,
        flow_label=catalog.GUIDED_FLOW_YIELD,
        progress_label=catalog.GUIDED_REVIEW_STAGE_LABEL,
        input_mode=guided_ux.BUTTON_ONLY,
        prompt_text=f"{catalog.YIELD_EDIT_MESSAGE}\n{_edit_value_lines(draft, catalog)}",
    )


def repair_message(
    target_state: str,
    catalog,
    draft: YieldDraft | None = None,
    *,
    focus_summary: str | None = None,
) -> str:
    mapping = {
        STATE_YIELD_READY: catalog.YIELD_READY_PROMPT,
        STATE_YIELD_FIELD: _text_prompt_for_state(
            STATE_YIELD_FIELD,
            catalog,
            prompt_text=catalog.YIELD_REPAIR_FIELD_MESSAGE,
        ),
        STATE_YIELD_AMOUNT: _text_prompt_for_state(
            STATE_YIELD_AMOUNT,
            catalog,
            prompt_text=catalog.YIELD_REPAIR_AMOUNT_MESSAGE,
        ),
        STATE_YIELD_DATE: _text_prompt_for_state(
            STATE_YIELD_DATE,
            catalog,
            prompt_text=catalog.YIELD_REPAIR_DATE_MESSAGE,
        ),
    }
    progress_label, input_mode = _step_meta(catalog, target_state)
    return guided_ux.format_guided_message(
        catalog,
        flow_label=catalog.GUIDED_FLOW_YIELD,
        progress_label=progress_label,
        input_mode=input_mode,
        prompt_text=mapping.get(target_state, catalog.YIELD_READY_PROMPT),
        draft_summary=focus_summary or _draft_summary(draft, catalog),
    )


def reset_draft_for_repair(draft: YieldDraft, target_state: str) -> YieldDraft:
    if target_state == STATE_YIELD_READY:
        return new_draft()
    if target_state == STATE_YIELD_FIELD:
        return update_draft(
            draft,
            field_name="",
            amount_value=None,
            amount_unit="",
            harvest_date="",
        )
    if target_state == STATE_YIELD_AMOUNT:
        return update_draft(
            draft,
            amount_value=None,
            amount_unit="",
            harvest_date="",
        )
    if target_state == STATE_YIELD_DATE:
        return update_draft(
            draft,
            harvest_date="",
        )
    return draft


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


def _step_meta(catalog, state: str) -> tuple[str, str | None]:
    mapping = {
        STATE_YIELD_READY: ("1/4", guided_ux.BUTTON_ONLY),
        STATE_YIELD_FIELD: ("2/4", guided_ux.TEXT_ALLOWED),
        STATE_YIELD_AMOUNT: ("3/4", guided_ux.TEXT_ALLOWED),
        STATE_YIELD_DATE: ("4/4", guided_ux.TEXT_ALLOWED),
        STATE_YIELD_CONFIRM: (catalog.GUIDED_REVIEW_STAGE_LABEL, guided_ux.BUTTON_ONLY),
        STATE_YIELD_EDIT_SELECT: (catalog.GUIDED_REVIEW_STAGE_LABEL, guided_ux.BUTTON_ONLY),
    }
    return mapping[state]


def _text_prompt_for_state(state: str, catalog, *, prompt_text: str | None = None) -> str:
    if state == STATE_YIELD_FIELD:
        return guided_ux.format_text_input_prompt(
            catalog,
            prompt_text=prompt_text or catalog.YIELD_FIELD_PROMPT,
            examples=catalog.YIELD_FIELD_EXAMPLES,
            unsupported_hint=catalog.YIELD_FIELD_UNSUPPORTED_INPUT_HINT,
        )
    if state == STATE_YIELD_AMOUNT:
        return guided_ux.format_text_input_prompt(
            catalog,
            prompt_text=prompt_text or catalog.YIELD_AMOUNT_PROMPT,
            examples=catalog.YIELD_AMOUNT_EXAMPLES,
            unsupported_hint=catalog.YIELD_AMOUNT_UNSUPPORTED_INPUT_HINT,
        )
    if state == STATE_YIELD_DATE:
        return guided_ux.format_text_input_prompt(
            catalog,
            prompt_text=prompt_text or catalog.YIELD_DATE_PROMPT,
            examples=catalog.YIELD_DATE_EXAMPLES,
            unsupported_hint=catalog.YIELD_DATE_UNSUPPORTED_INPUT_HINT,
        )
    return prompt_text or ""


def repair_focus_summary(target_state: str, draft: YieldDraft, catalog) -> str | None:
    label = _field_label(target_state, catalog)
    value = _field_value(target_state, draft, catalog)
    if label is None or value is None:
        return None
    return f"{label}={value}"


def _edit_value_lines(draft: YieldDraft, catalog) -> str:
    lines = []
    for state in (
        STATE_YIELD_READY,
        STATE_YIELD_FIELD,
        STATE_YIELD_AMOUNT,
        STATE_YIELD_DATE,
    ):
        label = _field_label(state, catalog)
        value = _field_value(state, draft, catalog)
        if label is None or value is None:
            continue
        lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def _field_label(state: str, catalog) -> str | None:
    mapping = {
        STATE_YIELD_READY: catalog.BUTTON_YIELD_EDIT_READY,
        STATE_YIELD_FIELD: catalog.BUTTON_YIELD_EDIT_FIELD,
        STATE_YIELD_AMOUNT: catalog.BUTTON_YIELD_EDIT_AMOUNT,
        STATE_YIELD_DATE: catalog.BUTTON_YIELD_EDIT_DATE,
    }
    return mapping.get(state)


def _field_value(state: str, draft: YieldDraft, catalog) -> str | None:
    mapping = {
        STATE_YIELD_READY: (
            catalog.BUTTON_YES
            if draft.ready
            else catalog.BUTTON_NO
            if draft.ready is False
            else "-"
        ),
        STATE_YIELD_FIELD: draft.field_name or "-",
        STATE_YIELD_AMOUNT: format_amount(draft),
        STATE_YIELD_DATE: draft.harvest_date or "-",
    }
    return mapping.get(state)


def _draft_summary(draft: YieldDraft | None, catalog) -> str | None:
    if draft is None:
        return None

    fields: list[str] = []
    if draft.ready is not None:
        ready_label = catalog.BUTTON_YES if draft.ready else catalog.BUTTON_NO
        fields.append(f"{catalog.BUTTON_YIELD_EDIT_READY}={ready_label}")
    if draft.field_name:
        fields.append(f"{catalog.BUTTON_YIELD_EDIT_FIELD}={draft.field_name}")
    if draft.amount_value is not None and draft.amount_unit:
        fields.append(f"{catalog.BUTTON_YIELD_EDIT_AMOUNT}={format_amount(draft)}")
    if draft.harvest_date:
        fields.append(f"{catalog.BUTTON_YIELD_EDIT_DATE}={draft.harvest_date}")
    if not fields:
        return None
    return ", ".join(fields)
