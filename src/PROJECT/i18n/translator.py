from PROJECT.i18n.catalogs import en, km, ko

DEFAULT_LOCALE = "ko"

CATALOGS = {
    "ko": ko,
    "en": en,
    "km": km,
}

LANGUAGE_LABELS = {
    "ko": "한국어",
    "en": "English",
    "km": "ខ្មែរ",
}


def get_catalog(locale: str | None):
    return CATALOGS.get(locale or DEFAULT_LOCALE, ko)


def language_keyboard() -> list[list[dict[str, str]]]:
    return [[
        {"text": LANGUAGE_LABELS["ko"], "data": "language:ko"},
        {"text": LANGUAGE_LABELS["en"], "data": "language:en"},
        {"text": LANGUAGE_LABELS["km"], "data": "language:km"},
    ]]


def resolve_language_choice(text: str) -> str | None:
    normalized = text.strip()
    for locale, label in LANGUAGE_LABELS.items():
        if normalized == label or normalized.lower() == locale:
            return locale
    return None
def all_button_intents() -> dict[str, str]:
    from PROJECT.canonical_intents import registry

    mapping = {}
    for catalog in CATALOGS.values():
        mapping.update(
            {
                catalog.BUTTON_PROFILE: registry.INTENT_PROFILE,
                catalog.BUTTON_FERTILIZER: registry.INTENT_AGRI_INPUT_START,
                catalog.BUTTON_YIELD: registry.INTENT_YIELD_INPUT_START,
                catalog.BUTTON_MYFIELDS: registry.INTENT_FIELD_LIST,
                catalog.BUTTON_INPUT_RESOLVE: registry.INTENT_INPUT_RESOLVE_START,
                catalog.BUTTON_SUPPORT: registry.INTENT_SUPPORT_ESCALATE,
                catalog.BUTTON_HELP: registry.INTENT_HELP,
                catalog.BUTTON_BACK: registry.INTENT_BACK,
                catalog.BUTTON_CANCEL: registry.INTENT_CANCEL,
                catalog.BUTTON_RESTART: registry.INTENT_RESTART,
                catalog.BUTTON_CONFIRM: registry.INTENT_CONFIRM,
                catalog.BUTTON_EDIT: registry.INTENT_EDIT,
            }
        )
    return mapping
