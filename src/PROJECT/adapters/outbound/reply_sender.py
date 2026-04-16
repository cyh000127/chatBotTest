from telegram import ReplyKeyboardMarkup

from PROJECT.telemetry.delivery_status import DeliveryStatus


def _reply_markup(keyboard_layout: list[list[str]] | None):
    if keyboard_layout is None:
        return None
    return ReplyKeyboardMarkup(
        keyboard_layout,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


async def send_text(update, text: str, *, keyboard_layout: list[list[str]] | None = None) -> DeliveryStatus:
    message = update.effective_message
    if message is None:
        return DeliveryStatus.FAILED

    try:
        await message.reply_text(text, reply_markup=_reply_markup(keyboard_layout))
    except Exception:
        return DeliveryStatus.FAILED
    return DeliveryStatus.SENT
