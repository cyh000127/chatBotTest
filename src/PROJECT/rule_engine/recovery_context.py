from PROJECT.canonical_intents import registry
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_EDIT_SELECT,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)
from PROJECT.conversations.sample_menu import service as sample_service
from PROJECT.conversations.sample_menu.states import (
    STATE_AUTH_ID_INPUT,
    STATE_CANCELLED,
    STATE_LANGUAGE_SELECT,
    STATE_MAIN_MENU,
    STATE_WEATHER_MENU,
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
    profile_draft_data: dict | None = None,
    fertilizer_draft_data: dict | None = None,
    confirmed_profile_data: dict | None = None,
    pending_slot: str | None = None,
    selected_city: str | None = None,
) -> RecoveryContextDraft:
    prompt_schema = prompt_schema_for_state(
        current_step,
        locale=locale,
        profile_draft_data=profile_draft_data,
        fertilizer_draft_data=fertilizer_draft_data,
        selected_city=selected_city,
    )
    ux_decision = classify_recovery_ux(validation_result)
    policy_decision = evaluate_recovery_policy(
        recovery_attempt_count=recovery_attempt_count,
        ux_reason=ux_decision.reason,
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
            profile_draft_data=profile_draft_data,
            fertilizer_draft_data=fertilizer_draft_data,
            confirmed_profile_data=confirmed_profile_data,
            pending_slot=pending_slot,
            selected_city=selected_city,
        ),
        locale=locale,
        recovery_attempt_count=recovery_attempt_count,
        hard_constraints=prompt_schema["hard_constraints"],
        metadata={
            "runtime_policy_scope": "subordinate_guidance",
            "fallback_key": fallback_key,
            "pending_slot": pending_slot,
            "selected_city": selected_city,
            "validation_classification": validation_result.classification.value if validation_result is not None else None,
            "validation_reason": validation_result.reason if validation_result is not None else None,
            "ux_recovery_reason": ux_decision.reason.value,
            "ux_next_action_hint": ux_decision.next_action_hint,
            "recovery_policy_level": policy_decision.level.value,
            "recovery_should_offer_safe_exit": policy_decision.should_offer_safe_exit,
            "recovery_should_prioritize_buttons": policy_decision.should_prioritize_buttons,
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
    profile_draft_data: dict | None = None,
    fertilizer_draft_data: dict | None = None,
    selected_city: str | None = None,
) -> dict[str, str | tuple[str, ...]]:
    catalog = get_catalog(locale)
    draft = profile_service.draft_from_dict(profile_draft_data)
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
            "hard_constraints": shared_schema.hard_constraints,
        }

    if current_step == STATE_AUTH_ID_INPUT:
        return {
            "current_question": sample_service.auth_start_text(catalog),
            "expected_input_type": "login_id",
            "allowed_value_shape": "registered_login_id_text",
            "hard_constraints": (
                "authentication_required_before_service_access",
                "two_auth_failures_reset_session",
            ),
        }

    if current_step == STATE_MAIN_MENU:
        return {
            "current_question": sample_service.main_menu_text(catalog),
            "expected_input_type": "menu_selection",
            "allowed_value_shape": "one_of:show_today_date|open_weather_menu|profile|help|restart|cancel",
            "hard_constraints": (
                "authenticated_session_required",
                "menu_action_must_match_supported_intent",
            ),
        }

    if current_step == STATE_WEATHER_MENU:
        return {
            "current_question": sample_service.weather_menu_text(catalog),
            "expected_input_type": "city_selection",
            "allowed_value_shape": "one_of:supported_weather_city",
            "hard_constraints": (
                "city_must_be_supported_weather_location",
                f"selected_city_context={selected_city}" if selected_city else "selected_city_context=none",
            ),
        }

    if current_step == STATE_LANGUAGE_SELECT:
        return {
            "current_question": sample_service.language_menu_text(catalog),
            "expected_input_type": "language_selection",
            "allowed_value_shape": "one_of:ko|en|km",
            "hard_constraints": (
                "language_must_be_supported_locale",
            ),
        }

    if current_step == STATE_CANCELLED:
        return {
            "current_question": sample_service.cancel_text(catalog),
            "expected_input_type": "restart_or_help",
            "allowed_value_shape": "one_of:restart|help|start",
            "hard_constraints": (
                "cancelled_state_blocks_normal_flow",
            ),
        }

    if current_step == STATE_PROFILE_NAME:
        return {
            "current_question": profile_service.prompt_for_state(current_step, catalog),
            "expected_input_type": "person_name",
            "allowed_value_shape": "short_free_text_name",
            "hard_constraints": (
                "name_required_before_profile_progress",
                "name_length_max_20",
            ),
        }

    if current_step == STATE_PROFILE_RESIDENCE:
        return {
            "current_question": profile_service.prompt_for_state(current_step, catalog),
            "expected_input_type": "residence_text",
            "allowed_value_shape": "free_text_residence",
            "hard_constraints": (
                "residence_required_before_city",
            ),
        }

    if current_step == STATE_PROFILE_CITY:
        return {
            "current_question": profile_service.prompt_for_state(current_step, catalog),
            "expected_input_type": "city_or_province",
            "allowed_value_shape": "free_text_city_or_province",
            "hard_constraints": (
                "city_required_before_district",
            ),
        }

    if current_step == STATE_PROFILE_DISTRICT:
        return {
            "current_question": profile_service.prompt_for_state(current_step, catalog),
            "expected_input_type": "district_or_county",
            "allowed_value_shape": "free_text_district_county_city",
            "hard_constraints": (
                "district_required_before_birth_date",
            ),
        }

    if current_step == STATE_PROFILE_BIRTH_YEAR:
        return {
            "current_question": profile_service.prompt_for_state(current_step, catalog),
            "expected_input_type": "birth_year_button",
            "allowed_value_shape": "button_selection:1900_to_current_year",
            "hard_constraints": (
                "birth_year_must_be_between_1900_and_current_year",
            ),
        }

    if current_step == STATE_PROFILE_BIRTH_MONTH:
        return {
            "current_question": profile_service.prompt_for_state(current_step, catalog),
            "expected_input_type": "birth_month_button",
            "allowed_value_shape": "button_selection:1_to_12",
            "hard_constraints": (
                "birth_month_requires_birth_year",
            ),
        }

    if current_step == STATE_PROFILE_BIRTH_DAY:
        return {
            "current_question": profile_service.prompt_for_state(current_step, catalog),
            "expected_input_type": "birth_day_button",
            "allowed_value_shape": "button_selection:valid_day_for_selected_year_month",
            "hard_constraints": (
                "birth_day_requires_birth_year_and_birth_month",
            ),
        }

    if current_step == STATE_PROFILE_CONFIRM:
        return {
            "current_question": profile_service.confirmation_text(draft, catalog),
            "expected_input_type": "confirmation_action",
            "allowed_value_shape": "one_of:confirm|edit",
            "hard_constraints": (
                "all_profile_fields_must_be_present_before_finalize",
            ),
        }

    if current_step == STATE_PROFILE_EDIT_SELECT:
        return {
            "current_question": profile_service.edit_selection_text(draft, catalog),
            "expected_input_type": "profile_edit_field_selection",
            "allowed_value_shape": "one_of:name|residence|city|district|birth_date",
            "hard_constraints": (
                "selected_field_must_be_supported_profile_field",
            ),
        }

    return {
        "current_question": sample_service.main_menu_text(catalog),
        "expected_input_type": "unknown",
        "allowed_value_shape": "unknown",
        "hard_constraints": (),
    }


def _summarize_session(
    *,
    current_step: str,
    profile_draft_data: dict | None,
    fertilizer_draft_data: dict | None,
    confirmed_profile_data: dict | None,
    pending_slot: str | None,
    selected_city: str | None,
) -> str:
    summary_parts = [f"state={current_step}"]
    if pending_slot is not None:
        summary_parts.append(f"pending_slot={pending_slot}")
    if selected_city is not None:
        summary_parts.append(f"selected_city={selected_city}")

    draft = profile_service.draft_from_dict(profile_draft_data)
    filled_fields = []
    if draft.name:
        filled_fields.append("name")
    if draft.residence:
        filled_fields.append("residence")
    if draft.city:
        filled_fields.append("city")
    if draft.district:
        filled_fields.append("district")
    if draft.birth_date:
        filled_fields.append("birth_date")
    if filled_fields:
        summary_parts.append(f"profile_draft_fields={','.join(filled_fields)}")

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

    if confirmed_profile_data:
        confirmed = profile_service.draft_from_dict(confirmed_profile_data)
        confirmed_fields = []
        if confirmed.name:
            confirmed_fields.append("name")
        if confirmed.residence:
            confirmed_fields.append("residence")
        if confirmed.city:
            confirmed_fields.append("city")
        if confirmed.district:
            confirmed_fields.append("district")
        if confirmed.birth_date:
            confirmed_fields.append("birth_date")
        summary_parts.append(f"confirmed_profile_fields={','.join(confirmed_fields)}")

    return "; ".join(summary_parts)
