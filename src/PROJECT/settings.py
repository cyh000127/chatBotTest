import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    weather_api_base: str = "https://api.open-meteo.com/v1/forecast"
    timezone_name: str = "Asia/Seoul"


def load_settings() -> Settings:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN 이 없습니다. .env 파일을 확인하세요.")
    return Settings(bot_token=bot_token)
