from PROJECT.conversations.profile_intake.keyboards import profile_confirm_keyboard, profile_followup_keyboard, profile_input_keyboard
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_FOLLOWUP, STATE_PROFILE_INPUT
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


def keyboard_layout_for_state(state: str) -> list[list[str]]:
    if state == STATE_WEATHER_MENU:
        return weather_menu_keyboard()
    if state == STATE_PROFILE_INPUT:
        return profile_input_keyboard()
    if state == STATE_PROFILE_CONFIRM:
        return profile_confirm_keyboard()
    if state == STATE_PROFILE_FOLLOWUP:
        return profile_followup_keyboard()
    if state == STATE_CANCELLED:
        return cancelled_keyboard()
    return main_menu_keyboard()
