from PROJECT.canonical_intents import registry
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake.states import STATE_FERTILIZER_CONFIRM
from PROJECT.conversations.input_resolve.states import STATE_INPUT_RESOLVE_CANDIDATES
from PROJECT.conversations.yield_intake.states import STATE_YIELD_AMOUNT
from PROJECT.rule_engine import render_shared_step_question, shared_step_schema_for_step


def test_shared_step_schema_for_yield_amount():
    schema = shared_step_schema_for_step(STATE_YIELD_AMOUNT)

    assert schema is not None
    assert schema.domain == "yield"
    assert schema.canonical_intent == registry.INTENT_YIELD_INPUT_START
    assert schema.expected_input_type == "yield_amount"


def test_shared_step_schema_for_input_resolve_candidates():
    schema = shared_step_schema_for_step(STATE_INPUT_RESOLVE_CANDIDATES)

    assert schema is not None
    assert schema.domain == "input_resolve"
    assert schema.canonical_intent == registry.INTENT_INPUT_RESOLVE_START
    assert "candidate_selection" == schema.expected_input_type


def test_render_shared_step_question_for_fertilizer_confirm_uses_draft():
    draft = fertilizer_service.update_draft(
        fertilizer_service.new_draft(),
        used=True,
        kind="compound",
        product_name="한아름 복합비료",
        amount_value=20.0,
        amount_unit="kg",
        applied_date="2026-04-21",
    )

    question = render_shared_step_question(
        STATE_FERTILIZER_CONFIRM,
        locale="ko",
        context_data={"fertilizer_draft_data": draft.to_dict()},
    )

    assert question is not None
    assert "한아름 복합비료" in question
    assert "2026-04-21" in question
