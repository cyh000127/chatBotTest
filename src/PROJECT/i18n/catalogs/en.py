from datetime import datetime

BUTTON_TODAY_DATE = "Today's date"
BUTTON_TODAY_WEATHER = "Today's weather"
BUTTON_PROFILE = "Profile input"
BUTTON_HELP = "Help"
BUTTON_BACK = "Back"
BUTTON_CANCEL = "Cancel"
BUTTON_RESTART = "Start over"
BUTTON_CONFIRM = "Confirm"
BUTTON_EDIT = "Edit"
BUTTON_PREV_YEARS = "Previous 12 years"
BUTTON_NEXT_YEARS = "Next 12 years"

LANGUAGE_NAME = "English"
LANGUAGE_MENU_MESSAGE = "Choose a language."
LANGUAGE_CHANGED_MESSAGE = "Language has been changed to English."

CITY_BUTTON_TO_KEY = {
    "Seoul": "서울",
    "Busan": "부산",
    "Jeju": "제주",
}

START_MESSAGE = "Started.\nChoose today's date or today's weather."
MAIN_MENU_MESSAGE = "Main menu.\nChoose today's date or today's weather."
WEATHER_MENU_MESSAGE = "Choose a city to check today's weather."
PROFILE_ENTRY_MESSAGE = (
    "Starting profile input.\n"
    "Let's begin with your name."
)
CANCEL_MESSAGE = "Current task has been cancelled.\nUse 'Start over' or /start to begin again."
BACK_LIMIT_MESSAGE = "There is no previous step.\nPlease choose again from the main menu."
BACK_TO_MAIN_MESSAGE = "Returned to the previous step.\nChoose today's date or today's weather again."
BACK_TO_WEATHER_MESSAGE = "Returned to the weather selection step.\nChoose a city again."
BACK_GENERIC_MESSAGE = "Returned to the previous state."
WEATHER_ERROR_MESSAGE = "Could not fetch the weather.\nPlease try again shortly."
UNKNOWN_COMMAND_MESSAGE = "Unsupported command.\nUse /help or /menu."

HELP_MESSAGE = (
    "Available commands:\n"
    "- /start : go to the starting point\n"
    "- /help : show help\n"
    "- /menu : open the main menu\n"
    "- /profile : start profile input\n"
    "- /language : change language\n"
    "- Back : go to the previous step\n"
    "- Cancel : stop the current flow\n"
    "- Start over : reset the session and start again"
)

FALLBACK_MESSAGES = {
    "default": "Unknown input.\nUse menu buttons or /help.",
    "weather": "Unknown input.\nChoose a city button or use 'Back'.",
    "cancelled": "The current task is cancelled.\nUse 'Start over' or /start to begin again.",
    "profile_input": "Please enter the requested profile value again.",
    "profile_followup": "Additional confirmation is needed.\nPlease follow the prompt again.",
    "profile_confirm": "A draft is ready.\nChoose [Confirm] or [Edit].",
}

PROFILE_CONFIRMED_MESSAGE = "Input confirmed.\nSaved in the current session."
PROFILE_EDIT_MESSAGE = "We will restart profile input from the beginning."
PROFILE_NAME_PROMPT = "Please enter your name."
PROFILE_RESIDENCE_PROMPT = "Please enter your residence."
PROFILE_CITY_PROMPT = "Please enter your city/province.\nExample: Seoul, Gyeonggi-do"
PROFILE_DISTRICT_PROMPT = "Please enter your district/county/city.\nExample: Gangnam-gu, Bundang-gu"
PROFILE_BIRTH_YEAR_PROMPT = "Select your birth year using the buttons."
PROFILE_BIRTH_MONTH_PROMPT = "Select your birth month using the buttons."
PROFILE_BIRTH_DAY_PROMPT = "Select your birth day using the buttons."
PROFILE_NAME_FALLBACK = "Please enter your name again."
PROFILE_RESIDENCE_FALLBACK = "Please enter your residence again."
PROFILE_CITY_FALLBACK = "Please enter a valid city/province again.\nExample: Seoul, Gyeonggi-do"
PROFILE_DISTRICT_FALLBACK = "Please enter a valid district/county/city again.\nExample: Gangnam-gu, Bundang-gu"
PROFILE_BIRTH_YEAR_FALLBACK = "Please select a birth year button."
PROFILE_BIRTH_MONTH_FALLBACK = "Please select a birth month button."
PROFILE_BIRTH_DAY_FALLBACK = "Please select a birth day button."
PROFILE_CONFIRM_FALLBACK = "Choose [Confirm] or [Edit]."
PROFILE_REPAIR_NAME_MESSAGE = "Let's re-enter the name."
PROFILE_REPAIR_RESIDENCE_MESSAGE = "Let's re-enter the residence."
PROFILE_REPAIR_CITY_MESSAGE = "Let's re-enter the city/province."
PROFILE_REPAIR_DISTRICT_MESSAGE = "Let's re-enter the district/county/city."
PROFILE_REPAIR_BIRTH_MESSAGE = "Let's re-enter the birth date.\nPlease choose the birth year."


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "Please confirm.\n"
        f"- Name: {name}\n"
        f"- Residence: {residence}\n"
        f"- City/Province: {city}\n"
        f"- District/County/City: {district}\n"
        f"- Birth date: {birth_date}\n"
        "\nChoose [Confirm] if correct, or [Edit] to change it."
    )


WEATHER_CODE_LABELS = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Cloudy",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail",
    99: "Thunderstorm with heavy hail",
}


def weather_code_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"Unknown condition ({code})")


def format_today_date(current: datetime) -> str:
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday = weekdays[current.weekday()]
    return (
        "Today's date.\n"
        f"- Date: {current.strftime('%Y-%m-%d')} ({weekday})\n"
        f"- Time: {current.strftime('%H:%M:%S')} KST"
    )


def format_weather(
    *,
    city: str,
    observed_at: datetime,
    weather_label: str,
    temperature: float,
    apparent_temperature: float,
    wind_speed: float,
) -> str:
    return (
        f"Current weather in {city}.\n"
        f"- Observed at: {observed_at.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"- Condition: {weather_label}\n"
        f"- Temperature: {temperature:.1f}°C\n"
        f"- Feels like: {apparent_temperature:.1f}°C\n"
        f"- Wind speed: {wind_speed:.1f} km/h"
    )
