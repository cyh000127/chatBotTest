from PROJECT.conversations.fertilizer_intake import keyboards as fertilizer_keyboards
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)
from PROJECT.conversations.profile_intake import keyboards as profile_keyboards
from PROJECT.conversations.profile_intake import service as profile_service
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
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_LANGUAGE_SELECT, STATE_WEATHER_MENU
from PROJECT.i18n.translator import language_keyboard


def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def main_menu_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_TODAY_DATE, "intent:show_today_date"),
            _button(catalog.BUTTON_TODAY_WEATHER, "intent:open_weather_menu"),
        ],
        [
            _button(catalog.BUTTON_PROFILE, "intent:profile"),
            _button(catalog.BUTTON_FERTILIZER, "intent:fertilizer.input.start"),
        ],
        [_button(catalog.BUTTON_HELP, "intent:help")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
        [_button(catalog.BUTTON_CANCEL, "intent:cancel")],
    ]


def weather_menu_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(label, f"city:{city_key}") for label, city_key in catalog.CITY_BUTTON_TO_KEY.items()],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_RESTART, "intent:restart"),
        ],
        [
            _button(catalog.BUTTON_HELP, "intent:help"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
    ]


def cancelled_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [[
        _button(catalog.BUTTON_RESTART, "intent:restart"),
        _button(catalog.BUTTON_HELP, "intent:help"),
    ]]


def repair_confirmation_keyboard(domain: str, scope: str, target_state: str, catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_EDIT_START, f"repair:confirm:{domain}:{scope}:{target_state}")],
        [_button(catalog.BUTTON_KEEP_CURRENT, "repair:cancel")],
    ]


def fallback_keyboard_layout_for_state(state: str, catalog, draft: dict | None = None) -> list[list[dict[str, str]]]:
    if state == STATE_WEATHER_MENU:
        return weather_menu_keyboard(catalog)
    if state in {
        STATE_FERTILIZER_USED,
        STATE_FERTILIZER_KIND,
        STATE_FERTILIZER_PRODUCT,
        STATE_FERTILIZER_AMOUNT,
        STATE_FERTILIZER_DATE,
        STATE_FERTILIZER_CONFIRM,
    }:
        return fertilizer_keyboards.fertilizer_edit_select_keyboard(catalog)
    if state in {
        STATE_PROFILE_NAME,
        STATE_PROFILE_RESIDENCE,
        STATE_PROFILE_CITY,
        STATE_PROFILE_DISTRICT,
        STATE_PROFILE_BIRTH_YEAR,
        STATE_PROFILE_BIRTH_MONTH,
        STATE_PROFILE_BIRTH_DAY,
        STATE_PROFILE_CONFIRM,
        STATE_PROFILE_EDIT_SELECT,
    }:
        return profile_keyboards.profile_edit_select_keyboard(catalog)
    if state == STATE_CANCELLED:
        return cancelled_keyboard(catalog)
    return main_menu_keyboard(catalog)


def keyboard_layout_for_state(state: str, catalog, draft: dict | None = None) -> list[list[dict[str, str]]]:
    if state == STATE_WEATHER_MENU:
        return weather_menu_keyboard(catalog)
    if state in {
        STATE_FERTILIZER_USED,
        STATE_FERTILIZER_KIND,
        STATE_FERTILIZER_PRODUCT,
        STATE_FERTILIZER_AMOUNT,
        STATE_FERTILIZER_DATE,
        STATE_FERTILIZER_CONFIRM,
    }:
        return fertilizer_service.keyboard_for_state(state, catalog)
    if state in {
        STATE_PROFILE_NAME,
        STATE_PROFILE_RESIDENCE,
        STATE_PROFILE_CITY,
        STATE_PROFILE_DISTRICT,
        STATE_PROFILE_BIRTH_YEAR,
        STATE_PROFILE_BIRTH_MONTH,
        STATE_PROFILE_BIRTH_DAY,
        STATE_PROFILE_CONFIRM,
        STATE_PROFILE_EDIT_SELECT,
    }:
        return profile_service.keyboard_for_state(state, profile_service.draft_from_dict(draft), catalog)
    if state == STATE_LANGUAGE_SELECT:
        return language_keyboard()
    if state == STATE_CANCELLED:
        return cancelled_keyboard(catalog)
    return main_menu_keyboard(catalog)
