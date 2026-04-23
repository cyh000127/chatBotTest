from PROJECT.conversations.sample_menu import service
from PROJECT.i18n.translator import get_catalog
from PROJECT.rule_engine import RuleSource, ValidationClassification, ValidationResult


def test_cheap_gate_text_distinguishes_support_escalation_message():
    catalog = get_catalog("ko")
    result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="explicit_support_request",
    )

    text = service.cheap_gate_text(result, "default", catalog)

    assert "지원 이관" in text
    assert "이 대화창" in text


def test_cheap_gate_text_distinguishes_admin_followup_message():
    catalog = get_catalog("ko")
    result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="manual_handoff_request",
    )

    text = service.cheap_gate_text(result, "default", catalog)

    assert "운영 후속 확인" in text
    assert "이 대화창" in text


def test_cheap_gate_text_distinguishes_manual_resolution_message():
    catalog = get_catalog("ko")
    result = ValidationResult(
        classification=ValidationClassification.NEEDS_HANDOFF,
        source=RuleSource.CHEAP_GATE,
        reason="recovery_retry_limit_exceeded",
    )

    text = service.cheap_gate_text(result, "default", catalog)

    assert "수동 해결" in text
    assert "운영 검토" in text


def test_unknown_command_text_guides_to_related_items():
    catalog = get_catalog("ko")

    text = service.unknown_command_text(catalog)

    assert "아래 관련 항목" in text
