from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from PROJECT.channels.telegram.handlers.commands import cancel_command, fertilizer_command, help_command, input_resolve_command, language_command, menu_command, myfields_command, profile_command, start_command, support_command, yield_command
from PROJECT.channels.telegram.handlers.messages import button_callback, text_message, unknown_command
from PROJECT.admin.delivery import run_outbox_delivery_loop
from PROJECT.llm import GeminiEditIntentResolver, GeminiRecoveryClassifier
from PROJECT.settings import Settings


async def start_admin_background_tasks(application) -> None:
    settings = application.bot_data["settings"]
    if not settings.admin_api.enabled:
        return
    application.bot_data["admin_outbox_delivery_task"] = application.create_task(
        run_outbox_delivery_loop(
            application.bot,
            interval_seconds=settings.admin_api.outbox_poll_interval_seconds,
        ),
        name="admin_outbox_delivery_loop",
    )


def create_application(settings: Settings):
    gemini_recovery_classifier = (
        GeminiRecoveryClassifier(settings.gemini)
        if settings.llm_recovery_runtime_enabled
        else None
    )
    gemini_edit_intent_resolver = (
        GeminiEditIntentResolver(settings.gemini)
        if settings.llm_edit_intent_runtime_enabled
        else None
    )
    builder = __import__("telegram.ext", fromlist=["Application"]).Application.builder().token(settings.bot_token)
    if settings.admin_api.enabled:
        builder = builder.post_init(start_admin_background_tasks)
    application = builder.build()
    application.bot_data["settings"] = settings
    application.bot_data["llm_runtime_mode"] = settings.llm_runtime_mode
    application.bot_data["gemini_recovery_classifier"] = gemini_recovery_classifier
    application.bot_data["gemini_edit_intent_resolver"] = gemini_edit_intent_resolver
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("myfields", myfields_command))
    application.add_handler(CommandHandler("fertilizer", fertilizer_command))
    application.add_handler(CommandHandler("yield", yield_command))
    application.add_handler(CommandHandler("resolve", input_resolve_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    return application
