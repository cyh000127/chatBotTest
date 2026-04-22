import os
from dataclasses import dataclass

from dotenv import load_dotenv
from PROJECT.policy import AiMode, ai_mode_allows_edit_intent, ai_mode_allows_recovery_assist, parse_ai_mode

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_TIMEOUT_SECONDS = 15.0
TRUE_ENV_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str
    model: str
    api_base: str
    timeout_seconds: float


@dataclass(frozen=True)
class Settings:
    bot_token: str
    weather_api_base: str = "https://api.open-meteo.com/v1/forecast"
    timezone_name: str = "Asia/Seoul"
    gemini: GeminiSettings | None = None
    ai_mode: AiMode = AiMode.DISABLED

    @property
    def enable_llm_edit_intent(self) -> bool:
        return ai_mode_allows_edit_intent(self.ai_mode)

    @property
    def enable_llm_recovery(self) -> bool:
        return ai_mode_allows_recovery_assist(self.ai_mode)


def parse_bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_ENV_VALUES


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
    ai_mode = parse_ai_mode(ai_mode_raw)
    if not ai_mode_raw and legacy_edit_intent_enabled:
        ai_mode = AiMode.REPAIR_ASSIST_ONLY

    return Settings(
        bot_token=bot_token,
        gemini=gemini_settings,
        ai_mode=ai_mode,
    )
