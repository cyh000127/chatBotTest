from PROJECT.conversations import guided_runtime_ux as guided_ux
from PROJECT.conversations.evidence_submission import service as evidence_service
from PROJECT.conversations.evidence_submission.states import (
    STATE_EVIDENCE_VALIDATING,
    STATE_EVIDENCE_WAITING_DOCUMENT,
    STATE_EVIDENCE_WAITING_LOCATION,
)
from PROJECT.conversations.field_binding.states import (
    STATE_FIELD_BINDING_CANDIDATE_SELECT,
    STATE_FIELD_BINDING_CODE,
    STATE_FIELD_BINDING_CONFIRM,
    STATE_FIELD_BINDING_LOCATION,
    STATE_FIELD_BINDING_METHOD,
    STATE_MYFIELDS_SUMMARY,
)
from PROJECT.conversations.input_resolve.states import (
    STATE_INPUT_RESOLVE_CANDIDATES,
    STATE_INPUT_RESOLVE_DECISION,
    STATE_INPUT_RESOLVE_METHOD,
    STATE_INPUT_RESOLVE_RAW_INPUT,
    STATE_INPUT_RESOLVE_TARGET,
)
from PROJECT.conversations.onboarding import service as onboarding_service
from PROJECT.conversations.onboarding.states import (
    STATE_ONBOARDING_CONFIRM,
    STATE_ONBOARDING_NAME,
    STATE_ONBOARDING_PENDING_APPROVAL,
    STATE_ONBOARDING_PHONE,
)
from PROJECT.canonical_intents import registry
from PROJECT.conversations.sample_menu import service as sample_service
from PROJECT.conversations.sample_menu.states import (
    STATE_CANCELLED,
    STATE_LANGUAGE_SELECT,
    STATE_MAIN_MENU,
)
from PROJECT.conversations.yield_intake.states import (
    STATE_YIELD_AMOUNT,
    STATE_YIELD_CONFIRM,
    STATE_YIELD_DATE,
    STATE_YIELD_FIELD,
    STATE_YIELD_READY,
)
from PROJECT.i18n.translator import get_catalog
from PROJECT.policy import classify_handoff_route
from PROJECT.policy.recovery_policy import evaluate_recovery_policy
from PROJECT.rule_engine.contracts import RecoveryContextDraft, ValidationResult
from PROJECT.rule_engine.recovery_classifier import classify_recovery_ux
from PROJECT.rule_engine.step_schema import render_shared_step_question, shared_step_schema_for_step


def assemble_recovery_context(
    *,
    current_step: str,
    latest_user_message: str,
    locale: str,
    recovery_attempt_count: int,
    canonical_intent: str | None = None,
    validation_result: ValidationResult | None = None,
    fallback_key: str | None = None,
    fertilizer_draft_data: dict | None = None,
    evidence_submission_draft_data: dict | None = None,
    onboarding_draft_data: dict | None = None,
    pending_slot: str | None = None,
) -> RecoveryContextDraft:
    prompt_schema = prompt_schema_for_state(
        current_step,
        locale=locale,
        fertilizer_draft_data=fertilizer_draft_data,
        evidence_submission_draft_data=evidence_submission_draft_data,
        onboarding_draft_data=onboarding_draft_data,
    )
    ux_decision = classify_recovery_ux(validation_result)
    policy_decision = evaluate_recovery_policy(
        recovery_attempt_count=recovery_attempt_count,
        ux_reason=ux_decision.reason,
    )
    task_context = task_context_for_state(
        current_step,
        pending_slot=pending_slot,
    )

    return RecoveryContextDraft(
        canonical_intent=canonical_intent or registry.INTENT_UNKNOWN_TEXT,
        current_step=current_step,
        current_question=prompt_schema["current_question"],
        expected_input_type=prompt_schema["expected_input_type"],
        allowed_value_shape=prompt_schema["allowed_value_shape"],
        latest_user_message=latest_user_message,
        recent_messages_summary=_summarize_session(
            current_step=current_step,
            fertilizer_draft_data=fertilizer_draft_data,
            onboarding_draft_data=onboarding_draft_data,
            pending_slot=pending_slot,
        ),
        locale=locale,
        recovery_attempt_count=recovery_attempt_count,
        hard_constraints=prompt_schema["hard_constraints"],
        metadata={
            "runtime_policy_scope": "subordinate_guidance",
            "fallback_key": fallback_key,
            "pending_slot": pending_slot,
            "validation_classification": validation_result.classification.value if validation_result is not None else None,
            "validation_reason": validation_result.reason if validation_result is not None else None,
            "ux_recovery_reason": ux_decision.reason.value,
            "ux_next_action_hint": ux_decision.next_action_hint,
            "recovery_policy_level": policy_decision.level.value,
            "recovery_should_offer_safe_exit": policy_decision.should_offer_safe_exit,
            "recovery_should_prioritize_buttons": policy_decision.should_prioritize_buttons,
            "recovery_domain": task_context["domain"],
            "recovery_task_hint": task_context["task_hint"],
            "recovery_resume_action": task_context["resume_action"],
            "recovery_focus_target": task_context["focus_target"],
            "step_progress": prompt_schema["step_progress"],
            "input_mode": prompt_schema["input_mode"],
            "runtime_handoff_reason_hint": validation_result.human_handoff_reason if validation_result is not None else None,
            "runtime_handoff_route_hint": (
                classify_handoff_route(
                    reason=validation_result.reason,
                    human_handoff_reason=validation_result.human_handoff_reason,
                    source=validation_result.source.value,
                ).value
                if validation_result is not None and validation_result.classification.value == "needs_handoff"
                else None
            ),
        },
    )


def prompt_schema_for_state(
    current_step: str,
    *,
    locale: str,
    fertilizer_draft_data: dict | None = None,
    evidence_submission_draft_data: dict | None = None,
    onboarding_draft_data: dict | None = None,
) -> dict[str, str | tuple[str, ...] | None]:
    catalog = get_catalog(locale)
    shared_schema = shared_step_schema_for_step(current_step)
    if shared_schema is not None:
        question = render_shared_step_question(
            current_step,
            locale=locale,
            context_data={"fertilizer_draft_data": fertilizer_draft_data},
        )
        return {
            "current_question": question or "",
            "expected_input_type": shared_schema.expected_input_type,
            "allowed_value_shape": shared_schema.allowed_value_shape,
            "step_progress": shared_schema.step_progress,
            "input_mode": shared_schema.input_mode,
            "hard_constraints": shared_schema.hard_constraints,
        }

    if current_step == STATE_MAIN_MENU:
        return {
            "current_question": sample_service.main_menu_text(catalog),
            "expected_input_type": "menu_selection",
            "allowed_value_shape": "one_of:fertilizer|yield|myfields|input_resolve|support|help|restart|cancel|language",
            "step_progress": None,
            "input_mode": None,
            "hard_constraints": (
                "menu_action_must_match_supported_intent",
            ),
        }

    if current_step == STATE_LANGUAGE_SELECT:
        return {
            "current_question": sample_service.language_menu_text(catalog),
            "expected_input_type": "language_selection",
            "allowed_value_shape": "one_of:ko|en|km",
            "step_progress": None,
            "input_mode": guided_ux.BUTTON_ONLY,
            "hard_constraints": (
                "language_must_be_supported_locale",
            ),
        }

    if current_step == STATE_CANCELLED:
        return {
            "current_question": sample_service.cancel_text(catalog),
            "expected_input_type": "restart_or_help",
            "allowed_value_shape": "one_of:restart|help|start",
            "step_progress": None,
            "input_mode": guided_ux.BUTTON_ONLY,
            "hard_constraints": (
                "cancelled_state_blocks_normal_flow",
            ),
        }

    if current_step == STATE_ONBOARDING_NAME:
        draft = onboarding_service.draft_from_dict(onboarding_draft_data)
        return {
            "current_question": onboarding_service.prompt_for_state(current_step, catalog, draft),
            "expected_input_type": "person_name",
            "allowed_value_shape": "short_text_name",
            "step_progress": "2/3",
            "input_mode": guided_ux.TEXT_ALLOWED,
            "hard_constraints": ("onboarding_name_required",),
        }

    if current_step == STATE_ONBOARDING_PHONE:
        draft = onboarding_service.draft_from_dict(onboarding_draft_data)
        return {
            "current_question": onboarding_service.prompt_for_state(current_step, catalog, draft),
            "expected_input_type": "phone_number",
            "allowed_value_shape": "phone_number_with_supported_country_code",
            "step_progress": "3/3",
            "input_mode": guided_ux.TEXT_ALLOWED,
            "hard_constraints": ("onboarding_phone_requires_supported_country_code",),
        }

    if current_step == STATE_ONBOARDING_CONFIRM:
        draft = onboarding_service.draft_from_dict(onboarding_draft_data)
        return {
            "current_question": onboarding_service.prompt_for_state(current_step, catalog, draft),
            "expected_input_type": "onboarding_confirmation",
            "allowed_value_shape": "one_of:confirm|edit_name|edit_phone|restart",
            "step_progress": "review",
            "input_mode": guided_ux.BUTTON_ONLY,
            "hard_constraints": ("onboarding_review_required_before_submit",),
        }

    if current_step == STATE_ONBOARDING_PENDING_APPROVAL:
        draft = onboarding_service.draft_from_dict(onboarding_draft_data)
        return {
            "current_question": onboarding_service.prompt_for_state(current_step, catalog, draft),
            "expected_input_type": "wait_or_safe_exit",
            "allowed_value_shape": "one_of:support|restart",
            "step_progress": "received",
            "input_mode": guided_ux.STATUS_WAIT,
            "hard_constraints": ("onboarding_pending_approval_wait_state",),
        }

    if current_step == STATE_MYFIELDS_SUMMARY:
        return {
            "current_question": catalog.MYFIELDS_SUMMARY_MESSAGE,
            "expected_input_type": "myfields_action",
            "allowed_value_shape": "one_of:register|refresh|back|restart",
            "step_progress": "summary",
            "input_mode": guided_ux.BUTTON_ONLY,
            "hard_constraints": ("myfields_summary_requires_guided_action",),
        }

    if current_step == STATE_FIELD_BINDING_METHOD:
        return {
            "current_question": catalog.MYFIELDS_METHOD_PROMPT,
            "expected_input_type": "field_lookup_method",
            "allowed_value_shape": "one_of:location|code",
            "step_progress": "1/4",
            "input_mode": guided_ux.BUTTON_ONLY,
            "hard_constraints": ("field_lookup_method_required",),
        }

    if current_step == STATE_FIELD_BINDING_LOCATION:
        return {
            "current_question": catalog.MYFIELDS_LOCATION_PROMPT,
            "expected_input_type": "location_attachment",
            "allowed_value_shape": "telegram_location_attachment",
            "step_progress": "2/4",
            "input_mode": guided_ux.LOCATION_ATTACHMENT,
            "hard_constraints": ("field_location_required",),
        }

    if current_step == STATE_FIELD_BINDING_CODE:
        return {
            "current_question": catalog.MYFIELDS_CODE_PROMPT,
            "expected_input_type": "field_registry_code",
            "allowed_value_shape": "free_text_registry_code",
            "step_progress": "2/4",
            "input_mode": guided_ux.TEXT_ALLOWED,
            "hard_constraints": ("field_code_required",),
        }

    if current_step == STATE_FIELD_BINDING_CANDIDATE_SELECT:
        return {
            "current_question": catalog.MYFIELDS_CANDIDATE_PROMPT,
            "expected_input_type": "field_candidate_selection",
            "allowed_value_shape": "one_of:listed_candidate",
            "step_progress": "3/4",
            "input_mode": guided_ux.BUTTON_ONLY,
            "hard_constraints": ("field_candidate_selection_required",),
        }

    if current_step == STATE_FIELD_BINDING_CONFIRM:
        return {
            "current_question": catalog.MYFIELDS_CONFIRM_MESSAGE,
            "expected_input_type": "field_binding_confirmation",
            "allowed_value_shape": "one_of:confirm|back|restart",
            "step_progress": "review",
            "input_mode": guided_ux.BUTTON_ONLY,
            "hard_constraints": ("field_binding_confirmation_required",),
        }

    if current_step == STATE_EVIDENCE_WAITING_LOCATION:
        return {
            "current_question": evidence_service.prompt_for_state(
                STATE_EVIDENCE_WAITING_LOCATION,
                catalog,
                evidence_service.draft_from_dict(evidence_submission_draft_data),
            ),
            "expected_input_type": "location_attachment",
            "allowed_value_shape": "telegram_location_attachment",
            "step_progress": "1/2",
            "input_mode": guided_ux.LOCATION_ATTACHMENT,
            "hard_constraints": ("evidence_location_required_before_document",),
        }

    if current_step == STATE_EVIDENCE_WAITING_DOCUMENT:
        return {
            "current_question": evidence_service.prompt_for_state(
                STATE_EVIDENCE_WAITING_DOCUMENT,
                catalog,
                evidence_service.draft_from_dict(evidence_submission_draft_data),
            ),
            "expected_input_type": "document_upload",
            "allowed_value_shape": "telegram_document_upload",
            "step_progress": "2/2",
            "input_mode": guided_ux.DOCUMENT_UPLOAD,
            "hard_constraints": ("evidence_document_required_after_location",),
        }

    if current_step == STATE_EVIDENCE_VALIDATING:
        return {
            "current_question": evidence_service.prompt_for_state(
                STATE_EVIDENCE_VALIDATING,
                catalog,
                evidence_service.draft_from_dict(evidence_submission_draft_data),
            ),
            "expected_input_type": "wait_or_safe_exit",
            "allowed_value_shape": "one_of:help|restart|support",
            "step_progress": "review",
            "input_mode": guided_ux.STATUS_WAIT,
            "hard_constraints": ("evidence_validation_wait_state",),
        }

    return {
        "current_question": sample_service.main_menu_text(catalog),
        "expected_input_type": "unknown",
        "allowed_value_shape": "unknown",
        "step_progress": None,
        "input_mode": None,
        "hard_constraints": (),
    }


def task_context_for_state(
    current_step: str,
    *,
    pending_slot: str | None = None,
) -> dict[str, str]:
    if current_step == STATE_MAIN_MENU:
        return {
            "domain": "menu",
            "task_hint": "main_menu_selection",
            "resume_action": "choose_menu_action",
            "focus_target": "menu_action",
        }

    if current_step == STATE_LANGUAGE_SELECT:
        return {
            "domain": "settings",
            "task_hint": "language_selection",
            "resume_action": "choose_language",
            "focus_target": "locale",
        }

    if current_step == STATE_CANCELLED:
        return {
            "domain": "session",
            "task_hint": "cancelled_flow",
            "resume_action": "restart_or_open_help",
            "focus_target": "restart",
        }

    if current_step in {
        STATE_YIELD_READY,
        STATE_YIELD_FIELD,
        STATE_YIELD_AMOUNT,
        STATE_YIELD_DATE,
        STATE_YIELD_CONFIRM,
    }:
        return {
            "domain": "yield",
            "task_hint": "yield_step_input",
            "resume_action": "continue_yield_input",
            "focus_target": pending_slot or "yield_current_step",
        }

    if current_step in {
        STATE_ONBOARDING_NAME,
        STATE_ONBOARDING_PHONE,
        STATE_ONBOARDING_CONFIRM,
        STATE_ONBOARDING_PENDING_APPROVAL,
    }:
        return {
            "domain": "onboarding",
            "task_hint": "onboarding_step_input",
            "resume_action": "continue_onboarding",
            "focus_target": pending_slot or "onboarding_current_step",
        }

    if current_step in {
        STATE_INPUT_RESOLVE_TARGET,
        STATE_INPUT_RESOLVE_METHOD,
        STATE_INPUT_RESOLVE_RAW_INPUT,
        STATE_INPUT_RESOLVE_CANDIDATES,
        STATE_INPUT_RESOLVE_DECISION,
    }:
        return {
            "domain": "input_resolve",
            "task_hint": "input_resolve_step",
            "resume_action": "continue_input_resolution",
            "focus_target": pending_slot or "input_resolution",
        }

    if current_step in {
        STATE_MYFIELDS_SUMMARY,
        STATE_FIELD_BINDING_METHOD,
        STATE_FIELD_BINDING_LOCATION,
        STATE_FIELD_BINDING_CODE,
        STATE_FIELD_BINDING_CANDIDATE_SELECT,
        STATE_FIELD_BINDING_CONFIRM,
    }:
        return {
            "domain": "myfields",
            "task_hint": "field_binding_step",
            "resume_action": "continue_field_binding",
            "focus_target": pending_slot or "field_binding",
        }

    if current_step in {
        STATE_EVIDENCE_WAITING_LOCATION,
        STATE_EVIDENCE_WAITING_DOCUMENT,
        STATE_EVIDENCE_VALIDATING,
    }:
        return {
            "domain": "evidence",
            "task_hint": "evidence_submission_step",
            "resume_action": "continue_evidence_submission",
            "focus_target": pending_slot or "evidence_submission",
        }

    return {
        "domain": "general",
        "task_hint": "generic_recovery",
        "resume_action": "offer_related_actions",
        "focus_target": pending_slot or "current_step",
    }


def _summarize_session(
    *,
    current_step: str,
    fertilizer_draft_data: dict | None,
    onboarding_draft_data: dict | None,
    pending_slot: str | None,
) -> str:
    summary_parts = [f"state={current_step}"]
    if pending_slot is not None:
        summary_parts.append(f"pending_slot={pending_slot}")

    if fertilizer_draft_data:
        fertilizer_fields = []
        if fertilizer_draft_data.get("used") is not None:
            fertilizer_fields.append("used")
        if fertilizer_draft_data.get("kind"):
            fertilizer_fields.append("kind")
        if fertilizer_draft_data.get("product_name"):
            fertilizer_fields.append("product_name")
        if fertilizer_draft_data.get("amount_value") is not None and fertilizer_draft_data.get("amount_unit"):
            fertilizer_fields.append("amount")
        if fertilizer_draft_data.get("applied_date"):
            fertilizer_fields.append("applied_date")
        if fertilizer_fields:
            summary_parts.append(f"fertilizer_draft_fields={','.join(fertilizer_fields)}")

    if onboarding_draft_data:
        onboarding_fields = []
        if onboarding_draft_data.get("preferred_locale"):
            onboarding_fields.append("preferred_locale")
        if onboarding_draft_data.get("name"):
            onboarding_fields.append("name")
        if onboarding_draft_data.get("phone_normalized"):
            onboarding_fields.append("phone")
        if onboarding_fields:
            summary_parts.append(f"onboarding_draft_fields={','.join(onboarding_fields)}")

    return "; ".join(summary_parts)
