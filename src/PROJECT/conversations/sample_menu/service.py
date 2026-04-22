from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from PROJECT.conversations.sample_menu.states import STATE_LANGUAGE_SELECT, STATE_MAIN_MENU, STATE_WEATHER_MENU
from PROJECT.rule_engine.contracts import ValidationResult
from PROJECT.settings import Settings

KST = timezone(timedelta(hours=9), name="KST")

WEATHER_LOCATIONS = {
    "서울": {"label": "서울", "latitude": 37.5665, "longitude": 126.9780},
    "부산": {"label": "부산", "latitude": 35.1796, "longitude": 129.0756},
    "제주": {"label": "제주", "latitude": 33.4996, "longitude": 126.5312},
}


@dataclass(frozen=True)
class WeatherSnapshot:
    city: str
    observed_at: datetime
    weather_code: int
    temperature: float
    apparent_temperature: float
    wind_speed: float


def start_text(catalog) -> str:
    return catalog.START_MESSAGE


def help_text(catalog) -> str:
    return catalog.HELP_MESSAGE


def main_menu_text(catalog) -> str:
    return catalog.MAIN_MENU_MESSAGE


def weather_menu_text(catalog) -> str:
    return catalog.WEATHER_MENU_MESSAGE


def cancel_text(catalog) -> str:
    return catalog.CANCEL_MESSAGE


def back_text(previous_state: str | None, catalog) -> str:
    if previous_state is None:
        return catalog.BACK_LIMIT_MESSAGE
    if previous_state == STATE_MAIN_MENU:
        return catalog.BACK_TO_MAIN_MESSAGE
    if previous_state == STATE_WEATHER_MENU:
        return catalog.BACK_TO_WEATHER_MESSAGE
    if previous_state == STATE_LANGUAGE_SELECT:
        return catalog.BACK_GENERIC_MESSAGE
    return catalog.BACK_GENERIC_MESSAGE


def today_date_text(catalog, now: datetime | None = None) -> str:
    current = now or datetime.now(KST)
    return catalog.format_today_date(current)


def weather_result_text(snapshot: WeatherSnapshot, catalog) -> str:
    return catalog.format_weather(
        city=snapshot.city,
        observed_at=snapshot.observed_at,
        weather_label=catalog.weather_code_label(snapshot.weather_code),
        temperature=snapshot.temperature,
        apparent_temperature=snapshot.apparent_temperature,
        wind_speed=snapshot.wind_speed,
    )


def weather_error_text(catalog) -> str:
    return catalog.WEATHER_ERROR_MESSAGE


def fallback_text(key: str, catalog) -> str:
    return catalog.FALLBACK_MESSAGES[key]


def cheap_gate_text(result: ValidationResult, fallback_key: str, catalog) -> str:
    if result.reason == "explicit_support_request":
        return catalog.CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE
    if result.reason == "manual_handoff_request":
        return catalog.CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE
    if result.reason == "recovery_retry_limit_exceeded":
        return catalog.CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE
    return fallback_text(fallback_key, catalog)


def unknown_command_text(catalog) -> str:
    return catalog.UNKNOWN_COMMAND_MESSAGE


def language_menu_text(catalog) -> str:
    return catalog.LANGUAGE_MENU_MESSAGE


def language_changed_text(catalog) -> str:
    return catalog.LANGUAGE_CHANGED_MESSAGE


def auth_start_text(catalog) -> str:
    return catalog.AUTH_START_PROMPT


def auth_required_text(catalog) -> str:
    return catalog.AUTH_REQUIRED_MESSAGE


def auth_invalid_text(catalog) -> str:
    return catalog.AUTH_INVALID_MESSAGE


def auth_retry_limit_text(catalog) -> str:
    return catalog.AUTH_RETRY_LIMIT_MESSAGE


def auth_welcome_text(catalog, user_name: str) -> str:
    return catalog.AUTH_WELCOME_MESSAGE.format(user_name=user_name)


def auth_already_logged_in_text(catalog, user_name: str) -> str:
    return catalog.AUTH_ALREADY_LOGGED_IN_MESSAGE.format(user_name=user_name)


async def fetch_weather(city: str, settings: Settings) -> WeatherSnapshot:
    location = WEATHER_LOCATIONS[city]
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "timezone": settings.timezone_name,
        "forecast_days": 1,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.weather_api_base, params=params)
        response.raise_for_status()

    current = response.json()["current"]
    observed_at = datetime.fromisoformat(current["time"])
    return WeatherSnapshot(
        city=location["label"],
        observed_at=observed_at,
        weather_code=int(current["weather_code"]),
        temperature=float(current["temperature_2m"]),
        apparent_temperature=float(current["apparent_temperature"]),
        wind_speed=float(current["wind_speed_10m"]),
    )
