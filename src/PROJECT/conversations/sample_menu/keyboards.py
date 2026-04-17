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
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_LANGUAGE_SELECT, STATE_WEATHER_MENU
from PROJECT.i18n.translator import language_keyboard


def main_menu_keyboard(catalog) -> list[list[str]]:
    return [
        [catalog.BUTTON_TODAY_DATE, catalog.BUTTON_TODAY_WEATHER],
        [catalog.BUTTON_PROFILE, catalog.BUTTON_HELP],
        [catalog.BUTTON_RESTART],
        [catalog.BUTTON_CANCEL],
    ]


def weather_menu_keyboard(catalog) -> list[list[str]]:
    return [
        list(catalog.CITY_BUTTON_TO_KEY.keys()),
        [catalog.BUTTON_BACK, catalog.BUTTON_RESTART],
        [catalog.BUTTON_HELP, catalog.BUTTON_CANCEL],
    ]


def cancelled_keyboard(catalog) -> list[list[str]]:
    return [[catalog.BUTTON_RESTART, catalog.BUTTON_HELP]]


def keyboard_layout_for_state(state: str, catalog, draft: dict | None = None) -> list[list[str]]:
    if state == STATE_WEATHER_MENU:
        return weather_menu_keyboard(catalog)
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
        return profile_service.keyboard_for_state(state, profile_service.draft_from_dict(draft), catalog)
    if state == STATE_LANGUAGE_SELECT:
        return language_keyboard()
    if state == STATE_CANCELLED:
        return cancelled_keyboard(catalog)
    return main_menu_keyboard(catalog)
