from types import SimpleNamespace

from PROJECT.channels.telegram.app import create_application
from PROJECT.policy import LocalAiGate
from PROJECT import main as project_main
from PROJECT.settings import GeminiSettings, Settings


def test_create_application_registers_settings():
    application = create_application(Settings(bot_token="test-token"))
    assert application.bot_data["settings"].bot_token == "test-token"
    assert application.bot_data["llm_runtime_mode"] == "rules_only_disabled"
    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is None


def test_create_application_registers_myfields_command():
    application = create_application(Settings(bot_token="test-token"))
    handlers = application.handlers[0]
    command_handlers = [handler for handler in handlers if hasattr(handler, "commands")]
    registered = {command for handler in command_handlers for command in handler.commands}

    assert "myfields" in registered


def test_create_application_registers_resolve_command():
    application = create_application(Settings(bot_token="test-token"))
    handlers = application.handlers[0]
    command_handlers = [handler for handler in handlers if hasattr(handler, "commands")]
    registered = {command for handler in command_handlers for command in handler.commands}

    assert "resolve" in registered


def test_create_application_registers_support_command():
    application = create_application(Settings(bot_token="test-token"))
    handlers = application.handlers[0]
    command_handlers = [handler for handler in handlers if hasattr(handler, "commands")]
    registered = {command for handler in command_handlers for command in handler.commands}

    assert "support" in registered


def test_create_application_keeps_edit_intent_resolver_disabled_without_policy_gate():
    application = create_application(
        Settings(
            bot_token="test-token",
            gemini=GeminiSettings(
                api_key="test-key",
                model="gemini-2.5-flash",
                api_base="https://generativelanguage.googleapis.com/v1beta",
                timeout_seconds=15.0,
            ),
            local_ai_gate=LocalAiGate.DISABLED,
        )
    )

    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is None


def test_create_application_keeps_rules_only_manual_review_mode_when_configured():
    application = create_application(
        Settings(
            bot_token="test-token",
            gemini=GeminiSettings(
                api_key="test-key",
                model="gemini-2.5-flash",
                api_base="https://generativelanguage.googleapis.com/v1beta",
                timeout_seconds=15.0,
            ),
            local_ai_gate=LocalAiGate.MANUAL_REVIEW_FALLBACK,
        )
    )

    assert application.bot_data["llm_runtime_mode"] == "rules_only_manual_review"
    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is None


def test_create_application_keeps_rules_only_mode_when_gate_is_set_but_model_is_missing():
    application = create_application(
        Settings(
            bot_token="test-token",
            local_ai_gate=LocalAiGate.RECOVERY_ASSIST_ONLY,
        )
    )

    assert application.bot_data["llm_runtime_mode"] == "rules_only_disabled"
    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is None


def test_create_application_registers_edit_intent_resolver_only_when_policy_gate_is_enabled():
    application = create_application(
        Settings(
            bot_token="test-token",
            gemini=GeminiSettings(
                api_key="test-key",
                model="gemini-2.5-flash",
                api_base="https://generativelanguage.googleapis.com/v1beta",
                timeout_seconds=15.0,
            ),
            local_ai_gate=LocalAiGate.REPAIR_ASSIST_ONLY,
        )
    )

    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is not None


def test_create_application_registers_recovery_resolver_only_when_recovery_mode_is_enabled():
    application = create_application(
        Settings(
            bot_token="test-token",
            gemini=GeminiSettings(
                api_key="test-key",
                model="gemini-2.5-flash",
                api_base="https://generativelanguage.googleapis.com/v1beta",
                timeout_seconds=15.0,
            ),
            local_ai_gate=LocalAiGate.RECOVERY_ASSIST_ONLY,
        )
    )

    assert application.bot_data["gemini_recovery_classifier"] is not None
    assert application.bot_data["gemini_edit_intent_resolver"] is None


def test_startup_log_fields_reflect_runtime_mode_from_actual_model_availability():
    settings = Settings(bot_token="test-token", local_ai_gate=LocalAiGate.RECOVERY_ASSIST_ONLY)

    assert project_main.startup_log_fields(settings) == {
        "local_ai_gate": "recovery_assist_only",
        "llm_runtime_mode": "rules_only_disabled",
        "manual_review_fallback_active": False,
        "llm_recovery_enabled": False,
        "llm_edit_intent_enabled": False,
    }


def test_main_logs_bot_started_with_runtime_snapshot(monkeypatch):
    captured_events: list[tuple[str, dict]] = []
    application = SimpleNamespace(run_polling=lambda: None)
    settings = Settings(
        bot_token="test-token",
        gemini=GeminiSettings(
            api_key="test-key",
            model="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta",
            timeout_seconds=15.0,
        ),
        local_ai_gate=LocalAiGate.REPAIR_ASSIST_ONLY,
    )

    monkeypatch.setattr(project_main, "configure_logging", lambda: None)
    monkeypatch.setattr(project_main, "load_settings", lambda: settings)
    monkeypatch.setattr(project_main, "create_application", lambda loaded_settings: application)
    monkeypatch.setattr(project_main, "log_event", lambda event, **fields: captured_events.append((event, fields)))

    project_main.main()

    assert captured_events == [
        (
            "bot_started",
            {
                "local_ai_gate": "repair_assist_only",
                "llm_runtime_mode": "llm_assisted",
                "manual_review_fallback_active": False,
                "llm_recovery_enabled": False,
                "llm_edit_intent_enabled": True,
            },
        )
    ]
