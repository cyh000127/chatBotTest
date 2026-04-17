from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from PROJECT.channels.telegram.handlers.commands import cancel_command, help_command, language_command, menu_command, profile_command, start_command
from PROJECT.channels.telegram.handlers.messages import button_callback, text_message, unknown_command
from PROJECT.settings import Settings


def create_application(settings: Settings):
    application = (
        __import__("telegram.ext", fromlist=["Application"])
        .Application.builder()
        .token(settings.bot_token)
        .build()
    )
    application.bot_data["settings"] = settings
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    return application
