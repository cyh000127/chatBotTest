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
BUTTON_EDIT_NAME = "이름"
BUTTON_EDIT_RESIDENCE = "거주지"
BUTTON_EDIT_CITY = "시/도"
BUTTON_EDIT_DISTRICT = "구/군/시"
BUTTON_EDIT_BIRTH_DATE = "생년월일"
BUTTON_PREV_YEARS = "이전 12년"
BUTTON_NEXT_YEARS = "다음 12년"
LANGUAGE_NAME = "한국어"
LANGUAGE_MENU_MESSAGE = "언어를 선택하세요."
LANGUAGE_CHANGED_MESSAGE = "언어가 한국어로 변경되었습니다."
AUTH_START_PROMPT = "아이디를 입력해주세요.\n예: /start okccc5 또는 okccc5"
AUTH_REQUIRED_MESSAGE = "인증 후 이용할 수 있습니다.\n/start 를 입력한 뒤 아이디를 입력해주세요."
AUTH_INVALID_MESSAGE = "정확한 아이디를 입력하지 않았습니다. 다시 입력해주세요."
AUTH_RETRY_LIMIT_MESSAGE = "인증에 두 번 실패했습니다.\n처음부터 다시 시작합니다. /start 를 입력해주세요."
AUTH_WELCOME_MESSAGE = "어서오세요 {user_name}님!"
AUTH_ALREADY_LOGGED_IN_MESSAGE = "어서오세요 {user_name}님!"

CITY_LABELS = ("서울", "부산", "제주")
CITY_BUTTON_TO_KEY = {
    "서울": "서울",
    "부산": "부산",
    "제주": "제주",
}

START_MESSAGE = "시작합니다.\n오늘의 날짜와 날씨를 선택하세요."
MAIN_MENU_MESSAGE = "메인 메뉴입니다.\n오늘의 날짜와 날씨를 선택하세요."
WEATHER_MENU_MESSAGE = "오늘 날씨를 확인할 도시를 선택하세요."
PROFILE_ENTRY_MESSAGE = (
    "프로필 입력을 시작합니다.\n"
    "이름부터 순서대로 입력할게요."
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
    "- /profile : 프로필 입력 시작\n"
    "- /language : 언어 변경\n"
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
CHEAP_GATE_SUPPORT_MESSAGE = (
    "사람 상담 또는 운영자 연결 요청으로 이해했습니다.\n"
    "현재는 실시간 상담 전환이 연결되어 있지 않습니다. /help 또는 /menu 기준으로 다시 진행해주세요."
)
CHEAP_GATE_RETRY_LIMIT_MESSAGE = (
    "입력을 여러 번 이해하지 못했습니다.\n"
    "현재 단계는 자동 규칙 처리 범위를 벗어났습니다. /menu 또는 /start 로 다시 진행해주세요."
)

PROFILE_CONFIRMED_MESSAGE = "입력을 확인했습니다.\n현재 세션에 저장해두었어요."
PROFILE_EDIT_MESSAGE = "수정할 항목을 선택해주세요."
PROFILE_NOT_FOUND_MESSAGE = "아직 저장된 프로필이 없습니다.\n먼저 프로필 입력을 완료해주세요."
PROFILE_NAME_PROMPT = "이름을 입력해주세요."
PROFILE_RESIDENCE_PROMPT = "거주지를 입력해주세요."
PROFILE_CITY_PROMPT = "시/도를 입력해주세요.\n예: 서울특별시, 경기도"
PROFILE_DISTRICT_PROMPT = "구/군/시를 입력해주세요.\n예: 강남구, 분당구"
PROFILE_BIRTH_YEAR_PROMPT = "생년월일 중 출생 연도를 버튼으로 선택해주세요."
PROFILE_BIRTH_MONTH_PROMPT = "출생 월을 버튼으로 선택해주세요."
PROFILE_BIRTH_DAY_PROMPT = "출생 일을 버튼으로 선택해주세요."
PROFILE_NAME_FALLBACK = "이름을 다시 입력해주세요."
PROFILE_RESIDENCE_FALLBACK = "거주지를 다시 입력해주세요."
PROFILE_CITY_FALLBACK = "시/도를 다시 입력해주세요.\n예: 서울특별시, 경기도"
PROFILE_DISTRICT_FALLBACK = "구/군/시를 다시 입력해주세요.\n예: 강남구, 분당구"
PROFILE_BIRTH_YEAR_FALLBACK = "출생 연도 버튼을 선택해주세요."
PROFILE_BIRTH_MONTH_FALLBACK = "출생 월 버튼을 선택해주세요."
PROFILE_BIRTH_DAY_FALLBACK = "출생 일 버튼을 선택해주세요."
PROFILE_CONFIRM_FALLBACK = "[확인] 또는 [수정]을 선택해주세요."
PROFILE_EDIT_SELECT_FALLBACK = "수정할 항목 버튼을 선택해주세요."
PROFILE_REPAIR_NAME_MESSAGE = "이름을 다시 입력할게요."
PROFILE_REPAIR_RESIDENCE_MESSAGE = "거주지를 다시 입력할게요."
PROFILE_REPAIR_CITY_MESSAGE = "시/도를 다시 입력할게요."
PROFILE_REPAIR_DISTRICT_MESSAGE = "구/군/시를 다시 입력할게요."
PROFILE_REPAIR_BIRTH_MESSAGE = "생년월일을 다시 입력할게요.\n출생 연도를 선택해주세요."


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "확인했어요.\n"
        f"- 이름: {name}\n"
        f"- 거주지: {residence}\n"
        f"- 시/도: {city}\n"
        f"- 구/군/시: {district}\n"
        f"- 생년월일: {birth_date}\n"
        "\n맞으면 [확인], 수정하려면 [수정]을 눌러주세요."
    )


def format_profile_summary(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "현재 저장된 프로필입니다.\n"
        f"- 이름: {name}\n"
        f"- 거주지: {residence}\n"
        f"- 시/도: {city}\n"
        f"- 구/군/시: {district}\n"
        f"- 생년월일: {birth_date}"
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
