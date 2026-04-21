import logging

from PROJECT.telemetry.event_logger import LOGGER_NAME, log_event


def test_log_event_writes_json_payload(caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        log_event("repair_candidate_applied", domain="fertilizer", target_state="fertilizer_product", count=1)

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert '"event": "repair_candidate_applied"' in message
    assert '"domain": "fertilizer"' in message
    assert '"target_state": "fertilizer_product"' in message
