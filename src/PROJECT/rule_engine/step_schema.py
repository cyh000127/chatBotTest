from dataclasses import dataclass
from typing import Callable

from PROJECT.canonical_intents import registry
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)
from PROJECT.conversations.input_resolve.states import (
    STATE_INPUT_RESOLVE_CANDIDATES,
    STATE_INPUT_RESOLVE_DECISION,
    STATE_INPUT_RESOLVE_METHOD,
    STATE_INPUT_RESOLVE_RAW_INPUT,
    STATE_INPUT_RESOLVE_TARGET,
)
from PROJECT.conversations.yield_intake.states import (
    STATE_YIELD_AMOUNT,
    STATE_YIELD_CONFIRM,
    STATE_YIELD_DATE,
    STATE_YIELD_FIELD,
    STATE_YIELD_READY,
)
from PROJECT.i18n.translator import get_catalog


@dataclass(frozen=True)
class SharedStepSchema:
    domain: str
    canonical_intent: str
    current_step: str
    expected_input_type: str
    allowed_value_shape: str
    hard_constraints: tuple[str, ...]
    question_factory: Callable[[object, dict], str]


def shared_step_schema_for_step(current_step: str) -> SharedStepSchema | None:
    return SHARED_STEP_SCHEMAS.get(current_step)


def render_shared_step_question(
    current_step: str,
    *,
    locale: str,
    context_data: dict | None = None,
) -> str | None:
    schema = shared_step_schema_for_step(current_step)
    if schema is None:
        return None
    catalog = get_catalog(locale)
    return schema.question_factory(catalog, context_data or {})


SHARED_STEP_SCHEMAS = {
    STATE_FERTILIZER_USED: SharedStepSchema(
        domain="fertilizer",
        canonical_intent=registry.INTENT_AGRI_INPUT_START,
        current_step=STATE_FERTILIZER_USED,
        expected_input_type="binary_yes_no",
        allowed_value_shape="one_of:used|not_used",
        hard_constraints=("fertilizer_usage_flag_required",),
        question_factory=lambda catalog, _: catalog.FERTILIZER_USED_PROMPT,
    ),
    STATE_FERTILIZER_KIND: SharedStepSchema(
        domain="fertilizer",
        canonical_intent=registry.INTENT_AGRI_INPUT_START,
        current_step=STATE_FERTILIZER_KIND,
        expected_input_type="fertilizer_kind",
        allowed_value_shape="one_of:compound|urea|compost|liquid",
        hard_constraints=("fertilizer_kind_must_be_supported",),
        question_factory=lambda catalog, _: catalog.FERTILIZER_KIND_PROMPT,
    ),
    STATE_FERTILIZER_PRODUCT: SharedStepSchema(
        domain="fertilizer",
        canonical_intent=registry.INTENT_AGRI_INPUT_START,
        current_step=STATE_FERTILIZER_PRODUCT,
        expected_input_type="product_name",
        allowed_value_shape="free_text_product_name",
        hard_constraints=("product_name_required_before_amount",),
        question_factory=lambda catalog, _: catalog.FERTILIZER_PRODUCT_PROMPT,
    ),
    STATE_FERTILIZER_AMOUNT: SharedStepSchema(
        domain="fertilizer",
        canonical_intent=registry.INTENT_AGRI_INPUT_START,
        current_step=STATE_FERTILIZER_AMOUNT,
        expected_input_type="amount_with_unit",
        allowed_value_shape="supported_amount_unit_pair",
        hard_constraints=("amount_requires_supported_unit",),
        question_factory=lambda catalog, _: catalog.FERTILIZER_AMOUNT_PROMPT,
    ),
    STATE_FERTILIZER_DATE: SharedStepSchema(
        domain="fertilizer",
        canonical_intent=registry.INTENT_AGRI_INPUT_START,
        current_step=STATE_FERTILIZER_DATE,
        expected_input_type="applied_date",
        allowed_value_shape="absolute_or_limited_relative_date",
        hard_constraints=("applied_date_required_before_confirm",),
        question_factory=lambda catalog, _: catalog.FERTILIZER_DATE_PROMPT,
    ),
    STATE_FERTILIZER_CONFIRM: SharedStepSchema(
        domain="fertilizer",
        canonical_intent=registry.INTENT_AGRI_INPUT_START,
        current_step=STATE_FERTILIZER_CONFIRM,
        expected_input_type="confirmation_action",
        allowed_value_shape="one_of:confirm|back|cancel",
        hard_constraints=("fertilizer_entry_must_be_reviewed_before_finalize",),
        question_factory=lambda catalog, data: fertilizer_service.confirmation_text(
            fertilizer_service.draft_from_dict(data.get("fertilizer_draft_data")),
            catalog,
        ),
    ),
    STATE_YIELD_READY: SharedStepSchema(
        domain="yield",
        canonical_intent=registry.INTENT_YIELD_INPUT_START,
        current_step=STATE_YIELD_READY,
        expected_input_type="binary_ready_status",
        allowed_value_shape="one_of:ready|not_ready",
        hard_constraints=("yield_ready_status_required",),
        question_factory=lambda catalog, _: catalog.YIELD_READY_PROMPT,
    ),
    STATE_YIELD_FIELD: SharedStepSchema(
        domain="yield",
        canonical_intent=registry.INTENT_YIELD_INPUT_START,
        current_step=STATE_YIELD_FIELD,
        expected_input_type="field_selection",
        allowed_value_shape="registered_field_alias_or_button",
        hard_constraints=("field_selection_required_before_yield_amount",),
        question_factory=lambda catalog, _: catalog.YIELD_FIELD_PROMPT,
    ),
    STATE_YIELD_AMOUNT: SharedStepSchema(
        domain="yield",
        canonical_intent=registry.INTENT_YIELD_INPUT_START,
        current_step=STATE_YIELD_AMOUNT,
        expected_input_type="yield_amount",
        allowed_value_shape="numeric_or_numeric_with_supported_unit",
        hard_constraints=("yield_amount_requires_supported_unit_or_default_kg",),
        question_factory=lambda catalog, _: catalog.YIELD_AMOUNT_PROMPT,
    ),
    STATE_YIELD_DATE: SharedStepSchema(
        domain="yield",
        canonical_intent=registry.INTENT_YIELD_INPUT_START,
        current_step=STATE_YIELD_DATE,
        expected_input_type="harvest_date",
        allowed_value_shape="absolute_or_limited_relative_date",
        hard_constraints=("harvest_date_required_before_confirm",),
        question_factory=lambda catalog, _: catalog.YIELD_DATE_PROMPT,
    ),
    STATE_YIELD_CONFIRM: SharedStepSchema(
        domain="yield",
        canonical_intent=registry.INTENT_YIELD_INPUT_START,
        current_step=STATE_YIELD_CONFIRM,
        expected_input_type="confirmation_action",
        allowed_value_shape="one_of:confirm|edit|cancel",
        hard_constraints=("yield_entry_must_be_reviewed_before_finalize",),
        question_factory=lambda catalog, _: catalog.YIELD_CONFIRM_PROMPT,
    ),
    STATE_INPUT_RESOLVE_TARGET: SharedStepSchema(
        domain="input_resolve",
        canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
        current_step=STATE_INPUT_RESOLVE_TARGET,
        expected_input_type="resolution_target_type",
        allowed_value_shape="declared_resolution_target",
        hard_constraints=("resolution_target_must_be_known",),
        question_factory=lambda catalog, _: catalog.INPUT_RESOLVE_TARGET_PROMPT,
    ),
    STATE_INPUT_RESOLVE_METHOD: SharedStepSchema(
        domain="input_resolve",
        canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
        current_step=STATE_INPUT_RESOLVE_METHOD,
        expected_input_type="resolution_input_method",
        allowed_value_shape="one_of:typed_text|ocr_image|candidate_retry",
        hard_constraints=("resolution_method_required_before_candidate_generation",),
        question_factory=lambda catalog, _: catalog.INPUT_RESOLVE_METHOD_PROMPT,
    ),
    STATE_INPUT_RESOLVE_RAW_INPUT: SharedStepSchema(
        domain="input_resolve",
        canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
        current_step=STATE_INPUT_RESOLVE_RAW_INPUT,
        expected_input_type="raw_resolution_input",
        allowed_value_shape="typed_text_or_ocr_result",
        hard_constraints=("raw_resolution_input_required_before_candidate_generation",),
        question_factory=lambda catalog, _: catalog.INPUT_RESOLVE_RAW_INPUT_PROMPT,
    ),
    STATE_INPUT_RESOLVE_CANDIDATES: SharedStepSchema(
        domain="input_resolve",
        canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
        current_step=STATE_INPUT_RESOLVE_CANDIDATES,
        expected_input_type="candidate_selection",
        allowed_value_shape="one_of:candidate_1|candidate_2|candidate_3|retry|none",
        hard_constraints=("candidate_selection_or_retry_required",),
        question_factory=lambda catalog, _: catalog.INPUT_RESOLVE_CANDIDATES_PROMPT,
    ),
    STATE_INPUT_RESOLVE_DECISION: SharedStepSchema(
        domain="input_resolve",
        canonical_intent=registry.INTENT_INPUT_RESOLVE_START,
        current_step=STATE_INPUT_RESOLVE_DECISION,
        expected_input_type="resolution_decision",
        allowed_value_shape="one_of:resolved|retry|manual_review",
        hard_constraints=("resolution_decision_must_close_or_retry_session",),
        question_factory=lambda catalog, _: catalog.INPUT_RESOLVE_DECISION_PROMPT,
    ),
}
