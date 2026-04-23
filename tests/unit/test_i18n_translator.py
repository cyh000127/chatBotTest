from PROJECT.dispatch.session_dispatcher import current_locale, set_locale
from PROJECT.i18n.translator import get_catalog, language_keyboard, resolve_language_choice


def test_default_locale_catalog_is_korean():
    user_data = {}
    assert current_locale(user_data) == "ko"
    assert get_catalog(current_locale(user_data)).LANGUAGE_NAME == "한국어"


def test_set_locale_changes_catalog():
    user_data = {}
    set_locale(user_data, "en")
    assert current_locale(user_data) == "en"
    assert get_catalog(current_locale(user_data)).LANGUAGE_NAME == "English"


def test_bengali_locale_catalog_is_available():
    user_data = {}
    set_locale(user_data, "bn")
    assert current_locale(user_data) == "bn"
    assert get_catalog(current_locale(user_data)).LANGUAGE_NAME == "বাংলা"


def test_resolve_language_choice():
    assert resolve_language_choice("English") == "en"
    assert resolve_language_choice("한국어") == "ko"
    assert resolve_language_choice("ខ្មែរ") == "km"
    assert resolve_language_choice("বাংলা") == "bn"


def test_language_keyboard_includes_bengali():
    layout = language_keyboard()

    assert {"text": "বাংলা", "data": "language:bn"} in layout[1]
