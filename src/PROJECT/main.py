from PROJECT.telemetry.event_logger import configure_logging, log_event
from PROJECT.telemetry.events import BOT_STARTED
from PROJECT.channels.telegram.app import create_application
from PROJECT.settings import load_settings


def main() -> None:
    configure_logging()
    settings = load_settings()
    application = create_application(settings)
    log_event(
        BOT_STARTED,
        local_ai_gate=settings.local_ai_gate.value,
        llm_runtime_mode=settings.llm_runtime_mode,
        manual_review_fallback_active=settings.manual_review_fallback_active,
        llm_recovery_enabled=settings.llm_recovery_runtime_enabled,
        llm_edit_intent_enabled=settings.llm_edit_intent_runtime_enabled,
    )
    application.run_polling()


if __name__ == "__main__":
    main()
