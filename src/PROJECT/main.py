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
        llm_recovery_enabled=settings.gemini is not None,
        llm_edit_intent_enabled=settings.enable_llm_edit_intent and settings.gemini is not None,
    )
    application.run_polling()


if __name__ == "__main__":
    main()
