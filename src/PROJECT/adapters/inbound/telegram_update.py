from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramInboundUpdate:
    chat_id: int | None
    user_id: int | None
    text: str
    command: str = ""
