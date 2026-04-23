from PROJECT.admin_api.server import start_admin_api_server
from PROJECT.telemetry.event_logger import configure_logging, log_event
from PROJECT.telemetry.events import BOT_STARTED
from PROJECT.channels.telegram.app import create_application
from PROJECT.settings import Settings, load_settings


def startup_log_fields(settings: Settings) -> dict[str, object]:
    return {
        "local_ai_gate": settings.local_ai_gate.value,
        "llm_runtime_mode": settings.llm_runtime_mode,
        "manual_review_fallback_active": settings.manual_review_fallback_active,
        "llm_recovery_enabled": settings.llm_recovery_runtime_enabled,
        "llm_edit_intent_enabled": settings.llm_edit_intent_runtime_enabled,
        "admin_api_enabled": settings.admin_api.enabled,
    }


def main() -> None:
    configure_logging()
    settings = load_settings()
    application = create_application(settings)
    if settings.admin_api.enabled:
        start_admin_api_server(settings)
    log_event(BOT_STARTED, **startup_log_fields(settings))
    application.run_polling()


if __name__ == "__main__":
    main()
