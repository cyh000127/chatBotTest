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
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_LANGUAGE_SELECT
from PROJECT.i18n.translator import language_keyboard


def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def main_menu_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_PROFILE, "intent:profile"),
            _button(catalog.BUTTON_FERTILIZER, "intent:fertilizer.input.start"),
        ],
        [
            _button(catalog.BUTTON_YIELD, "intent:yield.input.start"),
            _button(catalog.BUTTON_MYFIELDS, "intent:myfields.entry"),
        ],
        [
            _button(catalog.BUTTON_INPUT_RESOLVE, "intent:input.resolve.start"),
            _button(catalog.BUTTON_SUPPORT, "intent:support.escalate"),
        ],
        [_button(catalog.BUTTON_HELP, "intent:help")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
        [_button(catalog.BUTTON_CANCEL, "intent:cancel")],
    ]


def cancelled_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [[
        _button(catalog.BUTTON_RESTART, "intent:restart"),
        _button(catalog.BUTTON_HELP, "intent:help"),
    ]]


def repair_confirmation_keyboard(
    domain: str,
    scope: str,
    target_state: str,
    catalog,
    *,
    has_candidate: bool = False,
) -> list[list[dict[str, str]]]:
    if has_candidate:
        return [
            [_button(catalog.BUTTON_APPLY_SUGGESTED_VALUE, "repair:candidate:apply")],
            [_button(catalog.BUTTON_ENTER_VALUE_DIRECTLY, f"repair:confirm:{domain}:{scope}:{target_state}")],
            [_button(catalog.BUTTON_KEEP_CURRENT, "repair:cancel")],
        ]
    return [
        [_button(catalog.BUTTON_EDIT_START, f"repair:confirm:{domain}:{scope}:{target_state}")],
        [_button(catalog.BUTTON_KEEP_CURRENT, "repair:cancel")],
    ]


def profile_recovery_confirm_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_CONFIRM, "intent:confirm")],
        [
            _button(catalog.BUTTON_EDIT_NAME, "profile:edit:name"),
            _button(catalog.BUTTON_EDIT_RESIDENCE, "profile:edit:residence"),
        ],
        [
            _button(catalog.BUTTON_EDIT_CITY, "profile:edit:city"),
            _button(catalog.BUTTON_EDIT_DISTRICT, "profile:edit:district"),
        ],
        [_button(catalog.BUTTON_EDIT_BIRTH_DATE, "profile:edit:birth_date")],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def fertilizer_recovery_confirm_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_CONFIRM, "intent:confirm")],
        [
            _button(catalog.BUTTON_FERTILIZER_EDIT_USED, "fertilizer:edit:used"),
            _button(catalog.BUTTON_FERTILIZER_EDIT_KIND, "fertilizer:edit:kind"),
        ],
        [
            _button(catalog.BUTTON_FERTILIZER_EDIT_PRODUCT, "fertilizer:edit:product"),
            _button(catalog.BUTTON_FERTILIZER_EDIT_AMOUNT, "fertilizer:edit:amount"),
        ],
        [_button(catalog.BUTTON_FERTILIZER_EDIT_DATE, "fertilizer:edit:date")],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def fallback_keyboard_layout_for_state(
    state: str,
    catalog,
    draft: dict | None = None,
    recovery_context: dict | None = None,
) -> list[list[dict[str, str]]]:
    if state in {
        STATE_FERTILIZER_USED,
        STATE_FERTILIZER_KIND,
        STATE_FERTILIZER_PRODUCT,
        STATE_FERTILIZER_AMOUNT,
        STATE_FERTILIZER_DATE,
    }:
        return fertilizer_service.keyboard_for_state(state, catalog)
    if state == STATE_FERTILIZER_CONFIRM:
        return fertilizer_recovery_confirm_keyboard(catalog)
    if state in {
        STATE_PROFILE_NAME,
        STATE_PROFILE_RESIDENCE,
        STATE_PROFILE_CITY,
        STATE_PROFILE_DISTRICT,
        STATE_PROFILE_BIRTH_YEAR,
        STATE_PROFILE_BIRTH_MONTH,
        STATE_PROFILE_BIRTH_DAY,
    }:
        return profile_service.keyboard_for_state(state, profile_service.draft_from_dict(draft), catalog)
    if state == STATE_PROFILE_CONFIRM:
        return profile_recovery_confirm_keyboard(catalog)
    if state == STATE_PROFILE_EDIT_SELECT:
        return profile_keyboards.profile_edit_select_keyboard(catalog)
    if state == STATE_CANCELLED:
        return cancelled_keyboard(catalog)
    return main_menu_keyboard(catalog)


def keyboard_layout_for_state(state: str, catalog, draft: dict | None = None) -> list[list[dict[str, str]]]:
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
