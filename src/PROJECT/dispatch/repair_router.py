from dataclasses import dataclass

from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_EDIT_SELECT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)

REPAIR_NAME = "repair_name"
REPAIR_RESIDENCE = "repair_residence"
REPAIR_CITY = "repair_city"
REPAIR_DISTRICT = "repair_district"
REPAIR_BIRTH_DATE = "repair_birth_date"
REPAIR_PROFILE = "repair_profile"


@dataclass(frozen=True)
class RepairDecision:
    target: str
    target_state: str


def detect_repair_intent(text: str) -> RepairDecision | None:
    normalized = text.strip().lstrip("/").replace(" ", "")
    if not normalized:
        return None

    repair_markers = ("수정", "잘못", "틀렸", "다시", "변경", "고칠")
    if not any(marker in normalized for marker in repair_markers):
        return None

    if "생년월일" in normalized or "생일" in normalized:
        return RepairDecision(REPAIR_BIRTH_DATE, STATE_PROFILE_BIRTH_YEAR)
    if "거주지" in normalized or "주소" in normalized:
        return RepairDecision(REPAIR_RESIDENCE, STATE_PROFILE_RESIDENCE)
    if "시도" in normalized or "시/도" in text or "시도명" in normalized:
        return RepairDecision(REPAIR_CITY, STATE_PROFILE_CITY)
    if "구군시" in normalized or "구/군/시" in text or "구군" in normalized:
        return RepairDecision(REPAIR_DISTRICT, STATE_PROFILE_DISTRICT)
    if "이름" in normalized:
        return RepairDecision(REPAIR_NAME, STATE_PROFILE_NAME)
    if "프로필" in normalized or "정보" in normalized or "profile" in normalized.lower():
        return RepairDecision(REPAIR_PROFILE, STATE_PROFILE_EDIT_SELECT)
    return None


def detect_profile_view_intent(text: str) -> bool:
    normalized = text.strip().lstrip("/").replace(" ", "").lower()
    if not normalized:
        return False
    if normalized in {"profile", "프로필", "내프로필"}:
        return True
    profile_markers = ("프로필", "정보", "profile")
    view_markers = ("보여", "봐", "조회", "확인", "show", "view")
    return any(marker in normalized for marker in profile_markers) and any(marker in normalized for marker in view_markers)
