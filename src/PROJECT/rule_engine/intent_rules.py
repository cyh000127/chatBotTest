from PROJECT.canonical_intents import registry
from PROJECT.i18n.translator import all_button_intents
from PROJECT.rule_engine.contracts import IntentDecision, NormalizedInput, RuleSource
from PROJECT.rule_engine.normalizer import normalize_body_text, normalize_user_input

COMMAND_TO_INTENT = {
    "start": registry.INTENT_START,
    "help": registry.INTENT_HELP,
    "menu": registry.INTENT_MENU,
    "profile": registry.INTENT_PROFILE,
    "myfields": registry.INTENT_MYFIELDS_ENTRY,
    "fertilizer": registry.INTENT_FERTILIZER_INPUT_START,
    "cancel": registry.INTENT_CANCEL,
}

BUTTON_TO_INTENT = {
    normalize_body_text(label): intent
    for label, intent in all_button_intents().items()
}

REPAIR_MARKERS = ("수정", "잘못", "틀렸", "다시", "변경", "고칠", "edit", "change", "fix")
PROFILE_MARKERS = ("프로필", "정보", "내정보", "profile")
VIEW_MARKERS = ("보여", "봐", "조회", "확인", "show", "view")
FERTILIZER_MARKERS = ("비료", "fertilizer")
MYFIELDS_MARKERS = ("myfields", "내농지", "농지조회", "필드조회", "내필드")
START_MARKERS = ("입력", "등록", "기록", "시작", "할게", "할래", "start")
FERTILIZER_PRODUCT_MARKERS = ("제품", "제품명", "상품", "브랜드", "product", "name")
FERTILIZER_AMOUNT_MARKERS = ("양", "사용량", "수량", "kg", "포", "포대", "amount", "quantity")
FERTILIZER_DATE_MARKERS = ("날짜", "사용일", "언제", "date", "day")
FERTILIZER_KIND_MARKERS = ("유형", "종류", "타입", "kind", "type")
FERTILIZER_USED_MARKERS = ("사용", "썼", "안썼", "미사용", "used", "notused")


def _collapsed(text: str) -> str:
    return text.replace(" ", "")


def classify_global_intent(normalized_input: NormalizedInput, *, current_step: str | None = None) -> IntentDecision | None:
    normalized_text = normalized_input.normalized_text
    collapsed = _collapsed(normalized_text)

    if normalized_input.command:
        command_name = normalized_input.command.lstrip("/")
        canonical_intent = COMMAND_TO_INTENT.get(command_name)
        if canonical_intent is not None:
            return IntentDecision(
                canonical_intent=canonical_intent,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule=f"command:{command_name}",
            )
        if command_name == "프로필":
            canonical_intent = registry.INTENT_PROFILE_EDIT_START if "수정" in collapsed else registry.INTENT_PROFILE_VIEW
            return IntentDecision(
                canonical_intent=canonical_intent,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="command:/프로필",
            )

    button_intent = BUTTON_TO_INTENT.get(normalized_text)
    if button_intent is not None:
        return IntentDecision(
            canonical_intent=button_intent,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="button_label",
        )

    has_repair = any(marker in collapsed for marker in REPAIR_MARKERS)
    has_profile = any(marker in collapsed for marker in PROFILE_MARKERS)
    has_view = any(marker in collapsed for marker in VIEW_MARKERS)
    has_fertilizer = any(marker in collapsed for marker in FERTILIZER_MARKERS)
    has_myfields = any(marker in collapsed for marker in MYFIELDS_MARKERS)

    if has_repair:
        if has_fertilizer:
            if any(marker in collapsed for marker in FERTILIZER_AMOUNT_MARKERS):
                return IntentDecision(
                    canonical_intent=registry.INTENT_FERTILIZER_EDIT_AMOUNT,
                    current_step=current_step,
                    source=RuleSource.INTENT_RULE,
                    matched_rule="fertilizer_edit_amount",
                )
            if any(marker in collapsed for marker in FERTILIZER_DATE_MARKERS):
                return IntentDecision(
                    canonical_intent=registry.INTENT_FERTILIZER_EDIT_DATE,
                    current_step=current_step,
                    source=RuleSource.INTENT_RULE,
                    matched_rule="fertilizer_edit_date",
                )
            if any(marker in collapsed for marker in FERTILIZER_PRODUCT_MARKERS):
                return IntentDecision(
                    canonical_intent=registry.INTENT_FERTILIZER_EDIT_PRODUCT,
                    current_step=current_step,
                    source=RuleSource.INTENT_RULE,
                    matched_rule="fertilizer_edit_product",
                )
            if any(marker in collapsed for marker in FERTILIZER_KIND_MARKERS):
                return IntentDecision(
                    canonical_intent=registry.INTENT_FERTILIZER_EDIT_KIND,
                    current_step=current_step,
                    source=RuleSource.INTENT_RULE,
                    matched_rule="fertilizer_edit_kind",
                )
            if any(marker in collapsed for marker in FERTILIZER_USED_MARKERS):
                return IntentDecision(
                    canonical_intent=registry.INTENT_FERTILIZER_EDIT_USED,
                    current_step=current_step,
                    source=RuleSource.INTENT_RULE,
                    matched_rule="fertilizer_edit_used",
                )
            return IntentDecision(
                canonical_intent=registry.INTENT_FERTILIZER_EDIT_START,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="fertilizer_edit_start",
            )

        if "생년월일" in collapsed or "생일" in collapsed or "birthdate" in collapsed or "birthday" in collapsed:
            return IntentDecision(
                canonical_intent=registry.INTENT_PROFILE_EDIT_BIRTH_DATE,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_edit_birth_date",
            )
        if "거주지" in collapsed or "주소" in collapsed or "residence" in collapsed or "address" in collapsed:
            return IntentDecision(
                canonical_intent=registry.INTENT_PROFILE_EDIT_RESIDENCE,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_edit_residence",
            )
        if "시도" in collapsed or "시/도" in normalized_text or "province" in collapsed or "cityprovince" in collapsed:
            return IntentDecision(
                canonical_intent=registry.INTENT_PROFILE_EDIT_CITY,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_edit_city",
            )
        if "구군시" in collapsed or "구/군/시" in normalized_text or "district" in collapsed:
            return IntentDecision(
                canonical_intent=registry.INTENT_PROFILE_EDIT_DISTRICT,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_edit_district",
            )
        if "이름" in collapsed or "name" in collapsed:
            return IntentDecision(
                canonical_intent=registry.INTENT_PROFILE_EDIT_NAME,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_edit_name",
            )
        if has_profile:
            return IntentDecision(
                canonical_intent=registry.INTENT_PROFILE_EDIT_START,
                current_step=current_step,
                source=RuleSource.INTENT_RULE,
                matched_rule="profile_edit_start",
            )

    if collapsed in {"프로필", "내프로필", "profile"}:
        return IntentDecision(
            canonical_intent=registry.INTENT_PROFILE_VIEW,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="profile_view_exact",
        )

    if has_profile and has_view:
        return IntentDecision(
            canonical_intent=registry.INTENT_PROFILE_VIEW,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="profile_view_phrase",
        )

    if collapsed in {"myfields", "내농지", "농지조회", "내필드"}:
        return IntentDecision(
            canonical_intent=registry.INTENT_MYFIELDS_ENTRY,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="myfields_exact",
        )

    has_start = any(marker in collapsed for marker in START_MARKERS)
    if has_myfields and (has_view or "조회" in collapsed):
        return IntentDecision(
            canonical_intent=registry.INTENT_MYFIELDS_ENTRY,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="myfields_view_phrase",
        )
    if has_fertilizer and has_start:
        return IntentDecision(
            canonical_intent=registry.INTENT_FERTILIZER_INPUT_START,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="fertilizer_start_phrase",
        )

    return None


def classify_global_intent_text(text: str, *, locale: str = "ko", current_step: str | None = None) -> IntentDecision | None:
    return classify_global_intent(normalize_user_input(text, locale=locale), current_step=current_step)
