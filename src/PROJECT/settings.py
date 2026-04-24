import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from PROJECT.policy import (
    LocalAiGate,
    local_ai_gate_allows_edit_intent,
    local_ai_gate_allows_recovery_assist,
    parse_local_ai_gate,
)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_TIMEOUT_SECONDS = 15.0
TRUE_ENV_VALUES = {"1", "true", "yes", "on"}
DEFAULT_ADMIN_API_HOST = "127.0.0.1"
DEFAULT_ADMIN_API_PORT = 8000
DEFAULT_ADMIN_OUTBOX_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_ADMIN_API_ACCESS_ROLE = "operator"
ADMIN_API_ACCESS_ROLES = {"viewer", "operator"}
DEFAULT_SQLITE_BUSY_TIMEOUT_MS = 5000


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str
    model: str
    api_base: str
    timeout_seconds: float


@dataclass(frozen=True)
class AdminApiSettings:
    enabled: bool = False
    host: str = DEFAULT_ADMIN_API_HOST
    port: int = DEFAULT_ADMIN_API_PORT
    outbox_poll_interval_seconds: float = DEFAULT_ADMIN_OUTBOX_POLL_INTERVAL_SECONDS
    access_token: str = ""
    access_role: str = DEFAULT_ADMIN_API_ACCESS_ROLE

    @property
    def access_control_enabled(self) -> bool:
        return bool(self.access_token)

    @property
    def write_access_enabled(self) -> bool:
        return self.access_role == "operator"


@dataclass(frozen=True)
class SqliteSettings:
    database_path: str = ""
    migrations_enabled: bool = False
    busy_timeout_ms: int = DEFAULT_SQLITE_BUSY_TIMEOUT_MS

    @property
    def enabled(self) -> bool:
        return bool(self.database_path)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    gemini: GeminiSettings | None = None
    local_ai_gate: LocalAiGate = LocalAiGate.DISABLED
    admin_api: AdminApiSettings = AdminApiSettings()
    sqlite: SqliteSettings = SqliteSettings()

    @property
    def ai_mode(self) -> LocalAiGate:
        return self.local_ai_gate

    @property
    def enable_llm_edit_intent(self) -> bool:
        return local_ai_gate_allows_edit_intent(self.local_ai_gate)

    @property
    def enable_llm_recovery(self) -> bool:
        return local_ai_gate_allows_recovery_assist(self.local_ai_gate)

    @property
    def llm_edit_intent_runtime_enabled(self) -> bool:
        return self.gemini is not None and self.enable_llm_edit_intent

    @property
    def llm_recovery_runtime_enabled(self) -> bool:
        return self.gemini is not None and self.enable_llm_recovery

    @property
    def llm_runtime_assisted(self) -> bool:
        return self.llm_edit_intent_runtime_enabled or self.llm_recovery_runtime_enabled

    @property
    def manual_review_fallback_active(self) -> bool:
        return self.local_ai_gate == LocalAiGate.MANUAL_REVIEW_FALLBACK

    @property
    def runtime_rules_only(self) -> bool:
        if self.manual_review_fallback_active:
            return True
        return not self.llm_runtime_assisted

    @property
    def llm_runtime_mode(self) -> str:
        if self.manual_review_fallback_active:
            return "rules_only_manual_review"
        if self.runtime_rules_only:
            return "rules_only_disabled"
        return "llm_assisted"


def parse_bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_ENV_VALUES


def parse_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    if value < 0:
        return default
    return value


def parse_admin_api_access_role(raw: str) -> str:
    role = raw.strip().lower()
    if role in ADMIN_API_ACCESS_ROLES:
        return role
    return DEFAULT_ADMIN_API_ACCESS_ROLE


def load_sqlite_settings() -> SqliteSettings:
    database_path = os.getenv("SQLITE_DATABASE_PATH", "").strip()
    if database_path and not Path(database_path).is_absolute():
        raise ValueError("SQLITE_DATABASE_PATH 는 절대 경로여야 합니다.")
    return SqliteSettings(
        database_path=database_path,
        migrations_enabled=parse_bool_env("SQLITE_MIGRATIONS_ENABLED", default=False),
        busy_timeout_ms=parse_int_env("SQLITE_BUSY_TIMEOUT_MS", DEFAULT_SQLITE_BUSY_TIMEOUT_MS),
    )


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN 이 없습니다. .env 파일을 확인하세요.")

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_timeout_raw = os.getenv("GEMINI_TIMEOUT_SECONDS", str(DEFAULT_GEMINI_TIMEOUT_SECONDS)).strip()
    try:
        gemini_timeout_seconds = float(gemini_timeout_raw)
    except ValueError:
        gemini_timeout_seconds = DEFAULT_GEMINI_TIMEOUT_SECONDS

    gemini_settings = None
    if gemini_api_key:
        gemini_settings = GeminiSettings(
            api_key=gemini_api_key,
            model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL,
            api_base=os.getenv("GEMINI_API_BASE", DEFAULT_GEMINI_API_BASE).strip() or DEFAULT_GEMINI_API_BASE,
            timeout_seconds=gemini_timeout_seconds,
        )

    ai_mode_raw = os.getenv("AI_MODE", "").strip()
    legacy_edit_intent_enabled = parse_bool_env("ENABLE_LLM_EDIT_INTENT", default=False)
    local_ai_gate = parse_local_ai_gate(ai_mode_raw)
    if not ai_mode_raw and legacy_edit_intent_enabled:
        local_ai_gate = LocalAiGate.REPAIR_ASSIST_ONLY

    admin_api_host = os.getenv("ADMIN_API_HOST", DEFAULT_ADMIN_API_HOST).strip() or DEFAULT_ADMIN_API_HOST
    admin_api_port_raw = os.getenv("ADMIN_API_PORT", str(DEFAULT_ADMIN_API_PORT)).strip()
    try:
        admin_api_port = int(admin_api_port_raw)
    except ValueError:
        admin_api_port = DEFAULT_ADMIN_API_PORT
    admin_outbox_poll_interval_raw = os.getenv(
        "ADMIN_OUTBOX_POLL_INTERVAL_SECONDS",
        str(DEFAULT_ADMIN_OUTBOX_POLL_INTERVAL_SECONDS),
    ).strip()
    try:
        admin_outbox_poll_interval_seconds = float(admin_outbox_poll_interval_raw)
    except ValueError:
        admin_outbox_poll_interval_seconds = DEFAULT_ADMIN_OUTBOX_POLL_INTERVAL_SECONDS

    return Settings(
        bot_token=bot_token,
        gemini=gemini_settings,
        local_ai_gate=local_ai_gate,
        admin_api=AdminApiSettings(
            enabled=parse_bool_env("ADMIN_API_ENABLED", default=False),
            host=admin_api_host,
            port=admin_api_port,
            outbox_poll_interval_seconds=admin_outbox_poll_interval_seconds,
            access_token=os.getenv("ADMIN_API_ACCESS_TOKEN", "").strip(),
            access_role=parse_admin_api_access_role(
                os.getenv("ADMIN_API_ACCESS_ROLE", DEFAULT_ADMIN_API_ACCESS_ROLE)
            ),
        ),
        sqlite=load_sqlite_settings(),
    )
