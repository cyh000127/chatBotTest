from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import re

from PROJECT.conversations.fertilizer_intake import keyboards
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)

KST = timezone(timedelta(hours=9), name="KST")

KIND_ALIASES = {
    "compound": ("복합", "복합비료", "compound"),
    "urea": ("요소", "요소비료", "urea"),
    "compost": ("퇴비", "유기질", "compost"),
    "liquid": ("액비", "liquid"),
}

YES_ALIASES = {"예", "네", "응", "yes", "y", "사용", "썼어요", "썼어", "사용했어요", "used"}
NO_ALIASES = {"아니오", "아니요", "no", "n", "안씀", "안썼어요", "안썼어", "미사용", "사용안함", "not used"}
AMOUNT_WORDS = {
    "반": 0.5,
    "한": 1,
    "두": 2,
    "세": 3,
    "네": 4,
}
UNIT_ALIASES = {
    "kg": ("kg", "킬로", "킬로그램"),
    "bag": ("포", "포대", "bag", "bags"),
    "l": ("l", "리터", "liter", "liters"),
}


@dataclass(frozen=True)
class FertilizerDraft:
    used: bool | None = None
    kind: str = ""
    product_name: str = ""
    amount_value: float | None = None
    amount_unit: str = ""
    applied_date: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def new_draft() -> FertilizerDraft:
    return FertilizerDraft()


def draft_from_dict(draft_dict: dict | None) -> FertilizerDraft:
    if not draft_dict:
        return new_draft()
    return FertilizerDraft(**draft_dict)


def update_draft(draft: FertilizerDraft, **changes) -> FertilizerDraft:
    return FertilizerDraft(**{**draft.to_dict(), **changes})


def prompt_for_state(state: str, catalog) -> str:
    mapping = {
        STATE_FERTILIZER_USED: catalog.FERTILIZER_USED_PROMPT,
        STATE_FERTILIZER_KIND: catalog.FERTILIZER_KIND_PROMPT,
        STATE_FERTILIZER_PRODUCT: catalog.FERTILIZER_PRODUCT_PROMPT,
        STATE_FERTILIZER_AMOUNT: catalog.FERTILIZER_AMOUNT_PROMPT,
        STATE_FERTILIZER_DATE: catalog.FERTILIZER_DATE_PROMPT,
        STATE_FERTILIZER_CONFIRM: catalog.FERTILIZER_CONFIRM_PROMPT,
    }
    return mapping[state]


def keyboard_for_state(state: str, catalog) -> list[list[dict[str, str]]]:
    if state == STATE_FERTILIZER_USED:
        return keyboards.fertilizer_binary_keyboard(catalog)
    if state == STATE_FERTILIZER_KIND:
        return keyboards.fertilizer_kind_keyboard(catalog)
    if state == STATE_FERTILIZER_CONFIRM:
        return keyboards.fertilizer_confirm_keyboard(catalog)
    return keyboards.fertilizer_input_keyboard(catalog)


def parse_used(text: str) -> bool | None:
    normalized = _normalize(text)
    if normalized in YES_ALIASES:
        return True
    if normalized in NO_ALIASES:
        return False
    return None


def parse_kind(text: str) -> str | None:
    normalized = _normalize(text)
    for kind, aliases in KIND_ALIASES.items():
        if normalized in aliases:
            return kind
    return None


def parse_product_name(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.strip())
    if not normalized:
        return None
    if len(normalized) > 60:
        return None
    return normalized


def parse_amount(text: str) -> tuple[float, str] | None:
    normalized = _normalize(text).replace(",", "")
    numeric_match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|킬로|킬로그램|포|포대|bag|bags|l|리터|liter|liters)", normalized)
    if numeric_match:
        value = float(numeric_match.group(1))
        unit = _canonical_unit(numeric_match.group(2))
        if unit is not None:
            return value, unit

    word_match = re.search(r"(반|한|두|세|네)\s*(포|포대|bag|bags)", normalized)
    if word_match:
        return float(AMOUNT_WORDS[word_match.group(1)]), "bag"

    return None


def parse_applied_date(text: str, *, now: datetime | None = None) -> str | None:
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


def confirmation_text(draft: FertilizerDraft, catalog) -> str:
    return catalog.format_fertilizer_confirmation(
        used=draft.used,
        kind_label=catalog.FERTILIZER_KIND_LABELS.get(draft.kind, draft.kind or "-"),
        product_name=draft.product_name or "-",
        amount_text=format_amount(draft),
        applied_date=draft.applied_date or "-",
    )


def summary_text(draft: FertilizerDraft, catalog) -> str:
    return catalog.format_fertilizer_summary(
        used=draft.used,
        kind_label=catalog.FERTILIZER_KIND_LABELS.get(draft.kind, draft.kind or "-"),
        product_name=draft.product_name or "-",
        amount_text=format_amount(draft),
        applied_date=draft.applied_date or "-",
    )


def edit_selection_text(draft: FertilizerDraft, catalog) -> str:
    return f"{summary_text(draft, catalog)}\n\n{catalog.FERTILIZER_EDIT_MESSAGE}"


def confirmed_text(catalog) -> str:
    return catalog.FERTILIZER_CONFIRMED_MESSAGE


def no_fertilizer_text(catalog) -> str:
    return catalog.FERTILIZER_NOT_FOUND_MESSAGE


def reset_draft_for_repair(draft: FertilizerDraft, target_state: str) -> FertilizerDraft:
    if target_state == STATE_FERTILIZER_USED:
        return new_draft()
    if target_state == STATE_FERTILIZER_KIND:
        return update_draft(
            draft,
            kind="",
            product_name="",
            amount_value=None,
            amount_unit="",
            applied_date="",
        )
    if target_state == STATE_FERTILIZER_PRODUCT:
        return update_draft(
            draft,
            product_name="",
            amount_value=None,
            amount_unit="",
            applied_date="",
        )
    if target_state == STATE_FERTILIZER_AMOUNT:
        return update_draft(
            draft,
            amount_value=None,
            amount_unit="",
            applied_date="",
        )
    if target_state == STATE_FERTILIZER_DATE:
        return update_draft(
            draft,
            applied_date="",
        )
    return draft


def repair_message(target_state: str, catalog) -> str:
    mapping = {
        STATE_FERTILIZER_USED: catalog.FERTILIZER_REPAIR_USED_MESSAGE,
        STATE_FERTILIZER_KIND: catalog.FERTILIZER_REPAIR_KIND_MESSAGE,
        STATE_FERTILIZER_PRODUCT: catalog.FERTILIZER_REPAIR_PRODUCT_MESSAGE,
        STATE_FERTILIZER_AMOUNT: catalog.FERTILIZER_REPAIR_AMOUNT_MESSAGE,
        STATE_FERTILIZER_DATE: catalog.FERTILIZER_REPAIR_DATE_MESSAGE,
    }
    return mapping.get(target_state, catalog.FERTILIZER_USED_PROMPT)


def repair_confirmation_text(target_state: str, catalog) -> str:
    if target_state == STATE_FERTILIZER_CONFIRM:
        return catalog.FERTILIZER_EDIT_SELECTION_CONFIRMATION_MESSAGE.format(edit_button=catalog.BUTTON_EDIT_START)

    field_labels = {
        STATE_FERTILIZER_USED: catalog.BUTTON_FERTILIZER_EDIT_USED,
        STATE_FERTILIZER_KIND: catalog.BUTTON_FERTILIZER_EDIT_KIND,
        STATE_FERTILIZER_PRODUCT: catalog.BUTTON_FERTILIZER_EDIT_PRODUCT,
        STATE_FERTILIZER_AMOUNT: catalog.BUTTON_FERTILIZER_EDIT_AMOUNT,
        STATE_FERTILIZER_DATE: catalog.BUTTON_FERTILIZER_EDIT_DATE,
    }
    field_label = field_labels.get(target_state, catalog.BUTTON_EDIT)
    return catalog.format_repair_confirmation(field_label=field_label, edit_button=catalog.BUTTON_EDIT_START)


def change_preview_text(before: FertilizerDraft, after: FertilizerDraft, target_state: str, catalog) -> str:
    field_labels = {
        STATE_FERTILIZER_USED: catalog.BUTTON_FERTILIZER_EDIT_USED,
        STATE_FERTILIZER_KIND: catalog.BUTTON_FERTILIZER_EDIT_KIND,
        STATE_FERTILIZER_PRODUCT: catalog.BUTTON_FERTILIZER_EDIT_PRODUCT,
        STATE_FERTILIZER_AMOUNT: catalog.BUTTON_FERTILIZER_EDIT_AMOUNT,
        STATE_FERTILIZER_DATE: catalog.BUTTON_FERTILIZER_EDIT_DATE,
    }
    before_values = {
        STATE_FERTILIZER_USED: catalog.FERTILIZER_USED_LABEL_YES if before.used else catalog.FERTILIZER_USED_LABEL_NO if before.used is False else "-",
        STATE_FERTILIZER_KIND: catalog.FERTILIZER_KIND_LABELS.get(before.kind, before.kind or "-"),
        STATE_FERTILIZER_PRODUCT: before.product_name or "-",
        STATE_FERTILIZER_AMOUNT: format_amount(before),
        STATE_FERTILIZER_DATE: before.applied_date or "-",
    }
    after_values = {
        STATE_FERTILIZER_USED: catalog.FERTILIZER_USED_LABEL_YES if after.used else catalog.FERTILIZER_USED_LABEL_NO if after.used is False else "-",
        STATE_FERTILIZER_KIND: catalog.FERTILIZER_KIND_LABELS.get(after.kind, after.kind or "-"),
        STATE_FERTILIZER_PRODUCT: after.product_name or "-",
        STATE_FERTILIZER_AMOUNT: format_amount(after),
        STATE_FERTILIZER_DATE: after.applied_date or "-",
    }
    return catalog.format_change_preview(
        field_label=field_labels.get(target_state, catalog.BUTTON_EDIT),
        before_value=before_values.get(target_state, "-"),
        after_value=after_values.get(target_state, "-"),
    )


def fallback_text_for_state(state: str, catalog) -> str:
    mapping = {
        STATE_FERTILIZER_USED: catalog.FERTILIZER_USED_FALLBACK,
        STATE_FERTILIZER_KIND: catalog.FERTILIZER_KIND_FALLBACK,
        STATE_FERTILIZER_PRODUCT: catalog.FERTILIZER_PRODUCT_FALLBACK,
        STATE_FERTILIZER_AMOUNT: catalog.FERTILIZER_AMOUNT_FALLBACK,
        STATE_FERTILIZER_DATE: catalog.FERTILIZER_DATE_FALLBACK,
        STATE_FERTILIZER_CONFIRM: catalog.FERTILIZER_CONFIRM_FALLBACK,
    }
    return mapping[state]


def format_amount(draft: FertilizerDraft) -> str:
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
