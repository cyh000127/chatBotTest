from PROJECT.rule_engine import (
    IntentDecision,
    NormalizedInput,
    RecoveryContextDraft,
    ResolutionCandidate,
    RuleSource,
    ValidationClassification,
    ValidationResult,
)


def test_normalized_input_to_dict_preserves_core_fields():
    normalized = NormalizedInput(
        raw_text="  /fertilizer 입력할게요  ",
        normalized_text="/fertilizer 입력할게요",
        locale="ko",
        tokens=("/fertilizer", "입력할게요"),
        command="/fertilizer",
    )

    payload = normalized.to_dict()

    assert payload["raw_text"] == "  /fertilizer 입력할게요  "
    assert payload["normalized_text"] == "/fertilizer 입력할게요"
    assert payload["locale"] == "ko"
    assert payload["command"] == "/fertilizer"


def test_intent_decision_contract_supports_payload_and_rule_metadata():
    decision = IntentDecision(
        canonical_intent="fertilizer.input.start",
        current_step="entry",
        source=RuleSource.INTENT_RULE,
        matched_rule="fertilizer_start_keyword",
        payload={"entry_source": "text"},
    )

    assert decision.canonical_intent == "fertilizer.input.start"
    assert decision.source == RuleSource.INTENT_RULE
    assert decision.payload["entry_source"] == "text"


def test_validation_result_wraps_resolution_candidate():
    candidate = ResolutionCandidate(
        field_name="amount",
        raw_value="20kg",
        normalized_value={"amount": 20, "unit": "kg"},
        candidate_type="numeric_amount",
        source=RuleSource.SLOT_EXTRACTOR,
    )
    result = ValidationResult(
        classification=ValidationClassification.RESOLVED,
        source=RuleSource.VALIDATOR,
        normalized_candidate=candidate,
    )

    assert result.is_resolved is True
    assert result.normalized_candidate is not None
    assert result.normalized_candidate.normalized_value["unit"] == "kg"


def test_recovery_context_draft_matches_stage_three_minimum_shape():
    draft = RecoveryContextDraft(
        canonical_intent="yield.input.start",
        current_step="ask_yield_amount",
        current_question="수확량을 입력해주세요.",
        expected_input_type="numeric_amount",
        allowed_value_shape="positive number with optional unit",
        latest_user_message="세 포대쯤 돼요",
        recent_messages_summary="User is answering the harvest amount question after selecting one field.",
        locale="ko",
        recovery_attempt_count=1,
        hard_constraints=(
            "Do not infer identity",
            "Ask one short clarification question if amount is ambiguous",
        ),
    )

    payload = draft.to_dict()

    assert payload["canonical_intent"] == "yield.input.start"
    assert payload["current_step"] == "ask_yield_amount"
    assert payload["recovery_attempt_count"] == 1
    assert len(payload["hard_constraints"]) == 2
