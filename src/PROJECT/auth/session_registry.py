from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True)
class AuthSessionRecord:
    identity_key: str
    login_id: str
    user_name: str


class ProcessAuthRegistry:
    """Process-local auth cache. It is intentionally cleared on server restart."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, AuthSessionRecord] = {}

    def set_authenticated(self, *, identity_key: str, login_id: str, user_name: str) -> AuthSessionRecord:
        record = AuthSessionRecord(
            identity_key=identity_key,
            login_id=login_id,
            user_name=user_name,
        )
        with self._lock:
            self._records[identity_key] = record
        return record

    def get(self, identity_key: str | None) -> AuthSessionRecord | None:
        if identity_key is None:
            return None
        with self._lock:
            return self._records.get(identity_key)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


def telegram_identity_key(update) -> str | None:
    effective_user = getattr(update, "effective_user", None)
    if effective_user is not None and getattr(effective_user, "id", None) is not None:
        return f"telegram:user:{effective_user.id}"
    effective_chat = getattr(update, "effective_chat", None)
    if effective_chat is not None and getattr(effective_chat, "id", None) is not None:
        return f"telegram:chat:{effective_chat.id}"
    return None


process_auth_registry = ProcessAuthRegistry()
