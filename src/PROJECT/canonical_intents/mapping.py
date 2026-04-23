from PROJECT.canonical_intents import registry
from PROJECT.i18n.translator import all_button_intents
from PROJECT.rule_engine import classify_global_intent_text, classify_step_local_intent_text

COMMAND_TO_INTENT = {
    "start": registry.INTENT_START,
    "help": registry.INTENT_HELP,
    "menu": registry.INTENT_MENU,
    "profile": registry.INTENT_PROFILE,
    "myfields": registry.INTENT_FIELD_LIST,
    "fertilizer": registry.INTENT_AGRI_INPUT_START,
    "yield": registry.INTENT_YIELD_INPUT_START,
    "resolve": registry.INTENT_INPUT_RESOLVE_START,
    "support": registry.INTENT_SUPPORT_ESCALATE,
    "cancel": registry.INTENT_CANCEL,
}

BUTTON_TO_INTENT = {
    **all_button_intents(),
}


def command_to_intent(command: str) -> str:
    normalized = command.lstrip("/").split("@", 1)[0].lower()
    return COMMAND_TO_INTENT.get(normalized, registry.INTENT_UNKNOWN_COMMAND)


def text_to_intent(text: str, *, current_step: str | None = None, locale: str = "ko") -> tuple[str, dict]:
    decision = classify_step_local_intent_text(text, locale=locale, current_step=current_step)
    if decision is not None and decision.canonical_intent is not None:
        return decision.canonical_intent, decision.payload

    decision = classify_global_intent_text(text, locale=locale, current_step=current_step)
    if decision is not None and decision.canonical_intent is not None:
        return decision.canonical_intent, decision.payload

    normalized = text.strip()
    if normalized in BUTTON_TO_INTENT:
        return BUTTON_TO_INTENT[normalized], {}
    return registry.INTENT_UNKNOWN_TEXT, {}
