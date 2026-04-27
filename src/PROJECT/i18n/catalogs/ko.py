from datetime import datetime

# Copy rules:
# - 짧게 쓴다.
# - 어려운 말보다 쉬운 말을 쓴다.
# - 안내문에서는 "뒤로가기"와 "처음부터"를 먼저 보여준다.

BUTTON_TODAY_DATE = "오늘 날짜"
BUTTON_TODAY_WEATHER = "오늘 날씨"
BUTTON_FERTILIZER = "비료 입력"
BUTTON_YIELD = "수확량 입력"
BUTTON_MYFIELDS = "자기 조회"
BUTTON_INPUT_RESOLVE = "입력 해석"
BUTTON_SUPPORT = "지원 안내"
BUTTON_HELP = "도움말"
BUTTON_BACK = "뒤로가기"
BUTTON_CANCEL = "취소"
BUTTON_RESTART = "처음부터"
BUTTON_CONFIRM = "확인"
BUTTON_EDIT = "수정"
BUTTON_EDIT_START = "수정 시작"
BUTTON_KEEP_CURRENT = "그대로 둘래요"
BUTTON_APPLY_SUGGESTED_VALUE = "이 값으로 진행"
BUTTON_ENTER_VALUE_DIRECTLY = "직접 다시 입력"
BUTTON_YES = "예"
BUTTON_NO = "아니오"
BUTTON_EDIT_NAME = "이름"
BUTTON_EDIT_PHONE = "전화번호"
BUTTON_EDIT_RESIDENCE = "거주지"
BUTTON_EDIT_CITY = "시/도"
BUTTON_EDIT_DISTRICT = "구/군/시"
BUTTON_EDIT_BIRTH_DATE = "생년월일"
BUTTON_FERTILIZER_EDIT_USED = "비료 사용 여부"
BUTTON_FERTILIZER_EDIT_KIND = "비료 유형"
BUTTON_FERTILIZER_EDIT_PRODUCT = "제품명"
BUTTON_FERTILIZER_EDIT_AMOUNT = "사용량"
BUTTON_FERTILIZER_EDIT_DATE = "사용일"
BUTTON_YIELD_EDIT_READY = "수확 준비 여부"
BUTTON_YIELD_EDIT_FIELD = "농지"
BUTTON_YIELD_EDIT_AMOUNT = "수확량"
BUTTON_YIELD_EDIT_DATE = "수확일"
BUTTON_PREV_YEARS = "이전 12년"
BUTTON_NEXT_YEARS = "다음 12년"
BUTTON_FERTILIZER_KIND_COMPOUND = "복합비료"
BUTTON_FERTILIZER_KIND_UREA = "요소비료"
BUTTON_FERTILIZER_KIND_COMPOST = "퇴비"
BUTTON_FERTILIZER_KIND_LIQUID = "액비"
LANGUAGE_NAME = "한국어"
LANGUAGE_MENU_MESSAGE = "언어를 선택하세요."
LANGUAGE_CHANGED_MESSAGE = "언어가 한국어로 변경되었습니다."
AUTH_START_PROMPT = "아이디를 입력하세요.\n/start"
AUTH_REQUIRED_MESSAGE = "인증이 필요합니다.\n/start 입력 후 아이디를 입력하세요."
AUTH_INVALID_MESSAGE = "아이디가 맞지 않습니다.\n다시 입력하세요."
AUTH_RETRY_LIMIT_MESSAGE = "인증에 두 번 실패했습니다.\n/start 입력 후 처음부터 진행하세요."
AUTH_WELCOME_MESSAGE = "어서오세요 {user_name}님!"
AUTH_ALREADY_LOGGED_IN_MESSAGE = "어서오세요 {user_name}님!"
START_REQUIRED_MESSAGE = "먼저 /start로 시작하세요."
ONBOARDING_INVITE_REQUIRED_MESSAGE = "초대 코드가 필요합니다.\n초대 코드가 있다면 /start <초대코드>로 시작하세요."
ONBOARDING_INVALID_INVITE_MESSAGE = "초대 코드를 확인하지 못했습니다.\n코드를 다시 확인한 뒤 /start <초대코드>로 입력하세요."
ONBOARDING_IDENTITY_REQUIRED_MESSAGE = "Telegram 사용자 정보를 확인하지 못했습니다.\n잠시 뒤 다시 시도하세요."
ONBOARDING_STARTED_MESSAGE = "초대 코드를 확인했습니다.\n언어를 선택하면 온보딩을 이어갑니다."
ONBOARDING_ACCESS_REQUIRED_MESSAGE = "서비스 이용 전 온보딩과 관리자 승인이 필요합니다.\n초대 코드가 있다면 /start <초대코드>로 시작하세요."
ONBOARDING_PENDING_APPROVAL_MESSAGE = "온보딩이 아직 완료되지 않았거나 관리자 승인 대기 중입니다.\n승인 후 서비스를 이용할 수 있습니다."
ONBOARDING_NAME_PROMPT = "이름을 입력하세요."
ONBOARDING_NAME_FALLBACK = "이름을 다시 입력하세요.\n예: 홍길동"
ONBOARDING_PHONE_PROMPT = "전화번호를 국가번호와 함께 입력하세요.\n예: +855 12 345 678, +880 17 1234 5678"
ONBOARDING_PHONE_FALLBACK = "전화번호를 다시 입력하세요.\n현재는 +855 또는 +880 국가번호만 사용할 수 있습니다."
ONBOARDING_CONFIRM_MESSAGE = (
    "온보딩 입력 내용을 확인하세요.\n"
    "- 이름: {name}\n"
    "- 전화번호: {phone}\n"
    "- 언어: {language}\n\n"
    "맞으면 [확인], 수정하려면 항목을 선택하세요."
)
ONBOARDING_CONFIRM_FALLBACK = "[확인]을 누르거나 수정할 항목을 선택하세요."
ONBOARDING_PENDING_APPROVAL_SUBMITTED_MESSAGE = "온보딩 신청을 승인 대기로 제출했습니다.\n관리자 승인 후 서비스를 이용할 수 있습니다."

CITY_LABELS = ("서울", "부산", "제주")
CITY_BUTTON_TO_KEY = {
    "서울": "서울",
    "부산": "부산",
    "제주": "제주",
}

START_MESSAGE = "시작되었습니다.\n작업을 선택하세요."
MAIN_MENU_MESSAGE = "메인 메뉴입니다.\n작업을 선택하세요."
WEATHER_MENU_MESSAGE = "날씨를 볼 도시를 선택하세요."
PROFILE_ENTRY_MESSAGE = (
    "프로필 입력을 시작합니다.\n"
    "이름부터 입력하세요."
)
CANCEL_MESSAGE = "현재 흐름이 종료되었습니다.\n'처음부터' 또는 /start 로 다시 시작할 수 있습니다."
BACK_LIMIT_MESSAGE = "이전 단계가 없습니다.\n메인 메뉴에서 다시 선택하세요."
BACK_TO_MAIN_MESSAGE = "이전 단계로 돌아왔습니다.\n다시 선택하세요."
BACK_TO_WEATHER_MESSAGE = "날씨 선택으로 돌아왔습니다.\n도시를 다시 선택하세요."
BACK_GENERIC_MESSAGE = "이전 단계로 돌아왔습니다."
WEATHER_ERROR_MESSAGE = "날씨 정보를 가져오지 못했습니다.\n잠시 뒤 다시 시도하세요."
UNKNOWN_COMMAND_MESSAGE = "지원하지 않는 명령어입니다.\n아래 관련 항목을 선택하거나 /help 를 입력하세요."
MYFIELDS_ENTRY_MESSAGE = "자기 조회 화면입니다.\n현재는 안내와 다시 들어오기만 연결되어 있습니다.\n아래 항목에서 다른 작업을 선택하거나 /start 로 다시 시작하세요."
INPUT_RESOLVE_ENTRY_MESSAGE = "입력 해석 화면입니다.\n현재는 정할 값을 먼저 모으는 단계입니다.\n후보 만들기와 운영 검토 연결은 별도 단계에서 진행됩니다."
SUPPORT_ESCALATION_MESSAGE = "지원 요청이 접수되었습니다.\n새 채팅방은 만들지 않습니다. 이 대화창에서 후속 안내를 받을 수 있습니다.\n필요하면 /help, /menu, /start 로 이동하세요."
SUPPORT_HANDOFF_MESSAGE_RECORDED = "추가 내용이 지원 이관 이력에 저장되었습니다.\n새 채팅방은 만들지 않습니다. 이 대화창에서 후속 안내를 받을 수 있습니다.\n처음부터 다시 진행하려면 /start 를 입력하세요."
SUPPORT_HANDOFF_CLOSED_MESSAGE = "지원 이관이 종료되었습니다.\n필요하면 이 대화창에서 다시 도움을 요청할 수 있습니다."

HELP_MESSAGE = (
    "사용할 수 있는 명령어입니다.\n"
    "- /start : 처음으로 가기\n"
    "- /help : 도움말 보기\n"
    "- /menu : 메인 메뉴 열기\n"
    "- /myfields : 자기 조회 열기\n"
    "- /fertilizer : 비료 입력 시작\n"
    "- /yield : 수확량 입력 시작\n"
    "- /resolve : 입력 해석 열기\n"
    "- /support : 지원 안내 열기\n"
    "- /language : 언어 바꾸기\n"
    "- 뒤로가기 : 이전 단계로 가기\n"
    "- 처음부터 : 처음부터 다시 시작"
)

FALLBACK_MESSAGES = {
    "default": "입력을 처리하지 못했습니다.\n아래 항목에서 하나를 선택하세요.",
    "weather": "입력을 처리하지 못했습니다.\n도시를 선택하거나 뒤로가기를 누르세요.",
    "cancelled": "현재 흐름은 종료된 상태입니다.\n아래 항목에서 다시 시작할 작업을 선택하세요.",
    "fertilizer_input": "비료 입력을 처리하지 못했습니다.\n아래 항목에서 이어서 입력할 내용을 선택하세요.",
    "fertilizer_confirm": "비료 확인 단계입니다.\n확인하거나 수정할 항목을 선택하세요.",
    "yield_input": "수확량 입력을 처리하지 못했습니다.\n아래 항목에서 이어서 입력할 내용을 선택하세요.",
    "yield_confirm": "수확량 확인 단계입니다.\n확인하거나 뒤로가기를 누르세요.",
}
RECOVERY_GUIDANCE_SOFT = "이 단계에 필요한 입력입니다."
RECOVERY_GUIDANCE_GUIDED = "계속 진행하려면 아래 안내를 따르세요."
RECOVERY_GUIDANCE_ESCALATION_READY = "계속 진행하기 어렵다면 아래 항목으로 이동할 수 있습니다."
RECOVERY_MULTI_SLOT_CANDIDATE_HINT = "여러 후보 값이 확인되었습니다.\n아래 초안을 확인한 뒤 진행하세요."
RECOVERY_MULTI_SLOT_APPLIED_MESSAGE = "후보 값이 초안에 반영되었습니다. 내용을 확인하세요."
CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE = (
    "지원 요청으로 확인되었습니다.\n"
    "지원 이관 이력에 저장되며, 후속 안내는 이 대화창에서 이어집니다.\n"
    "아래 항목을 선택하거나 /help 를 입력하세요."
)
CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE = (
    "운영 후속 확인이 필요한 요청입니다.\n"
    "확인 항목으로 저장되며, 필요한 안내는 이 대화창에서 이어집니다.\n"
    "아래 항목을 선택해 다시 진행하세요."
)
CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE = (
    "입력을 여러 번 확인했지만 자동 처리할 수 없습니다.\n"
    "수동 해결이 필요한 상태입니다. 운영 검토로 전달됩니다.\n"
    "아래 항목을 선택하거나 /menu 또는 /start 로 다시 시작하세요."
)

PROFILE_CONFIRMED_MESSAGE = "입력이 저장되었습니다.\n현재 세션에 보관됩니다."
PROFILE_EDIT_MESSAGE = "수정할 항목을 선택하세요."
PROFILE_EDIT_SELECTION_CONFIRMATION_MESSAGE = "프로필 항목을 다시 선택합니다.\n[{edit_button}]을 누르면 항목 선택 화면이 열립니다."
PROFILE_NOT_FOUND_MESSAGE = "저장된 프로필이 없습니다.\n먼저 프로필 입력을 완료하세요."
PROFILE_NAME_PROMPT = "이름을 입력하세요."
PROFILE_RESIDENCE_PROMPT = "거주지를 입력하세요."
PROFILE_CITY_PROMPT = "시/도를 입력하세요.\n예: 서울특별시, 경기도"
PROFILE_DISTRICT_PROMPT = "구/군/시를 입력하세요.\n예: 강남구, 분당구"
PROFILE_BIRTH_YEAR_PROMPT = "출생 연도를 선택하세요."
PROFILE_BIRTH_MONTH_PROMPT = "출생 월을 선택하세요."
PROFILE_BIRTH_DAY_PROMPT = "출생 일을 선택하세요."
PROFILE_NAME_FALLBACK = "이름을 다시 입력하세요."
PROFILE_RESIDENCE_FALLBACK = "거주지를 다시 입력하세요."
PROFILE_CITY_FALLBACK = "시/도를 다시 입력하세요.\n예: 서울특별시, 경기도"
PROFILE_DISTRICT_FALLBACK = "구/군/시를 다시 입력하세요.\n예: 강남구, 분당구"
PROFILE_BIRTH_YEAR_FALLBACK = "출생 연도 버튼을 선택하세요."
PROFILE_BIRTH_MONTH_FALLBACK = "출생 월 버튼을 선택하세요."
PROFILE_BIRTH_DAY_FALLBACK = "출생 일 버튼을 선택하세요."
PROFILE_CONFIRM_FALLBACK = "[확인] 또는 [수정]을 선택하세요."
PROFILE_EDIT_SELECT_FALLBACK = "수정할 항목 버튼을 선택하세요."
PROFILE_REPAIR_NAME_MESSAGE = "이름을 다시 입력하세요."
PROFILE_REPAIR_RESIDENCE_MESSAGE = "거주지를 다시 입력하세요."
PROFILE_REPAIR_CITY_MESSAGE = "시/도를 다시 입력하세요."
PROFILE_REPAIR_DISTRICT_MESSAGE = "구/군/시를 다시 입력하세요."
PROFILE_REPAIR_BIRTH_MESSAGE = "생년월일을 다시 입력하세요.\n출생 연도부터 선택하세요."
PROFILE_DIRECT_UPDATE_MESSAGE = "변경 내용이 반영되었습니다. 확인 후 [확인]을 누르세요."
LLM_REPAIR_CANDIDATE_HINT = "\"{candidate_value}\"로 바꾸는 요청으로 확인되었습니다.\n맞으면 수정 시작을 누르세요."
LLM_REPAIR_UNSUPPORTED_MESSAGE = "수정할 항목을 확인하지 못했습니다.\n아래 항목에서 직접 선택하세요."
LLM_REPAIR_LOW_CONFIDENCE_MESSAGE = "수정할 항목을 확정하지 못했습니다.\n아래 항목에서 직접 선택하세요."
LLM_REPAIR_HUMAN_REVIEW_MESSAGE = (
    "이 요청은 한 항목으로 좁히기 어렵습니다.\n"
    "운영 검토가 필요할 수 있습니다. 아래 항목에서 직접 선택하세요."
)
LLM_REPAIR_RUNTIME_FAILURE_MESSAGE = (
    "자동 해석을 안정적으로 처리할 수 없습니다.\n"
    "아래 항목에서 직접 선택해 진행하세요."
)

FERTILIZER_KIND_LABELS = {
    "compound": "복합비료",
    "urea": "요소비료",
    "compost": "퇴비",
    "liquid": "액비",
}
FERTILIZER_USED_LABEL_YES = "사용함"
FERTILIZER_USED_LABEL_NO = "사용 안 함"
FERTILIZER_USED_PROMPT = "이번 작업에서 비료를 사용했나요?"
FERTILIZER_KIND_PROMPT = "비료 유형을 선택하세요."
FERTILIZER_PRODUCT_PROMPT = "제품명을 입력하세요.\n예: 한아름 복합비료"
FERTILIZER_AMOUNT_PROMPT = "사용량을 입력하세요.\n예: 20kg, 한 포"
FERTILIZER_DATE_PROMPT = "사용일을 입력하세요.\n예: 2026-04-21, 오늘, 어제"
FERTILIZER_CONFIRM_PROMPT = "비료 입력 내용을 확인하세요."
FERTILIZER_USED_FALLBACK = "예 또는 아니오를 선택하세요."
FERTILIZER_KIND_FALLBACK = "비료 유형 버튼을 선택하세요."
FERTILIZER_PRODUCT_FALLBACK = "제품명을 다시 입력하세요."
FERTILIZER_AMOUNT_FALLBACK = "사용량을 다시 입력하세요.\n예: 20kg, 한 포"
FERTILIZER_DATE_FALLBACK = "사용일을 다시 입력하세요.\n예: 2026-04-21, 오늘, 어제"
FERTILIZER_CONFIRM_FALLBACK = "[확인]을 누르거나 뒤로가기로 수정하세요."
FERTILIZER_CONFIRMED_MESSAGE = "비료 입력이 저장되었습니다.\n현재 세션에 보관됩니다."
FERTILIZER_EDIT_MESSAGE = "수정할 비료 항목을 선택하세요."
FERTILIZER_EDIT_SELECTION_CONFIRMATION_MESSAGE = "비료 입력 항목을 다시 선택합니다.\n[{edit_button}]을 누르면 항목 선택 화면이 열립니다."
FERTILIZER_NOT_FOUND_MESSAGE = "저장된 비료 입력이 없습니다.\n먼저 비료 입력을 완료하세요."
FERTILIZER_REPAIR_USED_MESSAGE = "비료 사용 여부를 다시 입력하세요."
FERTILIZER_REPAIR_KIND_MESSAGE = "비료 유형을 다시 입력하세요."
FERTILIZER_REPAIR_PRODUCT_MESSAGE = "비료 제품명을 다시 입력하세요."
FERTILIZER_REPAIR_AMOUNT_MESSAGE = "비료 사용량을 다시 입력하세요."
FERTILIZER_REPAIR_DATE_MESSAGE = "비료 사용일을 다시 입력하세요."
FERTILIZER_DIRECT_UPDATE_MESSAGE = "변경 내용이 반영되었습니다. 확인 후 [확인]을 누르세요."
YIELD_READY_PROMPT = "수확 준비가 되었나요?"
YIELD_FIELD_PROMPT = "수확한 농지를 선택하거나 입력하세요."
YIELD_AMOUNT_PROMPT = "수확량을 입력하세요.\n예: 320kg"
YIELD_DATE_PROMPT = "수확일을 입력하세요.\n예: 2026-04-21, 오늘, 어제"
YIELD_CONFIRM_PROMPT = "수확 입력 내용을 확인하세요."
YIELD_READY_FALLBACK = "예 또는 아니오를 선택하세요."
YIELD_FIELD_FALLBACK = "수확한 농지를 다시 입력하세요."
YIELD_AMOUNT_FALLBACK = "수확량을 다시 입력하세요.\n예: 320kg"
YIELD_DATE_FALLBACK = "수확일을 다시 입력하세요.\n예: 2026-04-21, 오늘, 어제"
YIELD_CONFIRM_FALLBACK = "[확인]을 누르거나 뒤로가기로 수정하세요."
YIELD_EDIT_MESSAGE = "수정할 수확량 항목을 선택하세요."
YIELD_EDIT_SELECT_FALLBACK = "수정할 항목을 선택하세요. [수정 시작], 뒤로가기, 처음부터 중 하나를 누를 수 있습니다."
YIELD_CONFIRMED_MESSAGE = "수확량 입력이 저장되었습니다.\n현재 세션에 보관됩니다."
INPUT_RESOLVE_TARGET_PROMPT = "정할 값을 선택하세요."
INPUT_RESOLVE_METHOD_PROMPT = "입력 방식을 선택하세요.\n글로 쓰기, OCR 사진, 다시 시도 중 하나로 진행합니다."
INPUT_RESOLVE_RAW_INPUT_PROMPT = "정할 원문을 입력하거나 제출하세요."
INPUT_RESOLVE_CANDIDATES_PROMPT = "후보를 확인하고 1~3번 중 선택하거나 다시 입력하세요."
INPUT_RESOLVE_DECISION_PROMPT = "후보 확정, 다시 시도, 운영 검토 중 하나를 선택하세요."


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "입력 내용을 확인하세요.\n"
        f"- 이름: {name}\n"
        f"- 거주지: {residence}\n"
        f"- 시/도: {city}\n"
        f"- 구/군/시: {district}\n"
        f"- 생년월일: {birth_date}\n"
        "\n맞으면 [확인], 바꾸려면 [수정]을 누르세요."
    )


def format_repair_confirmation(*, field_label: str, edit_button: str) -> str:
    return (
        f"{field_label} 항목을 수정합니다.\n"
        f"[{edit_button}]을 누르면 해당 항목을 다시 입력합니다."
    )


def format_change_preview(*, field_label: str, before_value: str, after_value: str) -> str:
    return (
        f"{field_label} 변경 내용을 확인하세요.\n"
        f"- 이전: {before_value}\n"
        f"- 변경: {after_value}"
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


def format_fertilizer_confirmation(
    *,
    used: bool | None,
    kind_label: str,
    product_name: str,
    amount_text: str,
    applied_date: str,
) -> str:
    if used is False:
        return (
            "비료 입력 내용을 확인하세요.\n"
            "- 비료 사용 여부: 사용 안 함\n\n"
            "맞으면 [확인]을 누르세요."
        )
    return (
        "비료 입력 내용을 확인하세요.\n"
        f"- 비료 사용 여부: {'사용함' if used else '-'}\n"
        f"- 비료 유형: {kind_label}\n"
        f"- 제품명: {product_name}\n"
        f"- 사용량: {amount_text}\n"
        f"- 사용일: {applied_date}\n\n"
        "맞으면 [확인]을 누르세요."
    )


def format_fertilizer_summary(
    *,
    used: bool | None,
    kind_label: str,
    product_name: str,
    amount_text: str,
    applied_date: str,
) -> str:
    if used is False:
        return (
            "현재 저장된 비료 입력입니다.\n"
            "- 비료 사용 여부: 사용 안 함"
        )
    return (
        "현재 저장된 비료 입력입니다.\n"
        f"- 비료 사용 여부: {'사용함' if used else '-'}\n"
        f"- 비료 유형: {kind_label}\n"
        f"- 제품명: {product_name}\n"
        f"- 사용량: {amount_text}\n"
        f"- 사용일: {applied_date}"
    )


def format_yield_confirmation(
    *,
    ready: bool | None,
    field_name: str,
    amount_text: str,
    harvest_date: str,
) -> str:
    return (
        "수확 입력 내용을 확인하세요.\n"
        f"- 수확 준비 여부: {'준비됨' if ready else '미준비' if ready is False else '-'}\n"
        f"- 농지: {field_name}\n"
        f"- 수확량: {amount_text}\n"
        f"- 수확일: {harvest_date}\n\n"
        "맞으면 [확인]을 누르세요."
    )


def format_support_admin_reply(*, admin_message: str) -> str:
    return (
        "운영자 답변입니다.\n"
        f"{admin_message}\n\n"
        "추가로 전달할 내용이 있으면 이 대화창에 이어서 입력하세요."
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
