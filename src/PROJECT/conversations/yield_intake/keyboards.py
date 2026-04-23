def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def yield_ready_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_YES, "yield:ready:yes"),
            _button(catalog.BUTTON_NO, "yield:ready:no"),
        ],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def yield_input_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def yield_confirm_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_CONFIRM, "intent:confirm")],
        [_button(catalog.BUTTON_EDIT, "intent:edit")],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def yield_edit_select_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_EDIT_START, "yield:edit:start")],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]
