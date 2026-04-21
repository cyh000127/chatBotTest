import json
import logging
from typing import Any


LOGGER_NAME = "PROJECT.telemetry"


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def log_event(event: str, **fields: Any) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    payload = {"event": event, **_clean_fields(fields)}
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _clean_fields(fields: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
            continue
        if isinstance(value, (list, tuple)):
            cleaned[key] = [item for item in value if isinstance(item, (str, int, float, bool))]
            continue
        cleaned[key] = str(value)
    return cleaned
