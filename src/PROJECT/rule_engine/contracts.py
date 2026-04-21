from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class RuleSource(StrEnum):
    NORMALIZER = "normalizer"
    INTENT_RULE = "intent_rule"
    SLOT_EXTRACTOR = "slot_extractor"
    ALIAS_RESOLUTION = "alias_resolution"
    VALIDATOR = "validator"
    REPAIR = "repair"
    CHEAP_GATE = "cheap_gate"


class ValidationClassification(StrEnum):
    RESOLVED = "resolved"
    REASK = "reask"
    UNSUPPORTED = "unsupported"
    NEEDS_HANDOFF = "needs_handoff"
    UNRESOLVED_RECOVERABLE = "unresolved_recoverable"


@dataclass(frozen=True)
class NormalizedInput:
    raw_text: str
    normalized_text: str
    locale: str
    tokens: tuple[str, ...] = ()
    command: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntentDecision:
    canonical_intent: str | None
    current_step: str | None
    source: RuleSource
    confidence: float = 1.0
    matched_rule: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolutionCandidate:
    field_name: str
    raw_value: str
    candidate_type: str
    source: RuleSource
    normalized_value: Any = None
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    classification: ValidationClassification
    source: RuleSource
    normalized_candidate: ResolutionCandidate | None = None
    reason: str | None = None
    clarification_question: str | None = None
    human_handoff_reason: str | None = None
    safety_flags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_resolved(self) -> bool:
        return self.classification == ValidationClassification.RESOLVED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryContextDraft:
    canonical_intent: str
    current_step: str
    current_question: str
    expected_input_type: str
    allowed_value_shape: str
    latest_user_message: str
    recent_messages_summary: str
    locale: str
    recovery_attempt_count: int = 0
    hard_constraints: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
