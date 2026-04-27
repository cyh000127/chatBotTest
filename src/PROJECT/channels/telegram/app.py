from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from PROJECT.channels.telegram.handlers.commands import cancel_command, fertilizer_command, help_command, input_resolve_command, language_command, menu_command, myfields_command, start_command, support_command, yield_command
from PROJECT.channels.telegram.handlers.messages import button_callback, location_message, text_message, unknown_command
from PROJECT.admin.delivery import run_outbox_delivery_loop
from PROJECT.admin.follow_up import admin_runtime
from PROJECT.admin.sqlite_follow_up import SqliteAdminRuntime
from PROJECT.activity import SeasonActivityService
from PROJECT.evidence import EvidenceSubmissionService
from PROJECT.fields.binding import FieldBindingService
from PROJECT.llm import GeminiEditIntentResolver, GeminiRecoveryClassifier
from PROJECT.reminders import DEFAULT_REMINDER_POLL_INTERVAL_SECONDS, run_reminder_delivery_loop
from PROJECT.settings import Settings
from PROJECT.storage.activity import SqliteSeasonActivityRepository
from PROJECT.storage.evidence import SqliteEvidenceRepository
from PROJECT.storage.fields import SqliteFieldRegistryRepository
from PROJECT.storage.input_resolution import SqliteInputResolutionRepository
from PROJECT.storage.invitations import SqliteInvitationRepository
from PROJECT.storage.onboarding import SqliteOnboardingRepository
from PROJECT.storage.reminders import SqliteReminderRepository
from PROJECT.storage.sqlite import SqliteRuntime


async def start_admin_background_tasks(application) -> None:
    settings = application.bot_data["settings"]
    if not settings.admin_api.enabled:
        if "reminder_repository" not in application.bot_data:
            return
    else:
        application.bot_data["admin_outbox_delivery_task"] = application.create_task(
            run_outbox_delivery_loop(
                application.bot,
                interval_seconds=settings.admin_api.outbox_poll_interval_seconds,
                runtime=application.bot_data["admin_runtime"],
            ),
            name="admin_outbox_delivery_loop",
        )
    reminder_repository = application.bot_data.get("reminder_repository")
    if reminder_repository is not None:
        application.bot_data["reminder_delivery_task"] = application.create_task(
            run_reminder_delivery_loop(
                application.bot,
                reminder_repository,
                interval_seconds=DEFAULT_REMINDER_POLL_INTERVAL_SECONDS,
            ),
            name="reminder_delivery_loop",
        )


def create_application(settings: Settings, *, sqlite_runtime: SqliteRuntime | None = None):
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
    if settings.admin_api.enabled or sqlite_runtime is not None:
        builder = builder.post_init(start_admin_background_tasks)
    application = builder.build()
    application.bot_data["settings"] = settings
    application.bot_data["llm_runtime_mode"] = settings.llm_runtime_mode
    application.bot_data["gemini_recovery_classifier"] = gemini_recovery_classifier
    application.bot_data["gemini_edit_intent_resolver"] = gemini_edit_intent_resolver
    application.bot_data["admin_runtime"] = (
        SqliteAdminRuntime(sqlite_runtime.connection)
        if sqlite_runtime is not None
        else admin_runtime
    )
    if sqlite_runtime is not None:
        application.bot_data["invitation_repository"] = SqliteInvitationRepository(sqlite_runtime.connection)
        application.bot_data["onboarding_repository"] = SqliteOnboardingRepository(sqlite_runtime.connection)
        application.bot_data["field_registry_repository"] = SqliteFieldRegistryRepository(sqlite_runtime.connection)
        application.bot_data["season_activity_repository"] = SqliteSeasonActivityRepository(sqlite_runtime.connection)
        application.bot_data["evidence_repository"] = SqliteEvidenceRepository(sqlite_runtime.connection)
        application.bot_data["input_resolution_repository"] = SqliteInputResolutionRepository(sqlite_runtime.connection)
        application.bot_data["reminder_repository"] = SqliteReminderRepository(sqlite_runtime.connection)
        application.bot_data["field_binding_service"] = FieldBindingService(
            application.bot_data["field_registry_repository"]
        )
        application.bot_data["season_activity_service"] = SeasonActivityService(
            application.bot_data["season_activity_repository"],
            application.bot_data["field_registry_repository"],
        )
        application.bot_data["evidence_submission_service"] = EvidenceSubmissionService(
            application.bot_data["evidence_repository"],
            application.bot_data["field_registry_repository"],
        )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("myfields", myfields_command))
    application.add_handler(CommandHandler("fertilizer", fertilizer_command))
    application.add_handler(CommandHandler("yield", yield_command))
    application.add_handler(CommandHandler("resolve", input_resolve_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.LOCATION, location_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    return application
