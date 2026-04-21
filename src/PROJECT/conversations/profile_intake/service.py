from dataclasses import asdict, dataclass
from datetime import datetime
import re

from PROJECT.conversations.profile_intake import keyboards
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

@dataclass(frozen=True)
class ProfileDraft:
    name: str = ""
    residence: str = ""
    city: str = ""
    district: str = ""
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    year_page_start: int = datetime.now().year

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def birth_date(self) -> str | None:
        if self.birth_year and self.birth_month and self.birth_day:
            return f"{self.birth_year:04d}-{self.birth_month:02d}-{self.birth_day:02d}"
        return None


def new_draft() -> ProfileDraft:
    return ProfileDraft(year_page_start=datetime.now().year)


def draft_from_dict(draft_dict: dict | None) -> ProfileDraft:
    if not draft_dict:
        return new_draft()
    return ProfileDraft(**draft_dict)


def update_draft(draft: ProfileDraft, **changes) -> ProfileDraft:
    return ProfileDraft(**{**draft.to_dict(), **changes})


def prompt_for_state(state: str, catalog) -> str:
    if state == STATE_PROFILE_NAME:
        return catalog.PROFILE_NAME_PROMPT
    if state == STATE_PROFILE_RESIDENCE:
        return catalog.PROFILE_RESIDENCE_PROMPT
    if state == STATE_PROFILE_CITY:
        return catalog.PROFILE_CITY_PROMPT
    if state == STATE_PROFILE_DISTRICT:
        return catalog.PROFILE_DISTRICT_PROMPT
    if state == STATE_PROFILE_BIRTH_YEAR:
        return catalog.PROFILE_BIRTH_YEAR_PROMPT
    if state == STATE_PROFILE_BIRTH_MONTH:
        return catalog.PROFILE_BIRTH_MONTH_PROMPT
    if state == STATE_PROFILE_BIRTH_DAY:
        return catalog.PROFILE_BIRTH_DAY_PROMPT
    if state == STATE_PROFILE_EDIT_SELECT:
        return catalog.PROFILE_EDIT_MESSAGE
    return catalog.PROFILE_ENTRY_MESSAGE


def keyboard_for_state(state: str, draft: ProfileDraft, catalog) -> list[list[str]]:
    if state == STATE_PROFILE_BIRTH_YEAR:
        return keyboards.profile_birth_year_keyboard(draft.year_page_start, catalog)
    if state == STATE_PROFILE_BIRTH_MONTH:
        return keyboards.profile_birth_month_keyboard(catalog)
    if state == STATE_PROFILE_BIRTH_DAY and draft.birth_year and draft.birth_month:
        return keyboards.profile_birth_day_keyboard(draft.birth_year, draft.birth_month, catalog)
    if state == STATE_PROFILE_CONFIRM:
        return keyboards.profile_confirm_keyboard(catalog)
    if state == STATE_PROFILE_EDIT_SELECT:
        return keyboards.profile_edit_select_keyboard(catalog)
    return keyboards.profile_input_keyboard(catalog)


def confirmation_text(draft: ProfileDraft, catalog) -> str:
    return catalog.format_profile_confirmation(
        name=draft.name,
        birth_date=draft.birth_date or "-",
        city=draft.city,
        district=draft.district,
        residence=draft.residence,
    )


def summary_text(draft: ProfileDraft, catalog) -> str:
    return catalog.format_profile_summary(
        name=draft.name,
        birth_date=draft.birth_date or "-",
        city=draft.city,
        district=draft.district,
        residence=draft.residence,
    )


def edit_selection_text(draft: ProfileDraft, catalog) -> str:
    return f"{summary_text(draft, catalog)}\n\n{catalog.PROFILE_EDIT_MESSAGE}"


def no_profile_text(catalog) -> str:
    return catalog.PROFILE_NOT_FOUND_MESSAGE


def reset_draft_for_repair(draft: ProfileDraft, target_state: str) -> ProfileDraft:
    if target_state == STATE_PROFILE_NAME:
        return update_draft(
            draft,
            name="",
        )
    if target_state == STATE_PROFILE_RESIDENCE:
        return update_draft(
            draft,
            residence="",
        )
    if target_state == STATE_PROFILE_CITY:
        return update_draft(
            draft,
            city="",
        )
    if target_state == STATE_PROFILE_DISTRICT:
        return update_draft(
            draft,
            district="",
        )
    if target_state == STATE_PROFILE_BIRTH_YEAR:
        return update_draft(
            draft,
            birth_year=None,
            birth_month=None,
            birth_day=None,
        )
    return draft


def parse_name(text: str) -> str | None:
    normalized = text.strip()
    if not normalized:
        return None
    if len(normalized) > 20:
        return None
    return normalized


def parse_free_text(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.strip())
    return normalized or None


def parse_year_button(text: str) -> int | None:
    match = re.fullmatch(r"(\d{4})(?:년)?", text.strip())
    return int(match.group(1)) if match else None


def parse_month_button(text: str) -> int | None:
    match = re.fullmatch(r"(\d{1,2})(?:월)?", text.strip())
    if not match:
        return None
    month = int(match.group(1))
    return month if 1 <= month <= 12 else None


def parse_day_button(text: str) -> int | None:
    match = re.fullmatch(r"(\d{1,2})(?:일)?", text.strip())
    if not match:
        return None
    day = int(match.group(1))
    return day if 1 <= day <= 31 else None


def parse_birth_date_text(text: str) -> tuple[int, int, int] | None:
    for pattern in (
        r"(?P<year>\d{4})[.\-/ ](?P<month>\d{1,2})[.\-/ ](?P<day>\d{1,2})",
        r"(?P<year>\d{4})년\s*(?P<month>\d{1,2})월\s*(?P<day>\d{1,2})일?",
    ):
        match = re.search(pattern, text)
        if not match:
            continue
        year = int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        if 1900 <= year <= datetime.now().year and 1 <= month <= 12 and 1 <= day <= 31:
            return year, month, day
    return None


def confirmed_text(catalog) -> str:
    return catalog.PROFILE_CONFIRMED_MESSAGE


def edit_text(catalog) -> str:
    return catalog.PROFILE_EDIT_MESSAGE


def change_preview_text(before: ProfileDraft, after: ProfileDraft, target_state: str, catalog) -> str:
    field_labels = {
        STATE_PROFILE_NAME: catalog.BUTTON_EDIT_NAME,
        STATE_PROFILE_RESIDENCE: catalog.BUTTON_EDIT_RESIDENCE,
        STATE_PROFILE_CITY: catalog.BUTTON_EDIT_CITY,
        STATE_PROFILE_DISTRICT: catalog.BUTTON_EDIT_DISTRICT,
        STATE_PROFILE_BIRTH_YEAR: catalog.BUTTON_EDIT_BIRTH_DATE,
    }
    before_values = {
        STATE_PROFILE_NAME: before.name or "-",
        STATE_PROFILE_RESIDENCE: before.residence or "-",
        STATE_PROFILE_CITY: before.city or "-",
        STATE_PROFILE_DISTRICT: before.district or "-",
        STATE_PROFILE_BIRTH_YEAR: before.birth_date or "-",
    }
    after_values = {
        STATE_PROFILE_NAME: after.name or "-",
        STATE_PROFILE_RESIDENCE: after.residence or "-",
        STATE_PROFILE_CITY: after.city or "-",
        STATE_PROFILE_DISTRICT: after.district or "-",
        STATE_PROFILE_BIRTH_YEAR: after.birth_date or "-",
    }
    return catalog.format_change_preview(
        field_label=field_labels.get(target_state, catalog.BUTTON_EDIT),
        before_value=before_values.get(target_state, "-"),
        after_value=after_values.get(target_state, "-"),
    )


def repair_confirmation_text(target_state: str, catalog) -> str:
    if target_state == STATE_PROFILE_EDIT_SELECT:
        return catalog.PROFILE_EDIT_SELECTION_CONFIRMATION_MESSAGE.format(edit_button=catalog.BUTTON_EDIT_START)

    field_labels = {
        STATE_PROFILE_NAME: catalog.BUTTON_EDIT_NAME,
        STATE_PROFILE_RESIDENCE: catalog.BUTTON_EDIT_RESIDENCE,
        STATE_PROFILE_CITY: catalog.BUTTON_EDIT_CITY,
        STATE_PROFILE_DISTRICT: catalog.BUTTON_EDIT_DISTRICT,
        STATE_PROFILE_BIRTH_YEAR: catalog.BUTTON_EDIT_BIRTH_DATE,
    }
    field_label = field_labels.get(target_state, catalog.BUTTON_EDIT)
    return catalog.format_repair_confirmation(field_label=field_label, edit_button=catalog.BUTTON_EDIT_START)


def fallback_text_for_state(state: str, catalog) -> str:
    mapping = {
        STATE_PROFILE_NAME: catalog.PROFILE_NAME_FALLBACK,
        STATE_PROFILE_RESIDENCE: catalog.PROFILE_RESIDENCE_FALLBACK,
        STATE_PROFILE_CITY: catalog.PROFILE_CITY_FALLBACK,
        STATE_PROFILE_DISTRICT: catalog.PROFILE_DISTRICT_FALLBACK,
        STATE_PROFILE_BIRTH_YEAR: catalog.PROFILE_BIRTH_YEAR_FALLBACK,
        STATE_PROFILE_BIRTH_MONTH: catalog.PROFILE_BIRTH_MONTH_FALLBACK,
        STATE_PROFILE_BIRTH_DAY: catalog.PROFILE_BIRTH_DAY_FALLBACK,
        STATE_PROFILE_CONFIRM: catalog.PROFILE_CONFIRM_FALLBACK,
        STATE_PROFILE_EDIT_SELECT: catalog.PROFILE_EDIT_SELECT_FALLBACK,
    }
    return mapping.get(state, catalog.PROFILE_ENTRY_MESSAGE)


def repair_message(target_state: str, catalog) -> str:
    mapping = {
        STATE_PROFILE_NAME: catalog.PROFILE_REPAIR_NAME_MESSAGE,
        STATE_PROFILE_RESIDENCE: catalog.PROFILE_REPAIR_RESIDENCE_MESSAGE,
        STATE_PROFILE_CITY: catalog.PROFILE_REPAIR_CITY_MESSAGE,
        STATE_PROFILE_DISTRICT: catalog.PROFILE_REPAIR_DISTRICT_MESSAGE,
        STATE_PROFILE_BIRTH_YEAR: catalog.PROFILE_REPAIR_BIRTH_MESSAGE,
    }
    return mapping.get(target_state, catalog.PROFILE_EDIT_MESSAGE)
