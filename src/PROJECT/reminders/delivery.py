from __future__ import annotations

import asyncio

from PROJECT.storage.reminders import SqliteReminderRepository
from PROJECT.telemetry.event_logger import log_event

DEFAULT_REMINDER_POLL_INTERVAL_SECONDS = 30.0
REMINDER_CREATED = "reminder_created"
REMINDER_SENT = "reminder_sent"
REMINDER_COMPLETED = "reminder_completed"


async def deliver_due_reminders(bot, repository: SqliteReminderRepository, *, limit: int = 10) -> int:
    delivered = 0
    for reminder in repository.due_pending_reminders(limit=limit):
        await bot.send_message(chat_id=reminder.chat_id, text=reminder.message_text)
        repository.mark_sent(reminder.id)
        log_event(
            REMINDER_SENT,
            source="reminder.delivery",
            reminder_id=reminder.id,
            resume_target_code=reminder.resume_target_code,
            chat_id=reminder.chat_id,
        )
        delivered += 1
    return delivered


async def run_reminder_delivery_loop(
    bot,
    repository: SqliteReminderRepository,
    *,
    interval_seconds: float = DEFAULT_REMINDER_POLL_INTERVAL_SECONDS,
) -> None:
    while True:
        await deliver_due_reminders(bot, repository)
        await asyncio.sleep(interval_seconds)
