from PROJECT.settings import GeminiSettings, Settings


def test_settings_defaults_include_gemini_configuration():
    settings = Settings(bot_token="test-token")

    assert settings.gemini is None


def test_settings_accept_explicit_gemini_configuration():
    settings = Settings(
        bot_token="test-token",
        gemini=GeminiSettings(
            api_key="test-key",
            model="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta",
            timeout_seconds=15.0,
        ),
    )

    assert settings.gemini is not None
    assert settings.gemini.model == "gemini-2.5-flash"
