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
from PROJECT.i18n.catalogs import ko


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


def prompt_for_state(state: str) -> str:
    if state == STATE_PROFILE_NAME:
        return ko.PROFILE_NAME_PROMPT
    if state == STATE_PROFILE_RESIDENCE:
        return ko.PROFILE_RESIDENCE_PROMPT
    if state == STATE_PROFILE_CITY:
        return ko.PROFILE_CITY_PROMPT
    if state == STATE_PROFILE_DISTRICT:
        return ko.PROFILE_DISTRICT_PROMPT
    if state == STATE_PROFILE_BIRTH_YEAR:
        return ko.PROFILE_BIRTH_YEAR_PROMPT
    if state == STATE_PROFILE_BIRTH_MONTH:
        return ko.PROFILE_BIRTH_MONTH_PROMPT
    if state == STATE_PROFILE_BIRTH_DAY:
        return ko.PROFILE_BIRTH_DAY_PROMPT
    return ko.PROFILE_ENTRY_MESSAGE


def keyboard_for_state(state: str, draft: ProfileDraft) -> list[list[str]]:
    if state == STATE_PROFILE_BIRTH_YEAR:
        return keyboards.profile_birth_year_keyboard(draft.year_page_start)
    if state == STATE_PROFILE_BIRTH_MONTH:
        return keyboards.profile_birth_month_keyboard()
    if state == STATE_PROFILE_BIRTH_DAY and draft.birth_year and draft.birth_month:
        return keyboards.profile_birth_day_keyboard(draft.birth_year, draft.birth_month)
    if state == STATE_PROFILE_CONFIRM:
        return keyboards.profile_confirm_keyboard()
    return keyboards.profile_input_keyboard()


def confirmation_text(draft: ProfileDraft) -> str:
    return ko.format_profile_confirmation(
        name=draft.name,
        birth_date=draft.birth_date or "-",
        city=draft.city,
        district=draft.district,
        residence=draft.residence,
    )


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
    match = re.fullmatch(r"(\d{4})년", text.strip())
    return int(match.group(1)) if match else None


def parse_month_button(text: str) -> int | None:
    match = re.fullmatch(r"(\d{1,2})월", text.strip())
    if not match:
        return None
    month = int(match.group(1))
    return month if 1 <= month <= 12 else None


def parse_day_button(text: str) -> int | None:
    match = re.fullmatch(r"(\d{1,2})일", text.strip())
    if not match:
        return None
    day = int(match.group(1))
    return day if 1 <= day <= 31 else None


def confirmed_text() -> str:
    return ko.PROFILE_CONFIRMED_MESSAGE


def edit_text() -> str:
    return ko.PROFILE_EDIT_MESSAGE


def fallback_text_for_state(state: str) -> str:
    mapping = {
        STATE_PROFILE_NAME: ko.PROFILE_NAME_FALLBACK,
        STATE_PROFILE_RESIDENCE: ko.PROFILE_RESIDENCE_FALLBACK,
        STATE_PROFILE_CITY: ko.PROFILE_CITY_FALLBACK,
        STATE_PROFILE_DISTRICT: ko.PROFILE_DISTRICT_FALLBACK,
        STATE_PROFILE_BIRTH_YEAR: ko.PROFILE_BIRTH_YEAR_FALLBACK,
        STATE_PROFILE_BIRTH_MONTH: ko.PROFILE_BIRTH_MONTH_FALLBACK,
        STATE_PROFILE_BIRTH_DAY: ko.PROFILE_BIRTH_DAY_FALLBACK,
        STATE_PROFILE_CONFIRM: ko.PROFILE_CONFIRM_FALLBACK,
    }
    return mapping.get(state, ko.PROFILE_ENTRY_MESSAGE)
