from PROJECT.canonical_intents import registry
from PROJECT.i18n.catalogs import ko

COMMAND_TO_INTENT = {
    "start": registry.INTENT_START,
    "help": registry.INTENT_HELP,
    "menu": registry.INTENT_MENU,
    "profile": registry.INTENT_PROFILE,
    "cancel": registry.INTENT_CANCEL,
}

BUTTON_TO_INTENT = {
    ko.BUTTON_TODAY_DATE: registry.INTENT_SHOW_TODAY_DATE,
    ko.BUTTON_TODAY_WEATHER: registry.INTENT_OPEN_WEATHER_MENU,
    ko.BUTTON_PROFILE: registry.INTENT_PROFILE,
    ko.BUTTON_HELP: registry.INTENT_HELP,
    ko.BUTTON_BACK: registry.INTENT_BACK,
    ko.BUTTON_CANCEL: registry.INTENT_CANCEL,
    ko.BUTTON_RESTART: registry.INTENT_RESTART,
    ko.BUTTON_CONFIRM: registry.INTENT_CONFIRM,
    ko.BUTTON_EDIT: registry.INTENT_EDIT,
}


def command_to_intent(command: str) -> str:
    normalized = command.lstrip("/").split("@", 1)[0].lower()
    return COMMAND_TO_INTENT.get(normalized, registry.INTENT_UNKNOWN_COMMAND)


def text_to_intent(text: str) -> tuple[str, dict]:
    normalized = text.strip()
    if normalized in BUTTON_TO_INTENT:
        return BUTTON_TO_INTENT[normalized], {}
    if normalized in ko.CITY_LABELS:
        return registry.INTENT_SELECT_CITY, {"city": normalized}
    return registry.INTENT_UNKNOWN_TEXT, {}
