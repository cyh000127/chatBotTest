from dataclasses import dataclass

from PROJECT.canonical_intents import registry
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)
from PROJECT.rule_engine.correction_extractor import (
    extract_fertilizer_correction_pattern,
)
from PROJECT.rule_engine import classify_global_intent_text

REPAIR_FERTILIZER = "repair_fertilizer"
REPAIR_FERTILIZER_USED = "repair_fertilizer_used"
REPAIR_FERTILIZER_KIND = "repair_fertilizer_kind"
REPAIR_FERTILIZER_PRODUCT = "repair_fertilizer_product"
REPAIR_FERTILIZER_AMOUNT = "repair_fertilizer_amount"
REPAIR_FERTILIZER_DATE = "repair_fertilizer_date"


@dataclass(frozen=True)
class RepairDecision:
    target: str
    target_state: str


REPAIR_MARKERS = ("수정", "잘못", "틀렸", "다시", "변경", "고칠", "edit", "change", "fix")
FERTILIZER_USED_MARKERS = ("사용", "썼", "안썼", "미사용", "used", "notused")
FERTILIZER_KIND_MARKERS = ("유형", "종류", "타입", "kind", "type")
FERTILIZER_PRODUCT_MARKERS = ("제품", "제품명", "상품", "브랜드", "product", "name")
FERTILIZER_AMOUNT_MARKERS = ("양", "사용량", "수량", "kg", "포", "포대", "amount", "quantity")
FERTILIZER_DATE_MARKERS = ("날짜", "사용일", "언제", "date", "day")

FERTILIZER_CONTEXT_STATES = {STATE_FERTILIZER_CONFIRM}


def _collapsed(text: str) -> str:
    return text.replace(" ", "").lower()


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _detect_fertilizer_contextual_repair(text: str) -> RepairDecision | None:
    pattern_decision = extract_fertilizer_correction_pattern(text)
    if pattern_decision is not None:
        return RepairDecision(REPAIR_FERTILIZER, pattern_decision.target_state)
    if _has_any(text, FERTILIZER_AMOUNT_MARKERS):
        return RepairDecision(REPAIR_FERTILIZER_AMOUNT, STATE_FERTILIZER_AMOUNT)
    if _has_any(text, FERTILIZER_DATE_MARKERS):
        return RepairDecision(REPAIR_FERTILIZER_DATE, STATE_FERTILIZER_DATE)
    if _has_any(text, FERTILIZER_PRODUCT_MARKERS):
        return RepairDecision(REPAIR_FERTILIZER_PRODUCT, STATE_FERTILIZER_PRODUCT)
    if _has_any(text, FERTILIZER_KIND_MARKERS):
        return RepairDecision(REPAIR_FERTILIZER_KIND, STATE_FERTILIZER_KIND)
    if _has_any(text, FERTILIZER_USED_MARKERS):
        return RepairDecision(REPAIR_FERTILIZER_USED, STATE_FERTILIZER_USED)
    return None


def detect_repair_intent(
    text: str,
    *,
    current_state: str | None = None,
    domain_hint: str | None = None,
) -> RepairDecision | None:
    decision = classify_global_intent_text(text, locale="ko", current_step=current_state)
    if decision is None:
        collapsed = _collapsed(text)
        if not _has_any(collapsed, REPAIR_MARKERS):
            return None

        if domain_hint == "fertilizer" and current_state in FERTILIZER_CONTEXT_STATES:
            return _detect_fertilizer_contextual_repair(collapsed)
        return None

    mapping = {
        registry.INTENT_FERTILIZER_EDIT_START: RepairDecision(REPAIR_FERTILIZER, STATE_FERTILIZER_CONFIRM),
        registry.INTENT_FERTILIZER_EDIT_USED: RepairDecision(REPAIR_FERTILIZER_USED, STATE_FERTILIZER_USED),
        registry.INTENT_FERTILIZER_EDIT_KIND: RepairDecision(REPAIR_FERTILIZER_KIND, STATE_FERTILIZER_KIND),
        registry.INTENT_FERTILIZER_EDIT_PRODUCT: RepairDecision(REPAIR_FERTILIZER_PRODUCT, STATE_FERTILIZER_PRODUCT),
        registry.INTENT_FERTILIZER_EDIT_AMOUNT: RepairDecision(REPAIR_FERTILIZER_AMOUNT, STATE_FERTILIZER_AMOUNT),
        registry.INTENT_FERTILIZER_EDIT_DATE: RepairDecision(REPAIR_FERTILIZER_DATE, STATE_FERTILIZER_DATE),
    }
    repair = mapping.get(decision.canonical_intent)
    if repair is not None:
        return repair
    return None
