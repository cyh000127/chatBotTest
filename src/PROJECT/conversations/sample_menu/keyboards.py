from PROJECT.conversations.profile_intake import service as profile_service
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
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_WEATHER_MENU
from PROJECT.i18n.catalogs import ko


def main_menu_keyboard() -> list[list[str]]:
    return [
        [ko.BUTTON_TODAY_DATE, ko.BUTTON_TODAY_WEATHER],
        [ko.BUTTON_PROFILE, ko.BUTTON_HELP],
        [ko.BUTTON_RESTART],
        [ko.BUTTON_CANCEL],
    ]


def weather_menu_keyboard() -> list[list[str]]:
    return [
        list(ko.CITY_LABELS),
        [ko.BUTTON_BACK, ko.BUTTON_RESTART],
        [ko.BUTTON_HELP, ko.BUTTON_CANCEL],
    ]


def cancelled_keyboard() -> list[list[str]]:
    return [[ko.BUTTON_RESTART, ko.BUTTON_HELP]]


def keyboard_layout_for_state(state: str, draft: dict | None = None) -> list[list[str]]:
    if state == STATE_WEATHER_MENU:
        return weather_menu_keyboard()
    if state in {
        STATE_PROFILE_NAME,
        STATE_PROFILE_RESIDENCE,
        STATE_PROFILE_CITY,
        STATE_PROFILE_DISTRICT,
        STATE_PROFILE_BIRTH_YEAR,
        STATE_PROFILE_BIRTH_MONTH,
        STATE_PROFILE_BIRTH_DAY,
        STATE_PROFILE_CONFIRM,
    }:
        return profile_service.keyboard_for_state(state, profile_service.draft_from_dict(draft))
    if state == STATE_CANCELLED:
        return cancelled_keyboard()
    return main_menu_keyboard()
