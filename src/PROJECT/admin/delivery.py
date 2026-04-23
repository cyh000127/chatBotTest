from __future__ import annotations

import asyncio

from PROJECT.admin.follow_up import InMemoryAdminRuntime, admin_runtime
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import OUTBOX_MESSAGE_FAILED, OUTBOX_MESSAGE_SENT


async def deliver_pending_outbox(bot, *, runtime: InMemoryAdminRuntime = admin_runtime, limit: int = 10) -> int:
    delivered = 0
    for message in runtime.claim_pending_outbox(limit=limit):
        try:
            await bot.send_message(chat_id=message.chat_id, text=message.text)
        except Exception as exc:  # pragma: no cover - exception type depends on Telegram transport
            runtime.mark_outbox_failed(message.outbox_id, str(exc))
            log_event(
                OUTBOX_MESSAGE_FAILED,
                source="admin.outbox.delivery",
                outbox_id=message.outbox_id,
                follow_up_id=message.follow_up_id,
                chat_id=message.chat_id,
                error_type=type(exc).__name__,
            )
            continue
        runtime.mark_outbox_sent(message.outbox_id)
        log_event(
            OUTBOX_MESSAGE_SENT,
            source="admin.outbox.delivery",
            outbox_id=message.outbox_id,
            follow_up_id=message.follow_up_id,
            chat_id=message.chat_id,
        )
        delivered += 1
    return delivered


async def run_outbox_delivery_loop(
    bot,
    *,
    interval_seconds: float,
    runtime: InMemoryAdminRuntime = admin_runtime,
) -> None:
    while True:
        await deliver_pending_outbox(bot, runtime=runtime)
        await asyncio.sleep(interval_seconds)
