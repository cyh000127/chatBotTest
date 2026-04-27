from PROJECT.conversations.evidence_submission.states import (
    STATE_EVIDENCE_VALIDATING,
    STATE_EVIDENCE_WAITING_DOCUMENT,
    STATE_EVIDENCE_WAITING_LOCATION,
)


def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def location_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_SUPPORT, "intent:support.escalate")],
        [
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
            _button(catalog.BUTTON_RESTART, "intent:restart"),
        ],
        [_button(catalog.BUTTON_HELP, "intent:help")],
    ]


def document_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_SUPPORT, "intent:support.escalate")],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def validating_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_SUPPORT, "intent:support.escalate")],
        [
            _button(catalog.BUTTON_HELP, "intent:help"),
            _button(catalog.BUTTON_RESTART, "intent:restart"),
        ],
    ]


def keyboard_for_state(state: str, catalog) -> list[list[dict[str, str]]]:
    if state == STATE_EVIDENCE_WAITING_LOCATION:
        return location_keyboard(catalog)
    if state == STATE_EVIDENCE_WAITING_DOCUMENT:
        return document_keyboard(catalog)
    if state == STATE_EVIDENCE_VALIDATING:
        return validating_keyboard(catalog)
    return location_keyboard(catalog)
