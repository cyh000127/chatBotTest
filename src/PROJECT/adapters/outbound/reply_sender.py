from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from PROJECT.telemetry.delivery_status import DeliveryStatus


def _reply_markup(keyboard_layout: list[list[dict[str, str]]] | None):
    if keyboard_layout is None:
        return None
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(button["text"], callback_data=button["data"])
                for button in row
            ]
            for row in keyboard_layout
        ]
    )


async def send_text(update, text: str, *, keyboard_layout: list[list[dict[str, str]]] | None = None) -> DeliveryStatus:
    message = update.effective_message
    if message is None:
        return DeliveryStatus.FAILED

    try:
        await message.reply_text(text, reply_markup=_reply_markup(keyboard_layout))
    except Exception:
        return DeliveryStatus.FAILED
    return DeliveryStatus.SENT
