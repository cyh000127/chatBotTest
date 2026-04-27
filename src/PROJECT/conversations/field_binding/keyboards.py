from PROJECT.conversations.field_binding.states import (
    STATE_FIELD_BINDING_CANDIDATE_SELECT,
    STATE_FIELD_BINDING_CODE,
    STATE_FIELD_BINDING_CONFIRM,
    STATE_FIELD_BINDING_LOCATION,
    STATE_FIELD_BINDING_METHOD,
    STATE_MYFIELDS_SUMMARY,
)


def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def summary_keyboard(catalog, *, has_bindings: bool) -> list[list[dict[str, str]]]:
    primary_text = getattr(catalog, "BUTTON_FIELD_REGISTER", "농지 등록")
    refresh_text = getattr(catalog, "BUTTON_FIELD_REFRESH", "새로고침")
    rows = [
        [_button(primary_text, "fieldbind:start"), _button(refresh_text, "fieldbind:refresh")],
        [_button(catalog.BUTTON_SUPPORT, "intent:support.escalate"), _button(catalog.BUTTON_HELP, "intent:help")],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]
    if has_bindings:
        return rows
    return rows


def method_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(getattr(catalog, "BUTTON_FIELD_LOOKUP_LOCATION", "위치로 찾기"), "fieldbind:method:location"),
            _button(getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"), "fieldbind:method:code"),
        ],
        [_button(catalog.BUTTON_BACK, "intent:back"), _button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def location_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"), "fieldbind:method:code")],
        [_button(catalog.BUTTON_BACK, "intent:back"), _button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def code_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(getattr(catalog, "BUTTON_FIELD_LOOKUP_LOCATION", "위치로 찾기"), "fieldbind:method:location")],
        [_button(catalog.BUTTON_BACK, "intent:back"), _button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def candidate_keyboard(catalog, candidates: tuple[dict, ...]) -> list[list[dict[str, str]]]:
    rows = [
        [_button(candidate["display_name"], f"fieldbind:candidate:{candidate['field_id']}")]
        for candidate in candidates
    ]
    rows.append([_button(getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"), "fieldbind:method:code")])
    rows.append([_button(catalog.BUTTON_BACK, "intent:back"), _button(catalog.BUTTON_RESTART, "intent:restart")])
    return rows


def confirm_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [_button(catalog.BUTTON_CONFIRM, "fieldbind:confirm")],
        [
            _button(getattr(catalog, "BUTTON_FIELD_LOOKUP_LOCATION", "위치로 찾기"), "fieldbind:method:location"),
            _button(getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"), "fieldbind:method:code"),
        ],
        [_button(catalog.BUTTON_BACK, "intent:back"), _button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def keyboard_for_state(state: str, catalog, *, has_bindings: bool = False, candidates: tuple[dict, ...] = ()) -> list[list[dict[str, str]]]:
    if state == STATE_MYFIELDS_SUMMARY:
        return summary_keyboard(catalog, has_bindings=has_bindings)
    if state == STATE_FIELD_BINDING_METHOD:
        return method_keyboard(catalog)
    if state == STATE_FIELD_BINDING_LOCATION:
        return location_keyboard(catalog)
    if state == STATE_FIELD_BINDING_CODE:
        return code_keyboard(catalog)
    if state == STATE_FIELD_BINDING_CANDIDATE_SELECT:
        return candidate_keyboard(catalog, candidates)
    if state == STATE_FIELD_BINDING_CONFIRM:
        return confirm_keyboard(catalog)
    return summary_keyboard(catalog, has_bindings=has_bindings)
