from calendar import monthrange

from PROJECT.i18n.catalogs import ko

YEARS_PER_PAGE = 12


def profile_input_keyboard() -> list[list[str]]:
    return [
        [ko.BUTTON_BACK, ko.BUTTON_CANCEL],
        [ko.BUTTON_RESTART],
    ]


def profile_confirm_keyboard() -> list[list[str]]:
    return [
        [ko.BUTTON_CONFIRM, ko.BUTTON_EDIT],
        [ko.BUTTON_BACK, ko.BUTTON_CANCEL],
        [ko.BUTTON_RESTART],
    ]


def profile_birth_year_keyboard(page_start: int) -> list[list[str]]:
    years = [f"{page_start - offset}년" for offset in range(YEARS_PER_PAGE)]
    rows = [years[index:index + 3] for index in range(0, len(years), 3)]
    rows.append([ko.BUTTON_PREV_YEARS, ko.BUTTON_NEXT_YEARS])
    rows.append([ko.BUTTON_BACK, ko.BUTTON_CANCEL])
    return rows


def profile_birth_month_keyboard() -> list[list[str]]:
    months = [f"{month}월" for month in range(1, 13)]
    rows = [months[index:index + 3] for index in range(0, len(months), 3)]
    rows.append([ko.BUTTON_BACK, ko.BUTTON_CANCEL])
    return rows


def profile_birth_day_keyboard(year: int, month: int) -> list[list[str]]:
    max_day = monthrange(year, month)[1]
    days = [f"{day}일" for day in range(1, max_day + 1)]
    rows = [days[index:index + 7] for index in range(0, len(days), 7)]
    rows.append([ko.BUTTON_BACK, ko.BUTTON_CANCEL])
    return rows
