from PROJECT.canonical_intents import registry
from PROJECT.i18n.translator import all_button_intents, all_city_labels
from PROJECT.rule_engine import classify_global_intent_text

COMMAND_TO_INTENT = {
    "start": registry.INTENT_START,
    "help": registry.INTENT_HELP,
    "menu": registry.INTENT_MENU,
    "profile": registry.INTENT_PROFILE,
    "cancel": registry.INTENT_CANCEL,
}

BUTTON_TO_INTENT = {
    **all_button_intents(),
}

CITY_LABELS = all_city_labels()


def command_to_intent(command: str) -> str:
    normalized = command.lstrip("/").split("@", 1)[0].lower()
    return COMMAND_TO_INTENT.get(normalized, registry.INTENT_UNKNOWN_COMMAND)


def text_to_intent(text: str) -> tuple[str, dict]:
    decision = classify_global_intent_text(text, locale="ko")
    if decision is not None and decision.canonical_intent is not None:
        return decision.canonical_intent, decision.payload

    normalized = text.strip()
    if normalized in BUTTON_TO_INTENT:
        return BUTTON_TO_INTENT[normalized], {}
    if normalized in CITY_LABELS:
        return registry.INTENT_SELECT_CITY, {"city": CITY_LABELS[normalized]}
    return registry.INTENT_UNKNOWN_TEXT, {}
