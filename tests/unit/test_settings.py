from PROJECT.policy import LocalAiGate
from PROJECT.settings import GeminiSettings, Settings, load_settings, parse_bool_env


def test_settings_defaults_include_gemini_configuration():
    settings = Settings(bot_token="test-token")

    assert settings.gemini is None
    assert settings.local_ai_gate == LocalAiGate.DISABLED
    assert settings.enable_llm_edit_intent is False
    assert settings.enable_llm_recovery is False
    assert settings.llm_edit_intent_runtime_enabled is False
    assert settings.llm_recovery_runtime_enabled is False
    assert settings.runtime_rules_only is True
    assert settings.llm_runtime_mode == "rules_only_disabled"


def test_settings_accept_explicit_gemini_configuration():
    settings = Settings(
        bot_token="test-token",
        local_ai_gate=LocalAiGate.REPAIR_ASSIST_ONLY,
        gemini=GeminiSettings(
            api_key="test-key",
            model="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta",
            timeout_seconds=15.0,
        ),
    )

    assert settings.gemini is not None
    assert settings.gemini.model == "gemini-2.5-flash"
    assert settings.local_ai_gate == LocalAiGate.REPAIR_ASSIST_ONLY
    assert settings.enable_llm_edit_intent is True
    assert settings.enable_llm_recovery is False
    assert settings.llm_edit_intent_runtime_enabled is True
    assert settings.llm_recovery_runtime_enabled is False
    assert settings.runtime_rules_only is False
    assert settings.llm_runtime_mode == "llm_assisted"


def test_settings_exposes_manual_review_fallback_mode():
    settings = Settings(bot_token="test-token", local_ai_gate=LocalAiGate.MANUAL_REVIEW_FALLBACK)

    assert settings.manual_review_fallback_active is True
    assert settings.runtime_rules_only is True
    assert settings.enable_llm_edit_intent is False
    assert settings.enable_llm_recovery is False
    assert settings.llm_runtime_mode == "rules_only_manual_review"


def test_settings_treats_gate_without_model_credentials_as_rules_only_runtime():
    settings = Settings(bot_token="test-token", local_ai_gate=LocalAiGate.RECOVERY_ASSIST_ONLY)

    assert settings.enable_llm_recovery is True
    assert settings.llm_recovery_runtime_enabled is False
    assert settings.runtime_rules_only is True
    assert settings.llm_runtime_mode == "rules_only_disabled"


def test_parse_bool_env_returns_false_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LLM_EDIT_INTENT", raising=False)

    assert parse_bool_env("ENABLE_LLM_EDIT_INTENT", default=False) is False


def test_parse_bool_env_accepts_true_values(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_EDIT_INTENT", "true")

    assert parse_bool_env("ENABLE_LLM_EDIT_INTENT", default=False) is True


def test_load_settings_reads_local_ai_gate_from_ai_mode_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("AI_MODE", "recovery_assist_only")
    monkeypatch.delenv("ENABLE_LLM_EDIT_INTENT", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    settings = load_settings()

    assert settings.local_ai_gate == LocalAiGate.RECOVERY_ASSIST_ONLY
    assert settings.enable_llm_recovery is True
    assert settings.enable_llm_edit_intent is False


def test_load_settings_uses_legacy_edit_intent_flag_when_local_ai_gate_is_missing(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.delenv("AI_MODE", raising=False)
    monkeypatch.setenv("ENABLE_LLM_EDIT_INTENT", "true")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    settings = load_settings()

    assert settings.local_ai_gate == LocalAiGate.REPAIR_ASSIST_ONLY
