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
    return keyboards.profile_input_keyboard(catalog)


def confirmation_text(draft: ProfileDraft, catalog) -> str:
    return catalog.format_profile_confirmation(
        name=draft.name,
        birth_date=draft.birth_date or "-",
        city=draft.city,
        district=draft.district,
        residence=draft.residence,
    )


def reset_draft_for_repair(draft: ProfileDraft, target_state: str) -> ProfileDraft:
    if target_state == STATE_PROFILE_NAME:
        return update_draft(
            draft,
            name="",
            residence="",
            city="",
            district="",
            birth_year=None,
            birth_month=None,
            birth_day=None,
        )
    if target_state == STATE_PROFILE_RESIDENCE:
        return update_draft(
            draft,
            residence="",
            city="",
            district="",
            birth_year=None,
            birth_month=None,
            birth_day=None,
        )
    if target_state == STATE_PROFILE_CITY:
        return update_draft(
            draft,
            city="",
            district="",
            birth_year=None,
            birth_month=None,
            birth_day=None,
        )
    if target_state == STATE_PROFILE_DISTRICT:
        return update_draft(
            draft,
            district="",
            birth_year=None,
            birth_month=None,
            birth_day=None,
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


def confirmed_text(catalog) -> str:
    return catalog.PROFILE_CONFIRMED_MESSAGE


def edit_text(catalog) -> str:
    return catalog.PROFILE_EDIT_MESSAGE


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
