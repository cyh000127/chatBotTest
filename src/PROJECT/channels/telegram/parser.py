from PROJECT.adapters.inbound.telegram_update import TelegramInboundUpdate
from PROJECT.identity.assertion_extractor import extract_identity


def parse_update(update) -> TelegramInboundUpdate:
    message = update.effective_message
    text = message.text.strip() if message and message.text else ""
    command = ""
    if text.startswith("/"):
        command = text.split()[0]

    identity = extract_identity(update)
    return TelegramInboundUpdate(
        chat_id=identity["chat_id"],
        user_id=identity["user_id"],
        text=text,
        command=command,
    )
