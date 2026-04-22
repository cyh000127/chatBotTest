from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM
from PROJECT.conversations.sample_menu.states import STATE_CANCELLED, STATE_MAIN_MENU
from PROJECT.rule_engine import MAX_RECOVERY_ATTEMPTS, ValidationClassification, classify_cheap_gate


def test_cheap_gate_marks_support_request_for_handoff():
    result = classify_cheap_gate("상담원 연결해주세요", current_step=STATE_MAIN_MENU)

    assert result.classification == ValidationClassification.NEEDS_HANDOFF
    assert result.reason == "explicit_support_request"


def test_cheap_gate_marks_retry_limit_for_handoff():
    result = classify_cheap_gate(
        "뭔가 안돼요",
        current_step=STATE_MAIN_MENU,
        recovery_attempt_count=MAX_RECOVERY_ATTEMPTS,
    )

    assert result.classification == ValidationClassification.NEEDS_HANDOFF
    assert result.reason == "recovery_retry_limit_exceeded"


def test_cheap_gate_reasks_for_structured_step_mismatch():
    result = classify_cheap_gate("아무거나 입력", current_step=STATE_CANCELLED)

    assert result.classification == ValidationClassification.REASK
    assert result.reason == "structured_step_mismatch"


def test_cheap_gate_reasks_for_empty_structured_input():
    result = classify_cheap_gate("   ", current_step=STATE_PROFILE_CONFIRM)

    assert result.classification == ValidationClassification.REASK
    assert result.reason == "empty_input"


def test_cheap_gate_leaves_general_unknown_text_recoverable():
    result = classify_cheap_gate("이건 아직 규칙에 없는 요청이야", current_step=STATE_MAIN_MENU)

    assert result.classification == ValidationClassification.UNRESOLVED_RECOVERABLE
    assert result.reason == "unresolved_text"
