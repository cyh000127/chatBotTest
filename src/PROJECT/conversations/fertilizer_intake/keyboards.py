def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def fertilizer_binary_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_YES, "fertilizer:used:yes"),
            _button(catalog.BUTTON_NO, "fertilizer:used:no"),
        ],
        [_button(catalog.BUTTON_BACK, "intent:back")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def fertilizer_kind_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_FERTILIZER_KIND_COMPOUND, "fertilizer:kind:compound"),
            _button(catalog.BUTTON_FERTILIZER_KIND_UREA, "fertilizer:kind:urea"),
        ],
        [
            _button(catalog.BUTTON_FERTILIZER_KIND_COMPOST, "fertilizer:kind:compost"),
            _button(catalog.BUTTON_FERTILIZER_KIND_LIQUID, "fertilizer:kind:liquid"),
        ],
        [_button(catalog.BUTTON_BACK, "intent:back")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def fertilizer_input_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_BACK, "intent:back")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def fertilizer_confirm_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_CONFIRM, "intent:confirm")],
        [_button(catalog.BUTTON_BACK, "intent:back")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def fertilizer_edit_select_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
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
