from PROJECT.settings import GeminiSettings, Settings, parse_bool_env


def test_settings_defaults_include_gemini_configuration():
    settings = Settings(bot_token="test-token")

    assert settings.gemini is None
    assert settings.enable_llm_edit_intent is False


def test_settings_accept_explicit_gemini_configuration():
    settings = Settings(
        bot_token="test-token",
        enable_llm_edit_intent=True,
        gemini=GeminiSettings(
            api_key="test-key",
            model="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta",
            timeout_seconds=15.0,
        ),
    )

    assert settings.gemini is not None
    assert settings.gemini.model == "gemini-2.5-flash"
    assert settings.enable_llm_edit_intent is True


def test_parse_bool_env_returns_false_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LLM_EDIT_INTENT", raising=False)

    assert parse_bool_env("ENABLE_LLM_EDIT_INTENT", default=False) is False


def test_parse_bool_env_accepts_true_values(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_EDIT_INTENT", "true")

    assert parse_bool_env("ENABLE_LLM_EDIT_INTENT", default=False) is True
