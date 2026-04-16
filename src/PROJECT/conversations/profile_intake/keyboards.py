from PROJECT.i18n.catalogs import ko


def profile_input_keyboard() -> list[list[str]]:
    return [[ko.BUTTON_CANCEL, ko.BUTTON_RESTART]]


def profile_confirm_keyboard() -> list[list[str]]:
    return [
        [ko.BUTTON_CONFIRM, ko.BUTTON_EDIT],
        [ko.BUTTON_CANCEL, ko.BUTTON_RESTART],
    ]


def profile_followup_keyboard(options: list[str] | None = None) -> list[list[str]]:
    rows: list[list[str]] = []
    if options:
        rows.append(options)
    rows.append([ko.BUTTON_EDIT, ko.BUTTON_CANCEL])
    return rows
