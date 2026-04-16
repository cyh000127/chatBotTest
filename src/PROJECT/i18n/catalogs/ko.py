from datetime import datetime

BUTTON_TODAY_DATE = "오늘 날짜"
BUTTON_TODAY_WEATHER = "오늘 날씨"
BUTTON_PROFILE = "프로필 입력"
BUTTON_HELP = "도움말"
BUTTON_BACK = "뒤로가기"
BUTTON_CANCEL = "취소"
BUTTON_RESTART = "처음부터"
BUTTON_CONFIRM = "확인"
BUTTON_EDIT = "수정"

CITY_LABELS = ("서울", "부산", "제주")

START_MESSAGE = "시작합니다.\n오늘의 날짜와 날씨를 선택하세요."
MAIN_MENU_MESSAGE = "메인 메뉴입니다.\n오늘의 날짜와 날씨를 선택하세요."
WEATHER_MENU_MESSAGE = "오늘 날씨를 확인할 도시를 선택하세요."
PROFILE_ENTRY_MESSAGE = (
    "프로필 자유입력 모드입니다.\n"
    "이름, 생년월일, 거주지를 한 번에 입력해주세요.\n"
    "예: 김민수 서울 강남 1998년 4월 20일"
)
CANCEL_MESSAGE = "현재 작업을 취소했습니다.\n'처음부터' 또는 /start 로 다시 시작할 수 있습니다."
BACK_LIMIT_MESSAGE = "더 이상 뒤로갈 단계가 없습니다.\n메인 메뉴에서 다시 선택하세요."
BACK_TO_MAIN_MESSAGE = "이전 단계로 돌아왔습니다.\n오늘의 날짜와 날씨를 다시 선택하세요."
BACK_TO_WEATHER_MESSAGE = "날씨 선택 단계로 돌아왔습니다.\n도시를 다시 선택하세요."
BACK_GENERIC_MESSAGE = "이전 상태로 돌아왔습니다."
WEATHER_ERROR_MESSAGE = "날씨 정보를 가져오지 못했습니다.\n잠시 후 다시 시도하세요."
UNKNOWN_COMMAND_MESSAGE = "지원하지 않는 명령어입니다.\n/help 또는 /menu 를 사용하세요."

HELP_MESSAGE = (
    "사용 가능한 명령어 목록입니다.\n"
    "- /start : 처음 진입점으로 이동\n"
    "- /help : 도움말 보기\n"
    "- /menu : 메인 메뉴 열기\n"
    "- /profile : 프로필 자유입력 시작\n"
    "- 뒤로가기 : 이전 단계로 이동\n"
    "- 취소 : 현재 흐름 종료\n"
    "- 처음부터 : 세션을 초기화하고 다시 시작"
)

FALLBACK_MESSAGES = {
    "default": "알 수 없는 입력입니다.\n메뉴 버튼이나 /help 를 사용하세요.",
    "weather": "알 수 없는 입력입니다.\n도시 버튼을 선택하거나 '뒤로가기'를 사용하세요.",
    "cancelled": "현재 작업은 취소된 상태입니다.\n'처음부터' 또는 /start 로 다시 시작하세요.",
    "profile_input": "프로필 입력 형식으로 다시 보내주세요.\n예: 김민수 서울 강남 1998년 4월 20일",
    "profile_followup": "추가 확인이 필요합니다.\n안내된 형식으로 다시 입력하거나 버튼을 눌러주세요.",
    "profile_confirm": "초안이 준비돼 있어요.\n[확인] 또는 [수정]을 선택해주세요.",
}

PROFILE_CONFIRMED_MESSAGE = "초안을 확인했습니다.\n현재 세션에 저장해두었어요."
PROFILE_EDIT_MESSAGE = "프로필 초안을 다시 입력해주세요."
PROFILE_MISSING_NAME_MESSAGE = "이름을 확인하지 못했어요.\n이름을 포함해서 다시 입력해주세요."
PROFILE_MISSING_BIRTH_MESSAGE = "생년월일을 확인하지 못했어요.\n예: 1998-04-20 또는 1998년 4월 20일"
PROFILE_MISSING_RESIDENCE_MESSAGE = "거주지를 확인하지 못했어요.\n예: 서울특별시 강남구"
PROFILE_CITY_FOLLOWUP_MESSAGE = (
    "거주지를 조금 더 확인할게요.\n"
    "{district}는 어느 시/도에 해당하나요?\n"
    "예: {examples}"
)
PROFILE_DISTRICT_FOLLOWUP_MESSAGE = (
    "{city}까지 확인했어요.\n"
    "어느 구/군/시에 거주하시나요?\n"
    "예: {examples}"
)
PROFILE_AMBIGUOUS_DISTRICT_MESSAGE = (
    "{keyword}은(는) 여러 후보가 있어요.\n"
    "아래 중 어디에 해당하나요?"
)


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
) -> str:
    return (
        "확인했어요.\n"
        f"- 이름: {name}\n"
        f"- 생년월일: {birth_date}\n"
        f"- 거주지: {city} {district}\n\n"
        "맞으면 [확인], 수정하려면 [수정]을 눌러주세요."
    )

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


def weather_code_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"알 수 없는 상태({code})")


def format_today_date(current: datetime) -> str:
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekdays[current.weekday()]
    return (
        "오늘 날짜입니다.\n"
        f"- 날짜: {current.strftime('%Y-%m-%d')} ({weekday})\n"
        f"- 시간: {current.strftime('%H:%M:%S')} KST"
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
        f"{city} 현재 날씨입니다.\n"
        f"- 관측 시각: {observed_at.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"- 상태: {weather_label}\n"
        f"- 기온: {temperature:.1f}°C\n"
        f"- 체감: {apparent_temperature:.1f}°C\n"
        f"- 풍속: {wind_speed:.1f} km/h"
    )
