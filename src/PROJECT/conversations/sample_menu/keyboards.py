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
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_LANGUAGE_SELECT
from PROJECT.conversations.onboarding import service as onboarding_service
from PROJECT.conversations.onboarding.states import ONBOARDING_STATES
from PROJECT.conversations.yield_intake import service as yield_service
from PROJECT.conversations.yield_intake.states import (
    STATE_YIELD_AMOUNT,
    STATE_YIELD_CONFIRM,
    STATE_YIELD_DATE,
    STATE_YIELD_EDIT_SELECT,
    STATE_YIELD_FIELD,
    STATE_YIELD_READY,
)
from PROJECT.i18n.translator import language_keyboard


def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def main_menu_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_FERTILIZER, "intent:agri.input.start"),
            _button(catalog.BUTTON_YIELD, "intent:yield.input.start"),
        ],
        [
            _button(catalog.BUTTON_MYFIELDS, "intent:field.list"),
            _button(catalog.BUTTON_INPUT_RESOLVE, "intent:input.resolve.start"),
        ],
        [
            _button(catalog.BUTTON_SUPPORT, "intent:support.escalate"),
            _button(catalog.BUTTON_HELP, "intent:help"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
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
        [_button(catalog.BUTTON_BACK, "intent:back")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def fallback_keyboard_layout_for_state(
    state: str,
    catalog,
    draft: dict | None = None,
    recovery_context: dict | None = None,
) -> list[list[dict[str, str]]]:
    if state in ONBOARDING_STATES:
        return onboarding_service.keyboard_for_state(state, catalog) or main_menu_keyboard(catalog)
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
    if state in {STATE_YIELD_READY, STATE_YIELD_FIELD, STATE_YIELD_AMOUNT, STATE_YIELD_DATE, STATE_YIELD_CONFIRM, STATE_YIELD_EDIT_SELECT}:
        return yield_service.keyboard_for_state(state, catalog)
    if state == STATE_CANCELLED:
        return cancelled_keyboard(catalog)
    return main_menu_keyboard(catalog)


def keyboard_layout_for_state(state: str, catalog, draft: dict | None = None) -> list[list[dict[str, str]]]:
    if state in ONBOARDING_STATES:
        return onboarding_service.keyboard_for_state(state, catalog) or main_menu_keyboard(catalog)
    if state in {
        STATE_FERTILIZER_USED,
        STATE_FERTILIZER_KIND,
        STATE_FERTILIZER_PRODUCT,
        STATE_FERTILIZER_AMOUNT,
        STATE_FERTILIZER_DATE,
        STATE_FERTILIZER_CONFIRM,
    }:
        return fertilizer_service.keyboard_for_state(state, catalog)
    if state in {STATE_YIELD_READY, STATE_YIELD_FIELD, STATE_YIELD_AMOUNT, STATE_YIELD_DATE, STATE_YIELD_CONFIRM, STATE_YIELD_EDIT_SELECT}:
        return yield_service.keyboard_for_state(state, catalog)
    if state == STATE_LANGUAGE_SELECT:
        return language_keyboard()
    if state == STATE_CANCELLED:
        return cancelled_keyboard(catalog)
    return main_menu_keyboard(catalog)
