import json
from enum import Enum
from pathlib import Path

from PROJECT.rule_engine import (
    IntentDecision,
    NormalizedInput,
    RecoveryContextDraft,
    ResolutionCandidate,
    RuleSource,
    ValidationClassification,
    ValidationResult,
    render_shared_step_question,
    shared_step_schema_for_step,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _json_ready(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(inner) for key, inner in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(inner) for inner in value]
    if isinstance(value, list):
        return [_json_ready(inner) for inner in value]
    return value


def _normalized_input_from_payload(payload: dict) -> NormalizedInput:
    return NormalizedInput(
        raw_text=payload["raw_text"],
        normalized_text=payload["normalized_text"],
        locale=payload["locale"],
        tokens=tuple(payload.get("tokens", [])),
        command=payload.get("command"),
        metadata=payload.get("metadata", {}),
    )


def _intent_decision_from_payload(payload: dict) -> IntentDecision:
    return IntentDecision(
        canonical_intent=payload.get("canonical_intent"),
        current_step=payload.get("current_step"),
        source=RuleSource(payload["source"]),
        confidence=payload.get("confidence", 1.0),
        matched_rule=payload.get("matched_rule"),
        payload=payload.get("payload", {}),
    )


def _resolution_candidate_from_payload(payload: dict) -> ResolutionCandidate:
    return ResolutionCandidate(
        field_name=payload["field_name"],
        raw_value=payload["raw_value"],
        candidate_type=payload["candidate_type"],
        source=RuleSource(payload["source"]),
        normalized_value=payload.get("normalized_value"),
        confidence=payload.get("confidence", 1.0),
        metadata=payload.get("metadata", {}),
    )


def _validation_result_from_payload(payload: dict) -> ValidationResult:
    candidate_payload = payload.get("normalized_candidate")
    return ValidationResult(
        classification=ValidationClassification(payload["classification"]),
        source=RuleSource(payload["source"]),
        normalized_candidate=_resolution_candidate_from_payload(candidate_payload) if candidate_payload else None,
        reason=payload.get("reason"),
        clarification_question=payload.get("clarification_question"),
        human_handoff_reason=payload.get("human_handoff_reason"),
        safety_flags=tuple(payload.get("safety_flags", [])),
        metadata=payload.get("metadata", {}),
    )


def _recovery_context_from_payload(payload: dict) -> RecoveryContextDraft:
    return RecoveryContextDraft(
        canonical_intent=payload["canonical_intent"],
        current_step=payload["current_step"],
        current_question=payload["current_question"],
        expected_input_type=payload["expected_input_type"],
        allowed_value_shape=payload["allowed_value_shape"],
        latest_user_message=payload["latest_user_message"],
        recent_messages_summary=payload["recent_messages_summary"],
        locale=payload["locale"],
        recovery_attempt_count=payload.get("recovery_attempt_count", 0),
        hard_constraints=tuple(payload.get("hard_constraints", [])),
        metadata=payload.get("metadata", {}),
    )


def test_rule_engine_contract_fixtures_round_trip():
    fixture = _load_fixture("rule_engine_contracts.json")

    for case in fixture["normalized_inputs"]:
        payload = case["payload"]
        normalized = _normalized_input_from_payload(payload)
        assert _json_ready(normalized.to_dict()) == payload, case["id"]

    for case in fixture["intent_decisions"]:
        payload = case["payload"]
        decision = _intent_decision_from_payload(payload)
        assert _json_ready(decision.to_dict()) == payload, case["id"]

    for case in fixture["validation_results"]:
        payload = case["payload"]
        result = _validation_result_from_payload(payload)
        assert _json_ready(result.to_dict()) == payload, case["id"]

    for case in fixture["recovery_contexts"]:
        payload = case["payload"]
        context = _recovery_context_from_payload(payload)
        assert _json_ready(context.to_dict()) == payload, case["id"]


def test_shared_step_schema_cross_domain_fixtures():
    fixture = _load_fixture("shared_step_schemas.json")

    for case in fixture["schemas"]:
        schema = shared_step_schema_for_step(case["state"])

        assert schema is not None, case["id"]
        assert schema.domain == case["domain"], case["id"]
        assert schema.canonical_intent == case["canonical_intent"], case["id"]
        assert schema.expected_input_type == case["expected_input_type"], case["id"]
        assert schema.allowed_value_shape == case["allowed_value_shape"], case["id"]
        assert list(schema.hard_constraints) == case["hard_constraints"], case["id"]

        question = render_shared_step_question(
            case["state"],
            locale=case.get("locale", "ko"),
            context_data=case.get("context_data"),
        )

        assert question is not None, case["id"]
        for snippet in case["expected_prompt_contains"]:
            assert snippet in question, case["id"]
