from calendar import monthrange

YEARS_PER_PAGE = 12


def _button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "data": data}


def profile_input_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def profile_confirm_keyboard(catalog) -> list[list[dict[str, str]]]:
    return [
        [
            _button(catalog.BUTTON_CONFIRM, "intent:confirm"),
            _button(catalog.BUTTON_EDIT, "intent:edit"),
        ],
        [
            _button(catalog.BUTTON_BACK, "intent:back"),
            _button(catalog.BUTTON_CANCEL, "intent:cancel"),
        ],
        [_button(catalog.BUTTON_RESTART, "intent:restart")],
    ]


def profile_birth_year_keyboard(page_start: int, catalog) -> list[list[dict[str, str]]]:
    years = [str(page_start - offset) for offset in range(YEARS_PER_PAGE)]
    rows = [
        [_button(year, f"profile:year:{year}") for year in years[index:index + 3]]
        for index in range(0, len(years), 3)
    ]
    rows.append([
        _button(catalog.BUTTON_PREV_YEARS, "profile:year_nav:prev"),
        _button(catalog.BUTTON_NEXT_YEARS, "profile:year_nav:next"),
    ])
    rows.append([
        _button(catalog.BUTTON_BACK, "intent:back"),
        _button(catalog.BUTTON_CANCEL, "intent:cancel"),
    ])
    return rows


def profile_birth_month_keyboard(catalog) -> list[list[dict[str, str]]]:
    months = [str(month) for month in range(1, 13)]
    rows = [
        [_button(month, f"profile:month:{month}") for month in months[index:index + 3]]
        for index in range(0, len(months), 3)
    ]
    rows.append([
        _button(catalog.BUTTON_BACK, "intent:back"),
        _button(catalog.BUTTON_CANCEL, "intent:cancel"),
    ])
    return rows


def profile_birth_day_keyboard(year: int, month: int, catalog) -> list[list[dict[str, str]]]:
    max_day = monthrange(year, month)[1]
    days = [str(day) for day in range(1, max_day + 1)]
    rows = [
        [_button(day, f"profile:day:{day}") for day in days[index:index + 7]]
        for index in range(0, len(days), 7)
    ]
    rows.append([
        _button(catalog.BUTTON_BACK, "intent:back"),
        _button(catalog.BUTTON_CANCEL, "intent:cancel"),
    ])
    return rows
