def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def target_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_INPUT_RESOLVE_TARGET_FIELD_CODE, "inputresolve:target:field_code"),
            _button(catalog.BUTTON_INPUT_RESOLVE_TARGET_FIELD_NAME, "inputresolve:target:field_name"),
        ],
        [_button(catalog.BUTTON_CANCEL, "intent:cancel")],
    ]


def method_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_INPUT_RESOLVE_METHOD_TYPED_TEXT, "inputresolve:method:typed_text")],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
    ]


def raw_input_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
    ]


def candidate_keyboard(catalog, candidates: tuple[dict, ...]) -> list[list[dict[str, str]]]:
    rows: list[list[dict[str, str]]] = []
    for candidate in candidates:
        rows.append(
            [
                _button(
                    f"{candidate['rank']}. {candidate['label']}",
                    f"inputresolve:candidate:{candidate['candidate_id']}",
                )
            ]
        )
    rows.append([_button(catalog.BUTTON_INPUT_RESOLVE_RETRY, "inputresolve:retry")])
    rows.append([_button(catalog.BUTTON_INPUT_RESOLVE_RETRY_LATER, "inputresolve:retry_later")])
    rows.append([_button(catalog.BUTTON_INPUT_RESOLVE_MANUAL_REVIEW, "inputresolve:manual_review")])
    rows.append([_button(catalog.BUTTON_CANCEL, "intent:cancel")])
    return rows


def candidate_empty_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_INPUT_RESOLVE_RETRY, "inputresolve:retry")],
        [_button(catalog.BUTTON_INPUT_RESOLVE_RETRY_LATER, "inputresolve:retry_later")],
        [_button(catalog.BUTTON_INPUT_RESOLVE_MANUAL_REVIEW, "inputresolve:manual_review")],
        [_button(catalog.BUTTON_CANCEL, "intent:cancel")],
    ]


def decision_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_INPUT_RESOLVE_CONFIRM_CANDIDATE, "inputresolve:decision:resolved")],
        [_button(catalog.BUTTON_INPUT_RESOLVE_RETRY, "inputresolve:decision:retry")],
        [_button(catalog.BUTTON_INPUT_RESOLVE_RETRY_LATER, "inputresolve:decision:retry_later")],
        [_button(catalog.BUTTON_INPUT_RESOLVE_MANUAL_REVIEW, "inputresolve:decision:manual_review")],
        [_button(catalog.BUTTON_CANCEL, "intent:cancel")],
    ]
