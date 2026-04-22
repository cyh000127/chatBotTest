import logging
from types import SimpleNamespace

from PROJECT.channels.telegram.handlers.messages import (
    log_recovery_action_event,
    log_recovery_classification_event,
)
from PROJECT.rule_engine import RuleSource, ValidationClassification, ValidationResult, assemble_recovery_context
from PROJECT.telemetry.event_logger import LOGGER_NAME


def test_log_recovery_classification_event_writes_reason_and_policy(caplog):
    recovery_context = assemble_recovery_context(
        current_step="main_menu",
        latest_user_message="아무거나",
        locale="ko",
        recovery_attempt_count=3,
        validation_result=ValidationResult(
            classification=ValidationClassification.NEEDS_HANDOFF,
            source=RuleSource.CHEAP_GATE,
            reason="recovery_retry_limit_exceeded",
            human_handoff_reason="cheap_gate_retry_limit",
        ),
        fallback_key="default",
    )

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        log_recovery_classification_event(recovery_context, source="late_gate_handoff")

    message = caplog.records[0].getMessage()
    assert '"event": "recovery_classified"' in message
    assert '"policy_level": "escalation_ready"' in message
    assert '"recovery_reason": "repeated_failure"' in message


def test_log_recovery_action_event_writes_selected_action(caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        log_recovery_action_event(
            action="repair_confirmation_shown",
            domain="fertilizer",
            target_state="fertilizer_confirm",
            scope="confirmed",
            has_candidate=True,
            slot_count=3,
        )

    message = caplog.records[0].getMessage()
    assert '"event": "recovery_action_selected"' in message
    assert '"action": "repair_confirmation_shown"' in message
    assert '"slot_count": 3' in message
