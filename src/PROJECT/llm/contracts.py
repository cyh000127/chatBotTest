from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class LlmRecoveryClassification(StrEnum):
    RESOLVED_CANDIDATE = "resolved_candidate"
    NEEDS_CLARIFICATION = "needs_clarification"
    NEEDS_INPUT_RESOLUTION = "needs_input_resolution"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    RETRY_WITH_NEW_INPUT = "retry_with_new_input"
    UNSUPPORTED = "unsupported"


class LlmRelevance(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass(frozen=True)
class LlmRecoveryResult:
    classification: LlmRecoveryClassification
    relevance_to_current_step: LlmRelevance
    normalized_candidate: dict[str, Any] | None = None
    candidate_confidence: float | None = None
    needs_clarification: bool = False
    clarification_question: str | None = None
    needs_human: bool = False
    human_handoff_reason: str | None = None
    safety_flags: tuple[str, ...] = ()
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
