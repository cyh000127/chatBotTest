from calendar import monthrange

YEARS_PER_PAGE = 12


def profile_input_keyboard(catalog) -> list[list[str]]:
    return [
        [catalog.BUTTON_BACK, catalog.BUTTON_CANCEL],
        [catalog.BUTTON_RESTART],
    ]


def profile_confirm_keyboard(catalog) -> list[list[str]]:
    return [
        [catalog.BUTTON_CONFIRM, catalog.BUTTON_EDIT],
        [catalog.BUTTON_BACK, catalog.BUTTON_CANCEL],
        [catalog.BUTTON_RESTART],
    ]


def profile_birth_year_keyboard(page_start: int, catalog) -> list[list[str]]:
    years = [str(page_start - offset) for offset in range(YEARS_PER_PAGE)]
    rows = [years[index:index + 3] for index in range(0, len(years), 3)]
    rows.append([catalog.BUTTON_PREV_YEARS, catalog.BUTTON_NEXT_YEARS])
    rows.append([catalog.BUTTON_BACK, catalog.BUTTON_CANCEL])
    return rows


def profile_birth_month_keyboard(catalog) -> list[list[str]]:
    months = [str(month) for month in range(1, 13)]
    rows = [months[index:index + 3] for index in range(0, len(months), 3)]
    rows.append([catalog.BUTTON_BACK, catalog.BUTTON_CANCEL])
    return rows


def profile_birth_day_keyboard(year: int, month: int, catalog) -> list[list[str]]:
    max_day = monthrange(year, month)[1]
    days = [str(day) for day in range(1, max_day + 1)]
    rows = [days[index:index + 7] for index in range(0, len(days), 7)]
    rows.append([catalog.BUTTON_BACK, catalog.BUTTON_CANCEL])
    return rows
