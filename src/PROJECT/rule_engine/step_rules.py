from PROJECT.canonical_intents import registry
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT
from PROJECT.rule_engine.contracts import IntentDecision, NormalizedInput, RuleSource
from PROJECT.rule_engine.normalizer import normalize_user_input

CONFIRM_MARKERS = ("확인", "맞아", "맞아요", "맞습니다", "네", "응", "yes", "ok", "okay")
EDIT_MARKERS = ("수정", "변경", "다시", "아니", "아니오", "틀렸", "잘못", "edit", "change", "no")


def _collapsed(text: str) -> str:
    return text.replace(" ", "")


def _profile_edit_field_intent(collapsed: str, normalized_text: str) -> str | None:
    if "생년월일" in collapsed or "생일" in collapsed or "birthdate" in collapsed or "birthday" in collapsed:
        return registry.INTENT_PROFILE_EDIT_BIRTH_DATE
    if "거주지" in collapsed or "주소" in collapsed or "residence" in collapsed or "address" in collapsed:
        return registry.INTENT_PROFILE_EDIT_RESIDENCE
    if "시도" in collapsed or "시/도" in normalized_text or "province" in collapsed or "cityprovince" in collapsed:
        return registry.INTENT_PROFILE_EDIT_CITY
    if "구군시" in collapsed or "구/군/시" in normalized_text or "district" in collapsed:
        return registry.INTENT_PROFILE_EDIT_DISTRICT
    if "이름" in collapsed or "name" in collapsed:
        return registry.INTENT_PROFILE_EDIT_NAME
    return None


def classify_step_local_intent(normalized_input: NormalizedInput, *, current_step: str | None) -> IntentDecision | None:
    if current_step is None:
        return None

    normalized_text = normalized_input.normalized_text
    collapsed = _collapsed(normalized_text)

    if current_step == STATE_PROFILE_CONFIRM:
        if any(marker in collapsed for marker in EDIT_MARKERS):
            return IntentDecision(
                canonical_intent=registry.INTENT_EDIT,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_confirm_edit_response",
            )
        if any(marker in collapsed for marker in CONFIRM_MARKERS):
            return IntentDecision(
                canonical_intent=registry.INTENT_CONFIRM,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_confirm_positive_response",
            )

    if current_step == STATE_PROFILE_EDIT_SELECT:
        field_intent = _profile_edit_field_intent(collapsed, normalized_text)
        if field_intent is not None:
            return IntentDecision(
                canonical_intent=field_intent,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_edit_select_field",
            )

    return None


def classify_step_local_intent_text(text: str, *, locale: str = "ko", current_step: str | None = None) -> IntentDecision | None:
    return classify_step_local_intent(
        normalize_user_input(text, locale=locale),
        current_step=current_step,
    )
