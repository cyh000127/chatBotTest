from PROJECT.canonical_intents import registry
from PROJECT.i18n.translator import all_button_intents
from PROJECT.rule_engine.contracts import IntentDecision, NormalizedInput, RuleSource
from PROJECT.rule_engine.normalizer import normalize_body_text, normalize_user_input

COMMAND_TO_INTENT = {
    "start": registry.INTENT_START,
    "help": registry.INTENT_HELP,
    "menu": registry.INTENT_MENU,
    "myfields": registry.INTENT_FIELD_LIST,
    "fertilizer": registry.INTENT_AGRI_INPUT_START,
    "yield": registry.INTENT_YIELD_INPUT_START,
    "resolve": registry.INTENT_INPUT_RESOLVE_START,
    "support": registry.INTENT_SUPPORT_ESCALATE,
    "cancel": registry.INTENT_CANCEL,
}

BUTTON_TO_INTENT = {
    normalize_body_text(label): intent
    for label, intent in all_button_intents().items()
}

REPAIR_MARKERS = ("수정", "잘못", "틀렸", "다시", "변경", "고칠", "edit", "change", "fix")
FERTILIZER_MARKERS = ("비료", "fertilizer")
YIELD_MARKERS = ("yield", "수확", "수확량", "harvest")
MYFIELDS_MARKERS = ("myfields", "내농지", "농지조회", "필드조회", "내필드")
INPUT_RESOLVE_MARKERS = ("inputresolve", "resolve", "입력해석", "값해석", "값확정", "원문확정")
SUPPORT_MARKERS = ("support", "지원", "상담", "지원안내")
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

    button_intent = BUTTON_TO_INTENT.get(normalized_text)
    if button_intent is not None:
        return IntentDecision(
            canonical_intent=button_intent,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="button_label",
        )

    has_repair = any(marker in collapsed for marker in REPAIR_MARKERS)
    has_fertilizer = any(marker in collapsed for marker in FERTILIZER_MARKERS)
    has_yield = any(marker in collapsed for marker in YIELD_MARKERS)
    has_myfields = any(marker in collapsed for marker in MYFIELDS_MARKERS)
    has_input_resolve = any(marker in collapsed for marker in INPUT_RESOLVE_MARKERS)
    has_support = any(marker in collapsed for marker in SUPPORT_MARKERS)

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

    if collapsed in {"myfields", "내농지", "농지조회", "내필드"}:
        return IntentDecision(
            canonical_intent=registry.INTENT_FIELD_LIST,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="myfields_exact",
        )

    if collapsed in {"inputresolve", "resolve", "입력해석", "값확정"}:
        return IntentDecision(
            canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="input_resolve_exact",
        )

    if collapsed in {"support", "지원", "지원안내"}:
        return IntentDecision(
            canonical_intent=registry.INTENT_SUPPORT_ESCALATE,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="support_exact",
        )

    has_start = any(marker in collapsed for marker in START_MARKERS)
    if has_myfields and ("조회" in collapsed or "봐" in collapsed or "show" in collapsed or "view" in collapsed):
        return IntentDecision(
            canonical_intent=registry.INTENT_FIELD_LIST,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="myfields_view_phrase",
        )
    if has_input_resolve and (has_start or "열" in collapsed or "확정" in collapsed):
        return IntentDecision(
            canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="input_resolve_start_phrase",
        )
    if has_support and ("안내" in collapsed or "연결" in collapsed or "도움" in collapsed):
        return IntentDecision(
            canonical_intent=registry.INTENT_SUPPORT_ESCALATE,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="support_phrase",
        )
    if has_yield and has_start:
        return IntentDecision(
            canonical_intent=registry.INTENT_YIELD_INPUT_START,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="yield_start_phrase",
        )
    if has_fertilizer and has_start:
        return IntentDecision(
            canonical_intent=registry.INTENT_AGRI_INPUT_START,
            current_step=current_step,
            source=RuleSource.INTENT_RULE,
            matched_rule="fertilizer_start_phrase",
        )

    return None


def classify_global_intent_text(text: str, *, locale: str = "ko", current_step: str | None = None) -> IntentDecision | None:
    return classify_global_intent(normalize_user_input(text, locale=locale), current_step=current_step)
