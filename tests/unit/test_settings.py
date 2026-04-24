from PROJECT.policy import LocalAiGate
from PROJECT.settings import (
    DEFAULT_ADMIN_API_HOST,
    DEFAULT_ADMIN_API_PORT,
    DEFAULT_ADMIN_API_ACCESS_ROLE,
    DEFAULT_ADMIN_OUTBOX_POLL_INTERVAL_SECONDS,
    DEFAULT_SQLITE_BUSY_TIMEOUT_MS,
    GeminiSettings,
    Settings,
    SqliteSettings,
    load_settings,
    parse_admin_api_access_role,
    parse_bool_env,
    parse_int_env,
)


def test_settings_defaults_include_gemini_configuration():
    settings = Settings(bot_token="test-token")

    assert settings.gemini is None
    assert settings.admin_api.enabled is False
    assert settings.admin_api.host == DEFAULT_ADMIN_API_HOST
    assert settings.admin_api.port == DEFAULT_ADMIN_API_PORT
    assert settings.admin_api.outbox_poll_interval_seconds == DEFAULT_ADMIN_OUTBOX_POLL_INTERVAL_SECONDS
    assert settings.admin_api.access_token == ""
    assert settings.admin_api.access_role == DEFAULT_ADMIN_API_ACCESS_ROLE
    assert settings.admin_api.access_control_enabled is False
    assert settings.admin_api.write_access_enabled is True
    assert settings.sqlite == SqliteSettings()
    assert settings.sqlite.enabled is False
    assert settings.sqlite.busy_timeout_ms == DEFAULT_SQLITE_BUSY_TIMEOUT_MS
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


def test_parse_int_env_returns_default_for_missing_or_invalid_values(monkeypatch):
    monkeypatch.delenv("SQLITE_BUSY_TIMEOUT_MS", raising=False)
    assert parse_int_env("SQLITE_BUSY_TIMEOUT_MS", default=5000) == 5000

    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_MS", "invalid")
    assert parse_int_env("SQLITE_BUSY_TIMEOUT_MS", default=5000) == 5000

    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_MS", "-1")
    assert parse_int_env("SQLITE_BUSY_TIMEOUT_MS", default=5000) == 5000


def test_parse_int_env_accepts_non_negative_integer(monkeypatch):
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_MS", "2500")

    assert parse_int_env("SQLITE_BUSY_TIMEOUT_MS", default=5000) == 2500


def test_parse_admin_api_access_role_accepts_known_roles():
    assert parse_admin_api_access_role("viewer") == "viewer"
    assert parse_admin_api_access_role(" operator ") == "operator"
    assert parse_admin_api_access_role("unknown") == DEFAULT_ADMIN_API_ACCESS_ROLE


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


def test_load_settings_reads_admin_api_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("ADMIN_API_ENABLED", "true")
    monkeypatch.setenv("ADMIN_API_HOST", "0.0.0.0")
    monkeypatch.setenv("ADMIN_API_PORT", "9000")
    monkeypatch.setenv("ADMIN_OUTBOX_POLL_INTERVAL_SECONDS", "2.5")
    monkeypatch.setenv("ADMIN_API_ACCESS_TOKEN", "test-admin-token")
    monkeypatch.setenv("ADMIN_API_ACCESS_ROLE", "viewer")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    settings = load_settings()

    assert settings.admin_api.enabled is True
    assert settings.admin_api.host == "0.0.0.0"
    assert settings.admin_api.port == 9000
    assert settings.admin_api.outbox_poll_interval_seconds == 2.5
    assert settings.admin_api.access_token == "test-admin-token"
    assert settings.admin_api.access_role == "viewer"
    assert settings.admin_api.access_control_enabled is True
    assert settings.admin_api.write_access_enabled is False


def test_load_settings_reads_sqlite_env(monkeypatch, tmp_path):
    database_path = tmp_path / "runtime.sqlite3"
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("SQLITE_DATABASE_PATH", str(database_path))
    monkeypatch.setenv("SQLITE_MIGRATIONS_ENABLED", "true")
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_MS", "1234")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    settings = load_settings()

    assert settings.sqlite.enabled is True
    assert settings.sqlite.database_path == str(database_path)
    assert settings.sqlite.migrations_enabled is True
    assert settings.sqlite.busy_timeout_ms == 1234


def test_load_settings_rejects_relative_sqlite_path(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("SQLITE_DATABASE_PATH", "runtime.sqlite3")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    try:
        load_settings()
    except ValueError as exc:
        assert "SQLITE_DATABASE_PATH" in str(exc)
    else:
        raise AssertionError("relative SQLite path should be rejected")
