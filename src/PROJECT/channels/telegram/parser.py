from PROJECT.adapters.inbound.telegram_update import TelegramInboundUpdate
from PROJECT.identity.assertion_extractor import extract_identity
from PROJECT.rule_engine import extract_command_token, normalize_whitespace


def parse_update(update) -> TelegramInboundUpdate:
    message = update.effective_message
    text = normalize_whitespace(message.text) if message and message.text else ""
    command = extract_command_token(text) or ""

    identity = extract_identity(update)
    return TelegramInboundUpdate(
        chat_id=identity["chat_id"],
        user_id=identity["user_id"],
        text=text,
        command=command,
    )
