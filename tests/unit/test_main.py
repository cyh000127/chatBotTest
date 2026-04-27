import asyncio
from types import SimpleNamespace

from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime
from PROJECT.channels.telegram import app as telegram_app
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.channels.telegram.app import create_application, start_admin_background_tasks
from PROJECT.policy import LocalAiGate
from PROJECT import main as project_main
from PROJECT.settings import AdminApiSettings, GeminiSettings, Settings, SqliteSettings
from PROJECT.storage.sqlite import bootstrap_sqlite_runtime


def test_create_application_registers_settings():
    application = create_application(Settings(bot_token="test-token"))
    assert application.bot_data["settings"].bot_token == "test-token"
    assert application.bot_data["llm_runtime_mode"] == "rules_only_disabled"
    assert application.bot_data["gemini_recovery_classifier"] is None
    assert application.bot_data["gemini_edit_intent_resolver"] is None
    assert application.bot_data["admin_runtime"] is admin_runtime


def test_create_application_registers_sqlite_repositories_when_runtime_is_available(tmp_path):
    runtime = bootstrap_sqlite_runtime(
        SqliteSettings(
            database_path=str(tmp_path / "runtime.sqlite3"),
            migrations_enabled=True,
        )
    )
    assert runtime is not None

    try:
        application = create_application(Settings(bot_token="test-token"), sqlite_runtime=runtime)

        assert "invitation_repository" in application.bot_data
        assert "onboarding_repository" in application.bot_data
        assert "season_activity_repository" in application.bot_data
        assert "season_activity_service" in application.bot_data
        assert isinstance(application.bot_data["admin_runtime"], SqliteAdminRuntime)
    finally:
        runtime.close()


def test_start_admin_background_tasks_uses_registered_admin_runtime(monkeypatch):
    captured: dict[str, object] = {}
    runtime = InMemoryAdminRuntime()
    settings = Settings(
        bot_token="test-token",
        admin_api=AdminApiSettings(
            enabled=True,
            outbox_poll_interval_seconds=0.25,
        ),
    )

    def fake_delivery_loop(bot, *, interval_seconds, runtime):
        captured["bot"] = bot
        captured["interval_seconds"] = interval_seconds
        captured["runtime"] = runtime

        async def noop():
            return None

        return noop()

    def fake_create_task(coro, *, name):
        captured["task_name"] = name
        coro.close()
        return "task"

    monkeypatch.setattr(telegram_app, "run_outbox_delivery_loop", fake_delivery_loop)
    application = SimpleNamespace(
        bot="bot",
        bot_data={
            "settings": settings,
            "admin_runtime": runtime,
        },
        create_task=fake_create_task,
    )

    asyncio.run(start_admin_background_tasks(application))

    assert captured == {
        "bot": "bot",
        "interval_seconds": 0.25,
        "runtime": runtime,
        "task_name": "admin_outbox_delivery_loop",
    }
    assert application.bot_data["admin_outbox_delivery_task"] == "task"


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


def test_create_application_registers_yield_command():
    application = create_application(Settings(bot_token="test-token"))
    handlers = application.handlers[0]
    command_handlers = [handler for handler in handlers if hasattr(handler, "commands")]
    registered = {command for handler in command_handlers for command in handler.commands}

    assert "yield" in registered


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
        "admin_api_enabled": False,
        "sqlite_enabled": False,
        "sqlite_migrations_enabled": False,
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
    monkeypatch.setattr(project_main, "create_application", lambda loaded_settings, **kwargs: application)
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
                "admin_api_enabled": False,
                "sqlite_enabled": False,
                "sqlite_migrations_enabled": False,
            },
        )
    ]


def test_main_starts_admin_api_server_when_enabled(monkeypatch):
    started: list[tuple[Settings, object | None]] = []
    application = SimpleNamespace(run_polling=lambda: None)
    settings = Settings(
        bot_token="test-token",
        admin_api=AdminApiSettings(enabled=True, host="127.0.0.1", port=8000),
    )

    monkeypatch.setattr(project_main, "configure_logging", lambda: None)
    monkeypatch.setattr(project_main, "load_settings", lambda: settings)
    monkeypatch.setattr(project_main, "create_application", lambda loaded_settings, **kwargs: application)
    monkeypatch.setattr(
        project_main,
        "start_admin_api_server",
        lambda loaded_settings, *, sqlite_runtime=None: started.append((loaded_settings, sqlite_runtime)),
    )
    monkeypatch.setattr(project_main, "log_event", lambda event, **fields: None)

    project_main.main()

    assert started == [(settings, None)]


def test_main_passes_sqlite_runtime_to_admin_api_server(monkeypatch, tmp_path):
    started = []
    application = SimpleNamespace(run_polling=lambda: None)
    settings = Settings(
        bot_token="test-token",
        admin_api=AdminApiSettings(enabled=True, host="127.0.0.1", port=8000),
        sqlite=SqliteSettings(database_path=str(tmp_path / "runtime.sqlite3")),
    )
    sqlite_runtime = SimpleNamespace(close=lambda: None)

    monkeypatch.setattr(project_main, "configure_logging", lambda: None)
    monkeypatch.setattr(project_main, "load_settings", lambda: settings)
    monkeypatch.setattr(project_main, "create_application", lambda loaded_settings, **kwargs: application)
    monkeypatch.setattr(project_main, "bootstrap_sqlite_runtime", lambda sqlite_settings: sqlite_runtime)
    monkeypatch.setattr(
        project_main,
        "start_admin_api_server",
        lambda loaded_settings, *, sqlite_runtime=None: started.append((loaded_settings, sqlite_runtime)),
    )
    monkeypatch.setattr(project_main, "log_event", lambda event, **fields: None)

    project_main.main()

    assert started == [(settings, sqlite_runtime)]


def test_main_bootstraps_and_closes_sqlite_runtime_when_enabled(monkeypatch, tmp_path):
    closed = []
    application = SimpleNamespace(run_polling=lambda: None)
    settings = Settings(
        bot_token="test-token",
        sqlite=SqliteSettings(database_path=str(tmp_path / "runtime.sqlite3")),
    )
    runtime = SimpleNamespace(close=lambda: closed.append(True))

    monkeypatch.setattr(project_main, "configure_logging", lambda: None)
    monkeypatch.setattr(project_main, "load_settings", lambda: settings)
    monkeypatch.setattr(project_main, "create_application", lambda loaded_settings, **kwargs: application)
    monkeypatch.setattr(project_main, "bootstrap_sqlite_runtime", lambda sqlite_settings: runtime)
    monkeypatch.setattr(project_main, "log_event", lambda event, **fields: None)

    project_main.main()

    assert closed == [True]
