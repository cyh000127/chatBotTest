import os
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
KST = timezone(timedelta(hours=9), name="KST")

STATE_MAIN_MENU = "main_menu"
STATE_WEATHER_MENU = "weather_menu"
STATE_CANCELLED = "cancelled"

BUTTON_TODAY_DATE = "오늘 날짜"
BUTTON_TODAY_WEATHER = "오늘 날씨"
BUTTON_HELP = "도움말"
BUTTON_BACK = "뒤로가기"
BUTTON_CANCEL = "취소"
BUTTON_RESTART = "처음부터"

WEATHER_LOCATIONS = {
    "서울": {"label": "서울", "latitude": 37.5665, "longitude": 126.9780},
    "부산": {"label": "부산", "latitude": 35.1796, "longitude": 129.0756},
    "제주": {"label": "제주", "latitude": 33.4996, "longitude": 126.5312},
}

WEATHER_CODE_LABELS = {
    0: "맑음",
    1: "대체로 맑음",
    2: "부분적으로 흐림",
    3: "흐림",
    45: "안개",
    48: "서리 안개",
    51: "약한 이슬비",
    53: "이슬비",
    55: "강한 이슬비",
    56: "약한 어는 이슬비",
    57: "강한 어는 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    66: "약한 어는 비",
    67: "강한 어는 비",
    71: "약한 눈",
    73: "눈",
    75: "강한 눈",
    77: "진눈깨비",
    80: "약한 소나기",
    81: "소나기",
    82: "강한 소나기",
    85: "약한 눈 소나기",
    86: "강한 눈 소나기",
    95: "뇌우",
    96: "약한 우박 동반 뇌우",
    99: "강한 우박 동반 뇌우",
}


def get_session(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault(
        "session",
        {
            "state": STATE_MAIN_MENU,
            "history": [],
            "selected_city": None,
        },
    )


def reset_session(context: ContextTypes.DEFAULT_TYPE) -> dict:
    context.user_data["session"] = {
        "state": STATE_MAIN_MENU,
        "history": [],
        "selected_city": None,
    }
    return context.user_data["session"]


def set_state(
    context: ContextTypes.DEFAULT_TYPE,
    new_state: str,
    *,
    push_history: bool = False,
) -> dict:
    session = get_session(context)
    current_state = session["state"]

    if push_history and current_state != new_state:
        session["history"].append(current_state)

    session["state"] = new_state
    return session


def go_back(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    session = get_session(context)
    history = session["history"]
    if not history:
        return None

    previous_state = history.pop()
    session["state"] = previous_state
    return previous_state


def current_date_message() -> str:
    now = datetime.now(KST)
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekdays[now.weekday()]
    return (
        "오늘 날짜입니다.\n"
        f"- 날짜: {now.strftime('%Y-%m-%d')} ({weekday})\n"
        f"- 시간: {now.strftime('%H:%M:%S')} KST"
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BUTTON_TODAY_DATE, BUTTON_TODAY_WEATHER],
            [BUTTON_HELP, BUTTON_RESTART],
            [BUTTON_CANCEL],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def weather_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["서울", "부산", "제주"],
            [BUTTON_BACK, BUTTON_RESTART],
            [BUTTON_HELP, BUTTON_CANCEL],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def cancelled_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BUTTON_RESTART, BUTTON_HELP]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def keyboard_for_state(state: str):
    if state == STATE_WEATHER_MENU:
        return weather_menu_keyboard()
    if state == STATE_CANCELLED:
        return cancelled_keyboard()
    return main_menu_keyboard()


async def show_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    message: str | None = None,
    clear_history: bool = False,
) -> None:
    session = reset_session(context) if clear_history else set_state(context, STATE_MAIN_MENU)
    if clear_history:
        session["history"] = []

    text = message or "메인 메뉴입니다.\n'오늘 날짜' 또는 '오늘 날씨'를 선택하세요."
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def show_weather_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    message: str | None = None,
    push_history: bool = True,
) -> None:
    set_state(context, STATE_WEATHER_MENU, push_history=push_history)
    text = message or "오늘 날씨를 확인할 도시를 선택하세요."
    await update.message.reply_text(text, reply_markup=weather_menu_keyboard())


def weather_code_to_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"알 수 없는 상태({code})")


async def fetch_weather(city: str) -> str:
    location = WEATHER_LOCATIONS[city]
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "timezone": "Asia/Seoul",
        "forecast_days": 1,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
        response.raise_for_status()

    payload = response.json()
    current = payload["current"]
    observed_at = datetime.fromisoformat(current["time"])

    return (
        f"{location['label']} 현재 날씨입니다.\n"
        f"- 관측 시각: {observed_at.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"- 상태: {weather_code_to_label(current['weather_code'])}\n"
        f"- 기온: {current['temperature_2m']}°C\n"
        f"- 체감: {current['apparent_temperature']}°C\n"
        f"- 풍속: {current['wind_speed_10m']} km/h"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reset_session(context)
    await update.message.reply_text(
        "시작합니다.\n오늘의 날짜와 날씨를 선택하세요.",
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    await update.message.reply_text(
        "사용 가능한 명령어 목록입니다.\n"
        "- /start : 처음 진입점으로 이동\n"
        "- /help : 도움말 보기\n"
        "- /menu : 메인 메뉴 열기\n"
        "- 뒤로가기 : 이전 단계로 이동\n"
        "- 취소 : 현재 흐름 종료\n"
        "- 처음부터 : 세션을 초기화하고 다시 시작",
        reply_markup=keyboard_for_state(session["state"]),
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_main_menu(
        update,
        context,
        message="메인 메뉴입니다.\n오늘의 날짜와 날씨를 선택하세요.",
        clear_history=True,
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = reset_session(context)
    session["state"] = STATE_CANCELLED
    await update.message.reply_text(
        "현재 작업을 취소했습니다.\n'처음부터' 또는 /start 로 다시 시작할 수 있습니다.",
        reply_markup=cancelled_keyboard(),
    )


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    previous_state = go_back(context)
    if previous_state is None:
        await update.message.reply_text(
            "더 이상 뒤로갈 단계가 없습니다.\n메인 메뉴에서 다시 선택하세요.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if previous_state == STATE_MAIN_MENU:
        await show_main_menu(
            update,
            context,
            message="이전 단계로 돌아왔습니다.\n오늘의 날짜와 날씨를 다시 선택하세요.",
        )
        return

    if previous_state == STATE_WEATHER_MENU:
        await show_weather_menu(
            update,
            context,
            message="날씨 선택 단계로 돌아왔습니다.\n도시를 다시 선택하세요.",
            push_history=False,
        )
        return

    await update.message.reply_text(
        "이전 상태로 돌아왔습니다.",
        reply_markup=keyboard_for_state(previous_state),
    )


async def handle_today_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    await update.message.reply_text(
        current_date_message(),
        reply_markup=keyboard_for_state(session["state"]),
    )


async def handle_weather_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    city: str,
) -> None:
    session = get_session(context)
    session["selected_city"] = city

    try:
        weather_message = await fetch_weather(city)
    except httpx.HTTPError:
        await update.message.reply_text(
            "날씨 정보를 가져오지 못했습니다.\n잠시 후 다시 시도하세요.",
            reply_markup=weather_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        weather_message,
        reply_markup=weather_menu_keyboard(),
    )


async def handle_unknown_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    state = session["state"]

    if state == STATE_WEATHER_MENU:
        message = "알 수 없는 입력입니다.\n도시 버튼을 선택하거나 '뒤로가기'를 사용하세요."
    elif state == STATE_CANCELLED:
        message = "현재 작업은 취소된 상태입니다.\n'처음부터' 또는 /start 로 다시 시작하세요."
    else:
        message = "알 수 없는 입력입니다.\n메뉴 버튼이나 /help 를 사용하세요."

    await update.message.reply_text(message, reply_markup=keyboard_for_state(state))


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or not update.message.text:
        return

    text = update.message.text.strip()
    state = get_session(context)["state"]

    if text == BUTTON_HELP:
        await help_command(update, context)
        return
    if text == BUTTON_RESTART:
        await restart_command(update, context)
        return
    if text == BUTTON_CANCEL:
        await cancel_command(update, context)
        return
    if text == BUTTON_BACK:
        await handle_back(update, context)
        return
    if text == BUTTON_TODAY_DATE:
        await handle_today_date(update, context)
        return
    if text == BUTTON_TODAY_WEATHER:
        await show_weather_menu(update, context)
        return

    if state == STATE_WEATHER_MENU and text in WEATHER_LOCATIONS:
        await handle_weather_selection(update, context, text)
        return

    await handle_unknown_input(update, context)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "지원하지 않는 명령어입니다.\n/help 또는 /menu 를 사용하세요.",
        reply_markup=keyboard_for_state(get_session(context)["state"]),
    )


def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN 이 없습니다. .env 파일을 확인하세요.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.run_polling()


if __name__ == "__main__":
    main()
