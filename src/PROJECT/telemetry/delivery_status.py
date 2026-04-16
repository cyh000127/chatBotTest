from enum import Enum


class DeliveryStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
