import httpx

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.canonical_intents.mapping import command_to_intent, text_to_intent
from PROJECT.canonical_intents import registry
from PROJECT.canonical_intents.registry import INTENT_UNKNOWN_COMMAND
from PROJECT.channels.telegram.parser import parse_update
from PROJECT.channels.telegram.handlers.commands import (
    cancel_command,
    help_command,
    input_resolve_command,
    open_fertilizer_edit_selector,
    menu_command,
    myfields_command,
    open_fertilizer_target_edit,
    open_profile_edit_selector,
    open_profile_target_edit,
    show_support_guidance,
    show_current_profile,
    start_fertilizer_input,
    start_profile_input,
    start_yield_input,
)
from PROJECT.conversations.fertilizer_intake import service as fertilizer_service
from PROJECT.conversations.fertilizer_intake import keyboards as fertilizer_keyboards
from PROJECT.conversations.fertilizer_intake.states import (
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_CONFIRM,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_USED,
)
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
from PROJECT.conversations.yield_intake import service as yield_service
from PROJECT.conversations.yield_intake.states import (
    STATE_YIELD_AMOUNT,
    STATE_YIELD_CONFIRM,
    STATE_YIELD_DATE,
    STATE_YIELD_EDIT_SELECT,
    STATE_YIELD_FIELD,
    STATE_YIELD_READY,
)
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import (
    fallback_keyboard_layout_for_state,
    keyboard_layout_for_state,
    repair_confirmation_keyboard,
)
from PROJECT.conversations.sample_menu.states import STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.dispatch.command_router import (
    ROUTE_CANCEL,
    ROUTE_FERTILIZER_FINALIZE,
    ROUTE_GO_BACK,
    ROUTE_HELP,
    ROUTE_MAIN_MENU,
    ROUTE_OPEN_FERTILIZER,
    ROUTE_OPEN_INPUT_RESOLVE,
    ROUTE_OPEN_MYFIELDS,
    ROUTE_OPEN_PROFILE,
    ROUTE_OPEN_YIELD,
    ROUTE_PROFILE_EDIT,
    ROUTE_PROFILE_FINALIZE,
    ROUTE_SUPPORT_GUIDANCE,
    ROUTE_YIELD_EDIT,
    ROUTE_YIELD_FINALIZE,
    route_message,
)
from PROJECT.dispatch.input_fallback import fallback_key_for_state
from PROJECT.dispatch.repair_router import detect_profile_view_intent, detect_repair_intent
from PROJECT.dispatch.session_dispatcher import (
    clear_pending_candidate,
    cancel_session,
    confirmed_fertilizer,
    confirmed_profile,
    confirmed_yield,
    current_locale,
    current_state,
    fertilizer_draft,
    go_back,
    has_active_support_handoff,
    has_confirmed_fertilizer,
    has_confirmed_profile,
    has_seen_llm_input,
    increment_llm_calls_in_step,
    increment_recovery_attempts,
    last_recovery_context,
    llm_calls_in_step,
    mark_llm_input_seen,
    pending_candidate,
    pending_repair_confirmation,
    pending_slot,
    profile_draft,
    recovery_attempts,
    reset_session,
    reset_recovery_attempts,
    set_confirmed_fertilizer,
    set_confirmed_yield,
    set_fertilizer_draft,
    set_last_recovery_context,
    set_confirmed_profile,
    set_locale,
    set_pending_candidate,
    set_pending_repair_confirmation,
    set_pending_slot,
    set_profile_draft,
    set_state,
    set_yield_draft,
    yield_draft,
)
from PROJECT.dispatch.support_handoff_dispatcher import close_support_handoff, create_support_handoff_request, record_support_handoff_user_message
from PROJECT.i18n.translator import get_catalog, language_keyboard, resolve_language_choice
from PROJECT.llm import GeminiNotConfiguredError, GeminiRecoveryError, GeminiResponseFormatError, LlmEditAction, LlmEditIntentResult
from PROJECT.policy import (
    HandoffRoute,
    UnknownInputDisposition,
    classify_handoff_route,
    evaluate_llm_invocation_policy,
    evaluate_unknown_input_policy,
)
from PROJECT.rule_engine import (
    ValidationClassification,
    assemble_recovery_context,
    classify_cheap_gate,
    detect_fertilizer_direct_update,
    detect_profile_direct_update,
    extract_birth_date_candidate,
    extract_korean_name_candidate,
)
from PROJECT.rule_engine.normalizer import normalize_body_text
from PROJECT.policy import same_input_cache_key
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import (
    CHEAP_GATE_BLOCKED,
    FALLBACK_SHOWN,
    LLM_FAILED,
    HANDOFF_REQUESTED,
    LLM_INVOKED,
    LLM_REPAIR_GUIDANCE_SHOWN,
    LLM_REJECTED_LOW_CONFIDENCE,
    LLM_REPAIR_SIGNAL_DETECTED,
    LLM_SKIPPED_BY_POLICY,
    PENDING_CANDIDATE_CONFIRMED,
    PENDING_CANDIDATE_CREATED,
    PENDING_CANDIDATE_DISCARDED,
    RECOVERY_ACTION_SELECTED,
    RECOVERY_CLASSIFIED,
    REPAIR_CANDIDATE_APPLIED,
    RULE_MATCHED,
    RULE_REPAIR_SIGNAL_DETECTED,
)

PROFILE_STATES = {
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
    STATE_PROFILE_CITY,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_EDIT_SELECT,
}

FERTILIZER_STATES = {
    STATE_FERTILIZER_USED,
    STATE_FERTILIZER_KIND,
    STATE_FERTILIZER_PRODUCT,
    STATE_FERTILIZER_AMOUNT,
    STATE_FERTILIZER_DATE,
    STATE_FERTILIZER_CONFIRM,
}

YIELD_STATES = {
    STATE_YIELD_READY,
    STATE_YIELD_FIELD,
    STATE_YIELD_AMOUNT,
    STATE_YIELD_DATE,
    STATE_YIELD_CONFIRM,
    STATE_YIELD_EDIT_SELECT,
}

PROFILE_EDIT_CALLBACK_TO_STATE = {
    "name": STATE_PROFILE_NAME,
    "residence": STATE_PROFILE_RESIDENCE,
    "city": STATE_PROFILE_CITY,
    "district": STATE_PROFILE_DISTRICT,
    "birth_date": STATE_PROFILE_BIRTH_YEAR,
}

FERTILIZER_EDIT_CALLBACK_TO_STATE = {
    "used": STATE_FERTILIZER_USED,
    "kind": STATE_FERTILIZER_KIND,
    "product": STATE_FERTILIZER_PRODUCT,
    "amount": STATE_FERTILIZER_AMOUNT,
    "date": STATE_FERTILIZER_DATE,
}

YIELD_EDIT_CALLBACK_TO_STATE = {
    "ready": STATE_YIELD_READY,
    "field": STATE_YIELD_FIELD,
    "amount": STATE_YIELD_AMOUNT,
    "date": STATE_YIELD_DATE,
}

LLM_EDIT_ACTION_TO_TARGET = {
    LlmEditAction.PROFILE_EDIT_SELECT.value: ("profile", STATE_PROFILE_EDIT_SELECT),
    LlmEditAction.PROFILE_EDIT_NAME.value: ("profile", STATE_PROFILE_NAME),
    LlmEditAction.PROFILE_EDIT_RESIDENCE.value: ("profile", STATE_PROFILE_RESIDENCE),
    LlmEditAction.PROFILE_EDIT_CITY.value: ("profile", STATE_PROFILE_CITY),
    LlmEditAction.PROFILE_EDIT_DISTRICT.value: ("profile", STATE_PROFILE_DISTRICT),
    LlmEditAction.PROFILE_EDIT_BIRTH_DATE.value: ("profile", STATE_PROFILE_BIRTH_YEAR),
    LlmEditAction.FERTILIZER_EDIT_SELECT.value: ("fertilizer", STATE_FERTILIZER_CONFIRM),
    LlmEditAction.FERTILIZER_EDIT_USED.value: ("fertilizer", STATE_FERTILIZER_USED),
    LlmEditAction.FERTILIZER_EDIT_KIND.value: ("fertilizer", STATE_FERTILIZER_KIND),
    LlmEditAction.FERTILIZER_EDIT_PRODUCT.value: ("fertilizer", STATE_FERTILIZER_PRODUCT),
    LlmEditAction.FERTILIZER_EDIT_AMOUNT.value: ("fertilizer", STATE_FERTILIZER_AMOUNT),
    LlmEditAction.FERTILIZER_EDIT_DATE.value: ("fertilizer", STATE_FERTILIZER_DATE),
}

LLM_MIN_CONFIDENCE = 0.6
PROFILE_REPAIR_ALLOWED_ACTIONS = (
    LlmEditAction.PROFILE_EDIT_SELECT.value,
    LlmEditAction.PROFILE_EDIT_NAME.value,
    LlmEditAction.PROFILE_EDIT_RESIDENCE.value,
    LlmEditAction.PROFILE_EDIT_CITY.value,
    LlmEditAction.PROFILE_EDIT_DISTRICT.value,
    LlmEditAction.PROFILE_EDIT_BIRTH_DATE.value,
    LlmEditAction.UNSUPPORTED.value,
)
FERTILIZER_REPAIR_ALLOWED_ACTIONS = (
    LlmEditAction.FERTILIZER_EDIT_SELECT.value,
    LlmEditAction.FERTILIZER_EDIT_USED.value,
    LlmEditAction.FERTILIZER_EDIT_KIND.value,
    LlmEditAction.FERTILIZER_EDIT_PRODUCT.value,
    LlmEditAction.FERTILIZER_EDIT_AMOUNT.value,
    LlmEditAction.FERTILIZER_EDIT_DATE.value,
    LlmEditAction.UNSUPPORTED.value,
)
EDIT_INTENT_HINT_MARKERS = (
    "수정",
    "변경",
    "고쳐",
    "바꾸",
    "잘못",
    "틀렸",
    "edit",
    "change",
    "wrong",
)
HANDOFF_SAFE_EXIT_INTENTS = {
    registry.INTENT_START,
    registry.INTENT_MENU,
    registry.INTENT_RESTART,
    registry.INTENT_CANCEL,
}


def current_catalog(context):
    return get_catalog(current_locale(context.user_data))


def current_profile(context) -> profile_service.ProfileDraft:
    return profile_service.draft_from_dict(profile_draft(context.user_data))


def current_fertilizer(context) -> fertilizer_service.FertilizerDraft:
    return fertilizer_service.draft_from_dict(fertilizer_draft(context.user_data))


def confirmed_profile_draft(context) -> profile_service.ProfileDraft:
    return profile_service.draft_from_dict(confirmed_profile(context.user_data))


def confirmed_fertilizer_draft(context) -> fertilizer_service.FertilizerDraft:
    return fertilizer_service.draft_from_dict(confirmed_fertilizer(context.user_data))


def current_yield(context) -> yield_service.YieldDraft:
    return yield_service.draft_from_dict(yield_draft(context.user_data))


def log_rule_matched(*, rule_name: str, domain: str, target_state: str, scope: str) -> None:
    log_event(
        RULE_MATCHED,
        rule_name=rule_name,
        domain=domain,
        target_state=target_state,
        scope=scope,
    )


def log_recovery_classification_event(recovery_context, *, source: str) -> None:
    metadata = recovery_context.metadata if hasattr(recovery_context, "metadata") else recovery_context.get("metadata", {})
    current_step = recovery_context.current_step if hasattr(recovery_context, "current_step") else recovery_context.get("current_step")
    log_event(
        RECOVERY_CLASSIFIED,
        source=source,
        state=current_step,
        recovery_reason=metadata.get("ux_recovery_reason"),
        policy_level=metadata.get("recovery_policy_level"),
        task_hint=metadata.get("recovery_task_hint"),
        resume_action=metadata.get("recovery_resume_action"),
    )


def log_recovery_action_event(
    *,
    action: str,
    domain: str,
    target_state: str,
    scope: str,
    has_candidate: bool,
    slot_count: int = 0,
) -> None:
    log_event(
        RECOVERY_ACTION_SELECTED,
        action=action,
        domain=domain,
        target_state=target_state,
        scope=scope,
        has_candidate=has_candidate,
        slot_count=slot_count,
    )


def handoff_route_for_validation(*, reason: str | None, human_handoff_reason: str | None, source: str) -> HandoffRoute:
    return classify_handoff_route(
        reason=reason,
        human_handoff_reason=human_handoff_reason,
        source=source,
    )


def create_handoff_request_from_runtime(
    update,
    context,
    *,
    route_hint: HandoffRoute,
    reason: str,
    current_step: str | None,
    user_message: str,
    failure_count: int = 0,
    recent_messages_summary: str = "",
    source: str,
) -> None:
    create_support_handoff_request(
        context.user_data,
        route_hint=route_hint.value,
        reason=reason,
        current_step=current_step,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        user_id=update.effective_user.id if update.effective_user else None,
        locale=current_locale(context.user_data),
        user_message=user_message,
        failure_count=failure_count,
        recent_messages_summary=recent_messages_summary,
        source=source,
    )


def discard_pending_candidate(context, *, reason: str) -> None:
    candidate = pending_candidate(context.user_data)
    if candidate is not None:
        log_event(
            PENDING_CANDIDATE_DISCARDED,
            reason=reason,
            domain=candidate.get("domain"),
            target_state=candidate.get("target_state"),
            scope=candidate.get("scope"),
            source=candidate.get("source"),
        )
    clear_pending_candidate(context.user_data)


async def send_profile_prompt(update, context, state: str, text: str | None = None) -> None:
    catalog = current_catalog(context)
    draft = current_profile(context)
    await send_text(
        update,
        text or profile_service.prompt_for_state(state, catalog),
        keyboard_layout=profile_service.keyboard_for_state(state, draft, catalog),
    )


async def send_profile_confirmation(update, context) -> None:
    catalog = current_catalog(context)
    draft = current_profile(context)
    await send_text(
        update,
        profile_service.confirmation_text(draft, catalog),
        keyboard_layout=profile_service.keyboard_for_state(STATE_PROFILE_CONFIRM, draft, catalog),
    )


async def send_fertilizer_prompt(update, context, state: str, text: str | None = None) -> None:
    catalog = current_catalog(context)
    await send_text(
        update,
        text or fertilizer_service.prompt_for_state(state, catalog),
        keyboard_layout=fertilizer_service.keyboard_for_state(state, catalog),
    )


async def send_fertilizer_confirmation(update, context) -> None:
    catalog = current_catalog(context)
    draft = current_fertilizer(context)
    await send_text(
        update,
        fertilizer_service.confirmation_text(draft, catalog),
        keyboard_layout=fertilizer_service.keyboard_for_state(STATE_FERTILIZER_CONFIRM, catalog),
    )


async def send_yield_prompt(update, context, state: str, text: str | None = None) -> None:
    await send_text(
        update,
        text or yield_service.prompt_for_state(state, current_catalog(context)),
        keyboard_layout=yield_service.keyboard_for_state(state, current_catalog(context)),
    )


async def send_yield_confirmation(update, context) -> None:
    await send_text(
        update,
        yield_service.confirmation_text(current_yield(context), current_catalog(context)),
        keyboard_layout=yield_service.keyboard_for_state(STATE_YIELD_CONFIRM, current_catalog(context)),
    )


async def open_current_profile_edit_selector(update, context) -> None:
    catalog = current_catalog(context)
    set_pending_slot(context.user_data, None)
    set_state(context.user_data, STATE_PROFILE_EDIT_SELECT)
    await send_text(
        update,
        profile_service.edit_selection_text(current_profile(context), catalog),
        keyboard_layout=profile_service.keyboard_for_state(STATE_PROFILE_EDIT_SELECT, current_profile(context), catalog),
    )


async def open_current_profile_target_edit(update, context, target_state: str) -> None:
    catalog = current_catalog(context)
    draft = profile_service.reset_draft_for_repair(current_profile(context), target_state)
    set_profile_draft(context.user_data, draft.to_dict())
    if current_state(context.user_data) in {STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT}:
        set_pending_slot(context.user_data, target_state)
    else:
        set_pending_slot(context.user_data, None)
    set_state(context.user_data, target_state)
    await send_text(
        update,
        profile_service.repair_message(target_state, catalog),
        keyboard_layout=profile_service.keyboard_for_state(target_state, draft, catalog),
    )


async def open_current_fertilizer_edit_selector(update, context) -> None:
    catalog = current_catalog(context)
    set_state(context.user_data, STATE_FERTILIZER_CONFIRM)
    await send_text(
        update,
        fertilizer_service.edit_selection_text(current_fertilizer(context), catalog),
        keyboard_layout=fertilizer_keyboards.fertilizer_edit_select_keyboard(catalog),
    )


async def open_current_fertilizer_target_edit(update, context, target_state: str) -> None:
    draft = fertilizer_service.reset_draft_for_repair(current_fertilizer(context), target_state)
    set_fertilizer_draft(context.user_data, draft.to_dict())
    set_state(context.user_data, target_state)
    await send_text(
        update,
        fertilizer_service.repair_message(target_state, current_catalog(context)),
        keyboard_layout=fertilizer_service.keyboard_for_state(target_state, current_catalog(context)),
    )


def parse_profile_candidate_changes(target_state: str, candidate_value: str) -> dict | None:
    if target_state == STATE_PROFILE_NAME:
        name = profile_service.parse_name(candidate_value)
        return {"name": name} if name is not None else None
    if target_state == STATE_PROFILE_RESIDENCE:
        residence = profile_service.parse_free_text(candidate_value)
        return {"residence": residence} if residence is not None else None
    if target_state == STATE_PROFILE_CITY:
        city = profile_service.parse_free_text(candidate_value)
        return {"city": city} if city is not None else None
    if target_state == STATE_PROFILE_DISTRICT:
        district = profile_service.parse_free_text(candidate_value)
        return {"district": district} if district is not None else None
    if target_state == STATE_PROFILE_BIRTH_YEAR:
        birth_date = profile_service.parse_birth_date_text(candidate_value)
        if birth_date is None:
            return None
        return {
            "birth_year": birth_date[0],
            "birth_month": birth_date[1],
            "birth_day": birth_date[2],
        }
    return None


def parse_fertilizer_candidate_changes(target_state: str, candidate_value: str) -> dict | None:
    if target_state == STATE_FERTILIZER_USED:
        used = fertilizer_service.parse_used(candidate_value)
        return {"used": used} if used is not None else None
    if target_state == STATE_FERTILIZER_KIND:
        kind = fertilizer_service.parse_kind(candidate_value)
        return {"kind": kind} if kind is not None else None
    if target_state == STATE_FERTILIZER_PRODUCT:
        product_name = fertilizer_service.parse_product_name(candidate_value)
        return {"product_name": product_name} if product_name is not None else None
    if target_state == STATE_FERTILIZER_AMOUNT:
        amount = fertilizer_service.parse_amount(candidate_value)
        if amount is None:
            return None
        return {"amount_value": amount[0], "amount_unit": amount[1]}
    if target_state == STATE_FERTILIZER_DATE:
        applied_date = fertilizer_service.parse_applied_date(candidate_value)
        return {"applied_date": applied_date} if applied_date is not None else None
    return None


def parse_candidate_changes(domain: str, target_state: str, candidate_value: str | None) -> dict | None:
    if not candidate_value:
        return None
    if domain == "profile":
        return parse_profile_candidate_changes(target_state, candidate_value)
    if domain == "fertilizer":
        return parse_fertilizer_candidate_changes(target_state, candidate_value)
    return None


def candidate_changes_from_payload(payload: dict | None) -> dict | None:
    if payload is None:
        return None
    structured_changes = payload.get("candidate_changes")
    if isinstance(structured_changes, dict) and structured_changes:
        return structured_changes
    return parse_candidate_changes(
        payload.get("domain", ""),
        payload.get("target_state", ""),
        payload.get("candidate_value"),
    )


def logical_slot_count(changes: dict) -> int:
    grouped_slots: set[str] = set()
    for key in changes:
        if key in {"birth_year", "birth_month", "birth_day"}:
            grouped_slots.add("birth_date")
        elif key in {"amount_value", "amount_unit"}:
            grouped_slots.add("amount")
        else:
            grouped_slots.add(key)
    return len(grouped_slots)


def extract_profile_multi_slot_candidate_changes(text: str) -> dict | None:
    changes: dict[str, object] = {}
    birth_candidate, remaining = extract_birth_date_candidate(text)
    if birth_candidate is not None:
        year, month, day = map(int, str(birth_candidate.normalized_value).split("-"))
        changes.update({"birth_year": year, "birth_month": month, "birth_day": day})

    name_candidate, _ = extract_korean_name_candidate(remaining)
    if name_candidate is not None:
        changes["name"] = str(name_candidate.normalized_value)

    return changes if logical_slot_count(changes) >= 2 else None


def extract_fertilizer_multi_slot_candidate_changes(text: str) -> dict | None:
    changes: dict[str, object] = {}
    normalized = normalize_body_text(text)
    if any(alias in normalized for alias in fertilizer_service.YES_ALIASES):
        changes["used"] = True
    elif any(alias in normalized for alias in fertilizer_service.NO_ALIASES):
        changes["used"] = False

    for kind_key, aliases in fertilizer_service.KIND_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            changes["kind"] = kind_key
            break

    amount = fertilizer_service.parse_amount(text)
    if amount is not None:
        changes["amount_value"] = amount[0]
        changes["amount_unit"] = amount[1]

    if "어제" in normalized or "yesterday" in normalized:
        applied_date = fertilizer_service.parse_applied_date("어제")
    elif "오늘" in normalized or "today" in normalized:
        applied_date = fertilizer_service.parse_applied_date("오늘")
    else:
        applied_date = fertilizer_service.parse_applied_date(text)
    if applied_date is not None:
        changes["applied_date"] = applied_date

    correction_pattern = detect_fertilizer_direct_update(text, allow_implicit=True)
    if correction_pattern is not None and correction_pattern.target_state == STATE_FERTILIZER_PRODUCT:
        changes.update(correction_pattern.changes)

    return changes if logical_slot_count(changes) >= 2 else None


def repair_candidate_preview_text(context, *, domain: str, target_state: str, changes: dict, use_confirmed: bool) -> str:
    catalog = current_catalog(context)
    if domain == "profile":
        base_draft = confirmed_profile_draft(context) if use_confirmed else current_profile(context)
        updated = profile_service.update_draft(base_draft, **changes)
        if logical_slot_count(changes) >= 2:
            return f"{catalog.RECOVERY_MULTI_SLOT_CANDIDATE_HINT}\n\n{profile_service.summary_text(updated, catalog)}"
        return profile_service.change_preview_text(base_draft, updated, target_state, catalog)

    base_draft = confirmed_fertilizer_draft(context) if use_confirmed else current_fertilizer(context)
    updated = fertilizer_service.update_draft(base_draft, **changes)
    if target_state == STATE_FERTILIZER_USED and changes.get("used") is False:
        updated = fertilizer_service.update_draft(
            updated,
            kind="",
            product_name="",
            amount_value=None,
            amount_unit="",
            applied_date="",
        )
    if logical_slot_count(changes) >= 2:
        return f"{catalog.RECOVERY_MULTI_SLOT_CANDIDATE_HINT}\n\n{fertilizer_service.summary_text(updated, catalog)}"
    return fertilizer_service.change_preview_text(base_draft, updated, target_state, catalog)


async def continue_repair_flow(update, context, *, domain: str, target_state: str, use_confirmed: bool) -> None:
    discard_pending_candidate(context, reason="repair_flow_continued")
    if domain == "profile":
        if use_confirmed:
            if target_state == STATE_PROFILE_EDIT_SELECT:
                await open_profile_edit_selector(update, context)
            else:
                await open_profile_target_edit(update, context, target_state)
            return
        if target_state == STATE_PROFILE_EDIT_SELECT:
            await open_current_profile_edit_selector(update, context)
        else:
            await open_current_profile_target_edit(update, context, target_state)
        return

    if use_confirmed:
        if target_state == STATE_FERTILIZER_CONFIRM:
            await open_fertilizer_edit_selector(update, context)
        else:
            await open_fertilizer_target_edit(update, context, target_state)
        return
    if target_state == STATE_FERTILIZER_CONFIRM:
        await open_current_fertilizer_edit_selector(update, context)
    else:
        await open_current_fertilizer_target_edit(update, context, target_state)


async def apply_profile_changes(update, context, *, changes: dict, use_confirmed: bool) -> None:
    base_draft = confirmed_profile_draft(context) if use_confirmed else current_profile(context)
    updated = profile_service.update_draft(base_draft, **changes)
    target_state = next(iter(changes.keys()), "")
    state_by_change = {
        "name": STATE_PROFILE_NAME,
        "residence": STATE_PROFILE_RESIDENCE,
        "city": STATE_PROFILE_CITY,
        "district": STATE_PROFILE_DISTRICT,
        "birth_year": STATE_PROFILE_BIRTH_YEAR,
    }
    if logical_slot_count(changes) >= 2:
        preview_text = current_catalog(context).RECOVERY_MULTI_SLOT_APPLIED_MESSAGE
    else:
        preview_text = profile_service.change_preview_text(
            base_draft,
            updated,
            state_by_change.get(target_state, STATE_PROFILE_EDIT_SELECT),
            current_catalog(context),
        )

    if use_confirmed:
        reset_session(context.user_data)
    set_profile_draft(context.user_data, updated.to_dict())
    set_pending_slot(context.user_data, None)
    set_state(context.user_data, STATE_PROFILE_CONFIRM)
    await send_text(
        update,
        f"{preview_text}\n\n{profile_service.confirmation_text(updated, current_catalog(context))}",
        keyboard_layout=profile_service.keyboard_for_state(STATE_PROFILE_CONFIRM, updated, current_catalog(context)),
    )
    log_event(
        PENDING_CANDIDATE_CONFIRMED,
        domain="profile",
        target_state=state_by_change.get(target_state, STATE_PROFILE_EDIT_SELECT),
        scope="confirmed" if use_confirmed else "draft",
    )
    log_event(
        REPAIR_CANDIDATE_APPLIED,
        domain="profile",
        target_state=state_by_change.get(target_state, STATE_PROFILE_EDIT_SELECT),
        scope="confirmed" if use_confirmed else "draft",
    )


async def apply_fertilizer_changes(update, context, *, target_state: str, changes: dict, use_confirmed: bool) -> None:
    base_draft = confirmed_fertilizer_draft(context) if use_confirmed else current_fertilizer(context)
    updated = fertilizer_service.update_draft(base_draft, **changes)

    if target_state == STATE_FERTILIZER_USED and changes.get("used") is False:
        updated = fertilizer_service.update_draft(
            updated,
            kind="",
            product_name="",
            amount_value=None,
            amount_unit="",
            applied_date="",
        )

    if use_confirmed:
        reset_session(context.user_data)
    set_fertilizer_draft(context.user_data, updated.to_dict())
    set_state(context.user_data, STATE_FERTILIZER_CONFIRM)
    if logical_slot_count(changes) >= 2 or target_state == STATE_FERTILIZER_CONFIRM:
        preview_text = current_catalog(context).RECOVERY_MULTI_SLOT_APPLIED_MESSAGE
    else:
        preview_text = fertilizer_service.change_preview_text(base_draft, updated, target_state, current_catalog(context))
    await send_text(
        update,
        f"{preview_text}\n\n{fertilizer_service.confirmation_text(updated, current_catalog(context))}",
        keyboard_layout=fertilizer_service.keyboard_for_state(STATE_FERTILIZER_CONFIRM, current_catalog(context)),
    )
    log_event(
        PENDING_CANDIDATE_CONFIRMED,
        domain="fertilizer",
        target_state=target_state,
        scope="confirmed" if use_confirmed else "draft",
    )
    log_event(
        REPAIR_CANDIDATE_APPLIED,
        domain="fertilizer",
        target_state=target_state,
        scope="confirmed" if use_confirmed else "draft",
    )


async def send_repair_confirmation(
    update,
    context,
    *,
    domain: str,
    target_state: str,
    use_confirmed: bool,
    candidate_value: str | None = None,
    candidate_changes: dict | None = None,
    candidate_source: str = "rule",
) -> None:
    catalog = current_catalog(context)
    scope = "confirmed" if use_confirmed else "draft"
    if domain == "profile":
        text = profile_service.repair_confirmation_text(target_state, catalog)
    else:
        text = fertilizer_service.repair_confirmation_text(target_state, catalog)
    parsed_candidate = candidate_changes or parse_candidate_changes(domain, target_state, candidate_value)
    if parsed_candidate is not None:
        preview_text = repair_candidate_preview_text(
            context,
            domain=domain,
            target_state=target_state,
            changes=parsed_candidate,
            use_confirmed=use_confirmed,
        )
        text = f"{text}\n\n{preview_text}"
        set_pending_candidate(
            context.user_data,
            {
                "domain": domain,
                "scope": scope,
                "target_state": target_state,
                "candidate_value": candidate_value,
                "candidate_changes": parsed_candidate,
                "source": candidate_source,
            },
        )
        log_event(
            PENDING_CANDIDATE_CREATED,
            domain=domain,
            target_state=target_state,
            scope=scope,
            source=candidate_source,
        )
        set_pending_repair_confirmation(
            context.user_data,
            {
                "domain": domain,
                "scope": scope,
                "target_state": target_state,
                "has_candidate": True,
            },
        )
    else:
        set_pending_repair_confirmation(context.user_data, None)
        discard_pending_candidate(context, reason="no_valid_candidate")
    await send_text(
        update,
        text,
        keyboard_layout=repair_confirmation_keyboard(
            domain,
            scope,
            target_state,
            catalog,
            has_candidate=parsed_candidate is not None,
        ),
    )
    log_event(
        RULE_REPAIR_SIGNAL_DETECTED,
        domain=domain,
        target_state=target_state,
        scope=scope,
        has_candidate=parsed_candidate is not None,
    )
    log_recovery_action_event(
        action="repair_confirmation_shown",
        domain=domain,
        target_state=target_state,
        scope=scope,
        has_candidate=parsed_candidate is not None,
        slot_count=logical_slot_count(parsed_candidate) if parsed_candidate is not None else 0,
    )


def llm_repair_guidance_text(result: LlmEditIntentResult, catalog) -> str | None:
    if result.needs_human:
        return catalog.LLM_REPAIR_HUMAN_REVIEW_MESSAGE
    if result.action == LlmEditAction.UNSUPPORTED:
        return catalog.LLM_REPAIR_UNSUPPORTED_MESSAGE
    if result.confidence is None or result.confidence < LLM_MIN_CONFIDENCE:
        return catalog.LLM_REPAIR_LOW_CONFIDENCE_MESSAGE
    if result.clarification_question:
        return result.clarification_question
    return None


def classify_llm_runtime_failure(exc: Exception) -> str:
    if isinstance(exc, GeminiNotConfiguredError):
        return "not_configured"
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, GeminiResponseFormatError):
        return "response_format_error"
    if isinstance(exc, httpx.HTTPStatusError):
        return "http_status_error"
    if isinstance(exc, httpx.RequestError):
        return "network_error"
    if isinstance(exc, ValueError):
        return "schema_validation_error"
    if isinstance(exc, GeminiRecoveryError):
        return "runtime_error"
    return "unexpected_error"


def llm_edit_intent_policy_enabled(context) -> bool:
    settings = context.bot_data.get("settings")
    return bool(getattr(settings, "enable_llm_edit_intent", False))


def llm_edit_intent_policy_skip_reason(context) -> str:
    settings = context.bot_data.get("settings")
    if settings is None:
        return "edit_intent_policy_disabled"
    if getattr(settings, "manual_review_fallback_active", False):
        return "manual_review_fallback_active"
    if getattr(settings, "runtime_rules_only", False):
        return "local_ai_gate_disabled"
    return "edit_intent_policy_disabled"


def repair_allowed_actions(domain: str) -> tuple[str, ...]:
    if domain == "profile":
        return PROFILE_REPAIR_ALLOWED_ACTIONS
    if domain == "fertilizer":
        return FERTILIZER_REPAIR_ALLOWED_ACTIONS
    raise ValueError(f"지원하지 않는 repair domain 입니다: {domain}")


async def maybe_send_llm_repair_confirmation(
    update,
    context,
    *,
    text: str,
    allowed_actions: tuple[str, ...],
    use_confirmed: bool,
    policy_scope: str | None = None,
    unknown_policy_reason: str | None = None,
) -> bool:
    resolver = context.bot_data.get("gemini_edit_intent_resolver")
    state = current_state(context.user_data)
    normalized_text = normalize_body_text(text)
    cache_key = same_input_cache_key(
        normalized_text=normalized_text,
        current_step=state,
        locale=current_locale(context.user_data),
    )
    lowered = text.strip().lower()
    if resolver is None or not lowered:
        return False
    if not llm_edit_intent_policy_enabled(context):
        log_event(
            LLM_SKIPPED_BY_POLICY,
            invocation_type="repair",
            state=state,
            reason="edit_intent_policy_disabled",
        )
        return False
    if not any(marker in lowered for marker in EDIT_INTENT_HINT_MARKERS):
        return False
    same_input_seen = has_seen_llm_input(context.user_data, cache_key)
    llm_call_count = llm_calls_in_step(context.user_data, state)
    policy_decision = evaluate_llm_invocation_policy(
        local_ai_gate=context.bot_data["settings"].local_ai_gate,
        invocation_type="repair",
        current_step=state,
        is_structured_step=state in PROFILE_STATES or state in FERTILIZER_STATES,
        is_confirm_step=use_confirmed or state in {STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT, STATE_FERTILIZER_CONFIRM},
        is_free_text=True,
        llm_calls_in_step=llm_call_count,
        same_input_seen=same_input_seen,
    )
    if not policy_decision.allowed:
        log_event(
            LLM_SKIPPED_BY_POLICY,
            invocation_type="repair",
            state=state,
            reason=policy_decision.reason,
        )
        return False

    mark_llm_input_seen(context.user_data, cache_key)
    increment_llm_calls_in_step(context.user_data, state)
    log_event(
        LLM_INVOKED,
        invocation_type="repair",
        state=state,
        scope="confirmed" if use_confirmed else "draft",
        policy_scope=policy_scope,
        policy_reason=unknown_policy_reason,
    )

    try:
        result = await resolver.classify(
            text=text,
            locale=current_locale(context.user_data),
            allowed_actions=allowed_actions,
        )
    except Exception as exc:
        failure_reason = classify_llm_runtime_failure(exc)
        fallback_key = fallback_key_for_state(state)
        log_event(
            LLM_FAILED,
            invocation_type="repair",
            state=state,
            failure_reason=failure_reason,
            policy_scope=policy_scope,
            policy_reason=unknown_policy_reason,
        )
        await send_text(
            update,
            current_catalog(context).LLM_REPAIR_RUNTIME_FAILURE_MESSAGE,
            keyboard_layout=fallback_keyboard_layout_for_state(
                current_state(context.user_data),
                current_catalog(context),
                profile_draft(context.user_data),
            ),
        )
        log_event(
            FALLBACK_SHOWN,
            source="llm_runtime_failure",
            state=state,
            fallback_key=fallback_key,
            failure_reason=failure_reason,
        )
        return True

    guidance_text = llm_repair_guidance_text(result, current_catalog(context))
    if guidance_text is not None and (
        result.needs_human
        or result.action == LlmEditAction.UNSUPPORTED
        or result.confidence is None
        or result.confidence < LLM_MIN_CONFIDENCE
        or result.clarification_question is not None
    ):
        await send_text(
            update,
            guidance_text,
            keyboard_layout=fallback_keyboard_layout_for_state(
                current_state(context.user_data),
                current_catalog(context),
                profile_draft(context.user_data),
            ),
        )
        reason = (
            "needs_human" if result.needs_human else
            "unsupported" if result.action == LlmEditAction.UNSUPPORTED else
            "low_confidence" if result.confidence is None or result.confidence < LLM_MIN_CONFIDENCE else
            "clarification"
        )
        if result.confidence is None or result.confidence < LLM_MIN_CONFIDENCE:
            log_event(
                LLM_REJECTED_LOW_CONFIDENCE,
                invocation_type="repair",
                state=state,
                confidence=result.confidence,
            )
        if result.needs_human:
            handoff_route = classify_handoff_route(
                reason=result.reason or "needs_human",
                source="llm_repair",
            )
            create_handoff_request_from_runtime(
                update,
                context,
                route_hint=handoff_route,
                reason=result.reason or "needs_human",
                current_step=state,
                user_message=text,
                source="llm_repair",
            )
            log_event(
                HANDOFF_REQUESTED,
                source="llm_repair",
                state=state,
                route_hint=handoff_route.value,
                trigger_reason=result.reason or "needs_human",
            )
        log_event(
            LLM_REPAIR_GUIDANCE_SHOWN,
            reason=reason,
            action=result.action.value,
            confidence=result.confidence,
        )
        return True

    if not result.needs_confirmation:
        return False

    route = LLM_EDIT_ACTION_TO_TARGET.get(result.action.value)
    if route is None:
        return False

    domain, target_state = route
    await send_repair_confirmation(
        update,
        context,
        domain=domain,
        target_state=target_state,
        use_confirmed=use_confirmed,
        candidate_value=result.candidate_value,
        candidate_source="llm",
    )
    log_event(
        LLM_REPAIR_SIGNAL_DETECTED,
        domain=domain,
        target_state=target_state,
        scope="confirmed" if use_confirmed else "draft",
        confidence=result.confidence,
        has_candidate=result.candidate_value is not None,
        action=result.action.value,
    )
    return True


async def attempt_llm_repair_after_rules(
    update,
    context,
    *,
    text: str,
    domain: str,
    use_confirmed: bool,
) -> bool:
    state = current_state(context.user_data)
    if not llm_edit_intent_policy_enabled(context):
        log_event(
            LLM_SKIPPED_BY_POLICY,
            invocation_type="repair",
            state=state,
            domain=domain,
            policy_scope="unknown_input",
            reason=llm_edit_intent_policy_skip_reason(context),
        )
        return False
    unknown_policy = evaluate_unknown_input_policy(
        current_step=state,
        domain_hint=domain,
        use_confirmed=use_confirmed,
    )
    if unknown_policy.disposition != UnknownInputDisposition.REPAIR_ASSIST_ALLOWED:
        log_event(
            LLM_SKIPPED_BY_POLICY,
            invocation_type="repair",
            state=state,
            domain=domain,
            policy_scope="unknown_input",
            unknown_disposition=unknown_policy.disposition.value,
            reason=unknown_policy.reason,
        )
        return False
    return await maybe_send_llm_repair_confirmation(
        update,
        context,
        text=text,
        allowed_actions=repair_allowed_actions(domain),
        use_confirmed=use_confirmed,
        policy_scope="unknown_input",
        unknown_policy_reason=unknown_policy.reason,
    )


async def finish_profile_edit_if_needed(update, context, edited_state: str) -> bool:
    edit_target = pending_slot(context.user_data)
    if edit_target is None:
        return False

    if edited_state == STATE_PROFILE_NAME and edit_target == STATE_PROFILE_NAME:
        set_pending_slot(context.user_data, None)
        set_state(context.user_data, STATE_PROFILE_CONFIRM)
        await send_profile_confirmation(update, context)
        return True

    if edited_state == STATE_PROFILE_RESIDENCE and edit_target == STATE_PROFILE_RESIDENCE:
        set_pending_slot(context.user_data, None)
        set_state(context.user_data, STATE_PROFILE_CONFIRM)
        await send_profile_confirmation(update, context)
        return True

    if edited_state == STATE_PROFILE_CITY and edit_target == STATE_PROFILE_CITY:
        set_pending_slot(context.user_data, None)
        set_state(context.user_data, STATE_PROFILE_CONFIRM)
        await send_profile_confirmation(update, context)
        return True

    if edited_state == STATE_PROFILE_DISTRICT and edit_target == STATE_PROFILE_DISTRICT:
        set_pending_slot(context.user_data, None)
        set_state(context.user_data, STATE_PROFILE_CONFIRM)
        await send_profile_confirmation(update, context)
        return True

    if edited_state == STATE_PROFILE_BIRTH_DAY and edit_target == STATE_PROFILE_BIRTH_YEAR:
        set_pending_slot(context.user_data, None)
        set_state(context.user_data, STATE_PROFILE_CONFIRM)
        await send_profile_confirmation(update, context)
        return True

    return False


def parse_callback_data(data: str) -> tuple[str, dict]:
    if data.startswith("intent:"):
        return data.split(":", 1)[1], {}
    if data == "repair:candidate:apply":
        return "repair_candidate_apply", {}
    if data.startswith("repair:confirm:"):
        _, _, domain, scope, target_state = data.split(":", 4)
        return "repair_confirm", {"domain": domain, "scope": scope, "target_state": target_state}
    if data == "repair:cancel":
        return "repair_cancel", {}
    if data.startswith("language:"):
        return "language_select", {"locale": data.split(":", 1)[1]}
    if data.startswith("profile:year_nav:"):
        return "profile_year_nav", {"direction": data.rsplit(":", 1)[1]}
    if data.startswith("profile:year:"):
        return "profile_year", {"year": int(data.rsplit(":", 1)[1])}
    if data.startswith("profile:month:"):
        return "profile_month", {"month": int(data.rsplit(":", 1)[1])}
    if data.startswith("profile:day:"):
        return "profile_day", {"day": int(data.rsplit(":", 1)[1])}
    if data.startswith("profile:edit:"):
        return "profile_edit_select", {"target": data.rsplit(":", 1)[1]}
    if data.startswith("fertilizer:edit:"):
        return "fertilizer_edit_select", {"target": data.rsplit(":", 1)[1]}
    if data.startswith("fertilizer:used:"):
        return "fertilizer_used", {"used": data.rsplit(":", 1)[1] == "yes"}
    if data.startswith("fertilizer:kind:"):
        return "fertilizer_kind", {"kind": data.rsplit(":", 1)[1]}
    if data.startswith("yield:ready:"):
        return "yield_ready", {"ready": data.rsplit(":", 1)[1] == "yes"}
    if data.startswith("yield:edit:") and data != "yield:edit:start":
        return "yield_edit_select", {"target": data.rsplit(":", 1)[1]}
    if data == "yield:edit:start":
        return "yield_edit_start", {}
    return registry.INTENT_UNKNOWN_TEXT, {}


async def clear_callback_markup(update) -> None:
    query = update.callback_query
    if query is None:
        return
    try:
        await query.answer()
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        return


async def handle_profile_state(update, context, state: str, text: str) -> bool:
    catalog = current_catalog(context)
    draft = current_profile(context)

    if state == STATE_PROFILE_NAME:
        name = profile_service.parse_name(text)
        if name is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, name=name).to_dict())
        if await finish_profile_edit_if_needed(update, context, STATE_PROFILE_NAME):
            return True
        set_state(context.user_data, STATE_PROFILE_RESIDENCE, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_RESIDENCE)
        return True

    if state == STATE_PROFILE_RESIDENCE:
        residence = profile_service.parse_free_text(text)
        if residence is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, residence=residence).to_dict())
        if await finish_profile_edit_if_needed(update, context, STATE_PROFILE_RESIDENCE):
            return True
        set_state(context.user_data, STATE_PROFILE_CITY, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_CITY)
        return True

    if state == STATE_PROFILE_CITY:
        city = profile_service.parse_free_text(text)
        if city is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, city=city).to_dict())
        if await finish_profile_edit_if_needed(update, context, STATE_PROFILE_CITY):
            return True
        set_state(context.user_data, STATE_PROFILE_DISTRICT, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_DISTRICT)
        return True

    if state == STATE_PROFILE_DISTRICT:
        district = profile_service.parse_free_text(text)
        if district is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, district=district).to_dict())
        if await finish_profile_edit_if_needed(update, context, STATE_PROFILE_DISTRICT):
            return True
        set_state(context.user_data, STATE_PROFILE_BIRTH_YEAR, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_YEAR)
        return True

    if state == STATE_PROFILE_BIRTH_YEAR:
        if text == catalog.BUTTON_PREV_YEARS:
            updated = profile_service.update_draft(draft, year_page_start=draft.year_page_start - 12)
            set_profile_draft(context.user_data, updated.to_dict())
            await send_profile_prompt(update, context, state)
            return True
        if text == catalog.BUTTON_NEXT_YEARS:
            updated = profile_service.update_draft(draft, year_page_start=draft.year_page_start + 12)
            set_profile_draft(context.user_data, updated.to_dict())
            await send_profile_prompt(update, context, state)
            return True

        year = profile_service.parse_year_button(text)
        current_year = profile_service.datetime.now().year
        if year is None or year < 1900 or year > current_year:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
            return True
        updated = profile_service.update_draft(draft, birth_year=year, birth_month=None, birth_day=None)
        set_profile_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_PROFILE_BIRTH_MONTH, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_MONTH)
        return True

    if state == STATE_PROFILE_BIRTH_MONTH:
        month = profile_service.parse_month_button(text)
        if month is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
            return True
        updated = profile_service.update_draft(draft, birth_month=month, birth_day=None)
        set_profile_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_PROFILE_BIRTH_DAY, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_DAY)
        return True

    if state == STATE_PROFILE_BIRTH_DAY:
        day = profile_service.parse_day_button(text)
        if day is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
            return True
        updated = profile_service.update_draft(draft, birth_day=day)
        set_profile_draft(context.user_data, updated.to_dict())
        if await finish_profile_edit_if_needed(update, context, STATE_PROFILE_BIRTH_DAY):
            return True
        set_state(context.user_data, STATE_PROFILE_CONFIRM, push_history=True)
        await send_profile_confirmation(update, context)
        return True

    if state == STATE_PROFILE_CONFIRM:
        await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state, catalog))
        return True

    return False


async def handle_fertilizer_state(update, context, state: str, text: str) -> bool:
    catalog = current_catalog(context)
    draft = current_fertilizer(context)

    if state == STATE_FERTILIZER_USED:
        used = fertilizer_service.parse_used(text)
        if used is None:
            await send_fertilizer_prompt(update, context, state, fertilizer_service.fallback_text_for_state(state, catalog))
            return True
        updated = fertilizer_service.update_draft(draft, used=used)
        set_fertilizer_draft(context.user_data, updated.to_dict())
        if used is False:
            set_state(context.user_data, STATE_FERTILIZER_CONFIRM, push_history=True)
            await send_fertilizer_confirmation(update, context)
            return True
        set_state(context.user_data, STATE_FERTILIZER_KIND, push_history=True)
        await send_fertilizer_prompt(update, context, STATE_FERTILIZER_KIND)
        return True

    if state == STATE_FERTILIZER_KIND:
        kind = fertilizer_service.parse_kind(text)
        if kind is None:
            await send_fertilizer_prompt(update, context, state, fertilizer_service.fallback_text_for_state(state, catalog))
            return True
        set_fertilizer_draft(context.user_data, fertilizer_service.update_draft(draft, kind=kind).to_dict())
        set_state(context.user_data, STATE_FERTILIZER_PRODUCT, push_history=True)
        await send_fertilizer_prompt(update, context, STATE_FERTILIZER_PRODUCT)
        return True

    if state == STATE_FERTILIZER_PRODUCT:
        product_name = fertilizer_service.parse_product_name(text)
        if product_name is None:
            await send_fertilizer_prompt(update, context, state, fertilizer_service.fallback_text_for_state(state, catalog))
            return True
        set_fertilizer_draft(context.user_data, fertilizer_service.update_draft(draft, product_name=product_name).to_dict())
        set_state(context.user_data, STATE_FERTILIZER_AMOUNT, push_history=True)
        await send_fertilizer_prompt(update, context, STATE_FERTILIZER_AMOUNT)
        return True

    if state == STATE_FERTILIZER_AMOUNT:
        amount = fertilizer_service.parse_amount(text)
        if amount is None:
            await send_fertilizer_prompt(update, context, state, fertilizer_service.fallback_text_for_state(state, catalog))
            return True
        value, unit = amount
        set_fertilizer_draft(context.user_data, fertilizer_service.update_draft(draft, amount_value=value, amount_unit=unit).to_dict())
        set_state(context.user_data, STATE_FERTILIZER_DATE, push_history=True)
        await send_fertilizer_prompt(update, context, STATE_FERTILIZER_DATE)
        return True

    if state == STATE_FERTILIZER_DATE:
        applied_date = fertilizer_service.parse_applied_date(text)
        if applied_date is None:
            await send_fertilizer_prompt(update, context, state, fertilizer_service.fallback_text_for_state(state, catalog))
            return True
        set_fertilizer_draft(context.user_data, fertilizer_service.update_draft(draft, applied_date=applied_date).to_dict())
        set_state(context.user_data, STATE_FERTILIZER_CONFIRM, push_history=True)
        await send_fertilizer_confirmation(update, context)
        return True

    if state == STATE_FERTILIZER_CONFIRM:
        await send_fertilizer_prompt(update, context, state, fertilizer_service.fallback_text_for_state(state, catalog))
        return True

    return False


async def handle_yield_state(update, context, state: str, text: str) -> bool:
    catalog = current_catalog(context)
    draft = current_yield(context)

    if state == STATE_YIELD_READY:
        ready = yield_service.parse_ready(text)
        if ready is None:
            await send_yield_prompt(update, context, state, yield_service.fallback_text_for_state(state, catalog))
            return True
        set_yield_draft(context.user_data, yield_service.update_draft(draft, ready=ready).to_dict())
        set_state(context.user_data, STATE_YIELD_FIELD, push_history=True)
        await send_yield_prompt(update, context, STATE_YIELD_FIELD)
        return True

    if state == STATE_YIELD_FIELD:
        field_name = yield_service.parse_field_name(text)
        if field_name is None:
            await send_yield_prompt(update, context, state, yield_service.fallback_text_for_state(state, catalog))
            return True
        set_yield_draft(context.user_data, yield_service.update_draft(draft, field_name=field_name).to_dict())
        set_state(context.user_data, STATE_YIELD_AMOUNT, push_history=True)
        await send_yield_prompt(update, context, STATE_YIELD_AMOUNT)
        return True

    if state == STATE_YIELD_AMOUNT:
        amount = yield_service.parse_amount(text)
        if amount is None:
            await send_yield_prompt(update, context, state, yield_service.fallback_text_for_state(state, catalog))
            return True
        value, unit = amount
        set_yield_draft(context.user_data, yield_service.update_draft(draft, amount_value=value, amount_unit=unit).to_dict())
        set_state(context.user_data, STATE_YIELD_DATE, push_history=True)
        await send_yield_prompt(update, context, STATE_YIELD_DATE)
        return True

    if state == STATE_YIELD_DATE:
        harvest_date = yield_service.parse_harvest_date(text)
        if harvest_date is None:
            await send_yield_prompt(update, context, state, yield_service.fallback_text_for_state(state, catalog))
            return True
        set_yield_draft(context.user_data, yield_service.update_draft(draft, harvest_date=harvest_date).to_dict())
        set_state(context.user_data, STATE_YIELD_CONFIRM, push_history=True)
        await send_yield_confirmation(update, context)
        return True

    if state == STATE_YIELD_CONFIRM:
        await send_yield_prompt(update, context, state, yield_service.fallback_text_for_state(state, catalog))
        return True

    if state == STATE_YIELD_EDIT_SELECT:
        await send_yield_prompt(update, context, state, yield_service.fallback_text_for_state(state, catalog))
        return True

    return False


async def text_message(update, context) -> None:
    inbound = parse_update(update)
    state = current_state(context.user_data)
    session_locale = current_locale(context.user_data)
    intent, payload = text_to_intent(
        inbound.text,
        current_step=state,
        locale=session_locale,
    )

    if has_active_support_handoff(context.user_data) and intent not in HANDOFF_SAFE_EXIT_INTENTS:
        record_support_handoff_user_message(
            context.user_data,
            user_message=inbound.text,
            source="active_handoff_user_message",
        )
        await send_text(
            update,
            current_catalog(context).SUPPORT_HANDOFF_MESSAGE_RECORDED,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), current_catalog(context), profile_draft(context.user_data)),
        )
        return

    if has_active_support_handoff(context.user_data) and intent in HANDOFF_SAFE_EXIT_INTENTS:
        close_support_handoff(
            context.user_data,
            reason="user_safe_exit",
            source="active_handoff_safe_exit",
        )

    early_gate = classify_cheap_gate(
        inbound.text,
        current_step=state,
        locale=session_locale,
    )
    if early_gate.classification == ValidationClassification.NEEDS_HANDOFF and early_gate.reason in {
        "explicit_support_request",
        "manual_handoff_request",
    }:
        handoff_route = handoff_route_for_validation(
            reason=early_gate.reason,
            human_handoff_reason=early_gate.human_handoff_reason,
            source="cheap_gate",
        )
        log_event(
            CHEAP_GATE_BLOCKED,
            state=state,
            reason=early_gate.reason,
            classification=early_gate.classification.value,
        )
        log_event(
            HANDOFF_REQUESTED,
            source="cheap_gate",
            state=state,
            route_hint=handoff_route.value,
            trigger_reason=early_gate.human_handoff_reason or early_gate.reason,
        )
        catalog = current_catalog(context)
        recovery_context = assemble_recovery_context(
            current_step=state,
            latest_user_message=inbound.text,
            locale=session_locale,
            recovery_attempt_count=recovery_attempts(context.user_data),
            canonical_intent=registry.INTENT_UNKNOWN_TEXT,
            validation_result=early_gate,
            fallback_key=fallback_key_for_state(state),
            profile_draft_data=profile_draft(context.user_data),
            fertilizer_draft_data=fertilizer_draft(context.user_data),
            confirmed_profile_data=None,
            pending_slot=pending_slot(context.user_data),
        )
        set_last_recovery_context(context.user_data, recovery_context.to_dict())
        log_recovery_classification_event(recovery_context, source="early_gate_handoff")
        create_handoff_request_from_runtime(
            update,
            context,
            route_hint=handoff_route,
            reason=early_gate.human_handoff_reason or early_gate.reason or "needs_handoff",
            current_step=state,
            user_message=inbound.text,
            failure_count=recovery_attempts(context.user_data),
            recent_messages_summary=recovery_context.recent_messages_summary,
            source="early_gate_handoff",
        )
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.cheap_gate_text(
                early_gate,
                fallback_key_for_state(state),
                catalog,
                recovery_context.to_dict(),
            ),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if state == STATE_LANGUAGE_SELECT:
        locale = resolve_language_choice(inbound.text)
        if locale is not None:
            set_locale(context.user_data, locale)
            set_state(context.user_data, STATE_MAIN_MENU)
            catalog = current_catalog(context)
            reset_recovery_attempts(context.user_data)
            await send_text(
                update,
                service.language_changed_text(catalog),
                keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
            )
            return
        await send_text(
            update,
            service.language_menu_text(current_catalog(context)),
            keyboard_layout=language_keyboard(),
        )
        return

    if state in PROFILE_STATES:
        if state in {STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT}:
            multi_slot_changes = extract_profile_multi_slot_candidate_changes(inbound.text)
            if multi_slot_changes is not None:
                reset_recovery_attempts(context.user_data)
                await send_repair_confirmation(
                    update,
                    context,
                    domain="profile",
                    target_state=STATE_PROFILE_CONFIRM,
                    use_confirmed=False,
                    candidate_changes=multi_slot_changes,
                )
                return

        profile_direct_update = detect_profile_direct_update(
            inbound.text,
            allow_implicit=state in {STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT},
        )
        if profile_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=profile_direct_update.matched_rule,
                domain="profile",
                target_state=profile_direct_update.target_state,
                scope="draft",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=profile_direct_update.target_state,
                use_confirmed=False,
                candidate_changes=profile_direct_update.changes if state in {STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT} else None,
            )
            return

        repair = detect_repair_intent(
            inbound.text,
            current_state=state,
            domain_hint="profile",
        )
        if repair is not None and repair.target_state in PROFILE_STATES:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=repair.target,
                domain="profile",
                target_state=repair.target_state,
                scope="draft",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=repair.target_state,
                use_confirmed=False,
            )
            return

        handled_by_llm = await attempt_llm_repair_after_rules(
            update,
            context,
            text=inbound.text,
            domain="profile",
            use_confirmed=False,
        )
        if handled_by_llm:
            reset_recovery_attempts(context.user_data)
            return

    if state in FERTILIZER_STATES:
        if state == STATE_FERTILIZER_CONFIRM:
            multi_slot_changes = extract_fertilizer_multi_slot_candidate_changes(inbound.text)
            if multi_slot_changes is not None:
                reset_recovery_attempts(context.user_data)
                await send_repair_confirmation(
                    update,
                    context,
                    domain="fertilizer",
                    target_state=STATE_FERTILIZER_CONFIRM,
                    use_confirmed=False,
                    candidate_changes=multi_slot_changes,
                )
                return

        fertilizer_direct_update = detect_fertilizer_direct_update(
            inbound.text,
            allow_implicit=state == STATE_FERTILIZER_CONFIRM,
        )
        if fertilizer_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=fertilizer_direct_update.matched_rule,
                domain="fertilizer",
                target_state=fertilizer_direct_update.target_state,
                scope="draft",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=fertilizer_direct_update.target_state,
                use_confirmed=False,
                candidate_changes=fertilizer_direct_update.changes if state == STATE_FERTILIZER_CONFIRM else None,
            )
            return

        repair = detect_repair_intent(
            inbound.text,
            current_state=state,
            domain_hint="fertilizer",
        )
        if repair is not None and repair.target_state in FERTILIZER_STATES:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=repair.target,
                domain="fertilizer",
                target_state=repair.target_state,
                scope="draft",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=repair.target_state,
                use_confirmed=False,
            )
            return

        handled_by_llm = await attempt_llm_repair_after_rules(
            update,
            context,
            text=inbound.text,
            domain="fertilizer",
            use_confirmed=False,
        )
        if handled_by_llm:
            reset_recovery_attempts(context.user_data)
            return

    if state not in PROFILE_STATES and has_confirmed_profile(context.user_data):
        multi_slot_changes = extract_profile_multi_slot_candidate_changes(inbound.text)
        if multi_slot_changes is not None:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=STATE_PROFILE_CONFIRM,
                use_confirmed=True,
                candidate_changes=multi_slot_changes,
            )
            return

        profile_direct_update = detect_profile_direct_update(inbound.text, allow_implicit=True)
        if profile_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=profile_direct_update.matched_rule,
                domain="profile",
                target_state=profile_direct_update.target_state,
                scope="confirmed",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=profile_direct_update.target_state,
                use_confirmed=True,
                candidate_changes=profile_direct_update.changes,
            )
            return

        repair = detect_repair_intent(
            inbound.text,
            current_state=STATE_PROFILE_CONFIRM,
            domain_hint="profile",
        )
        if repair is not None and repair.target_state in PROFILE_STATES:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=repair.target,
                domain="profile",
                target_state=repair.target_state,
                scope="confirmed",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=repair.target_state,
                use_confirmed=True,
            )
            return
        if detect_profile_view_intent(inbound.text):
            reset_recovery_attempts(context.user_data)
            await show_current_profile(update, context)
            return

        handled_by_llm = await attempt_llm_repair_after_rules(
            update,
            context,
            text=inbound.text,
            domain="profile",
            use_confirmed=True,
        )
        if handled_by_llm:
            reset_recovery_attempts(context.user_data)
            return

    if state not in FERTILIZER_STATES and has_confirmed_fertilizer(context.user_data):
        multi_slot_changes = extract_fertilizer_multi_slot_candidate_changes(inbound.text)
        if multi_slot_changes is not None:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=STATE_FERTILIZER_CONFIRM,
                use_confirmed=True,
                candidate_changes=multi_slot_changes,
            )
            return

        fertilizer_direct_update = detect_fertilizer_direct_update(inbound.text, allow_implicit=True)
        if fertilizer_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=fertilizer_direct_update.matched_rule,
                domain="fertilizer",
                target_state=fertilizer_direct_update.target_state,
                scope="confirmed",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=fertilizer_direct_update.target_state,
                use_confirmed=True,
                candidate_changes=fertilizer_direct_update.changes,
            )
            return

        repair = detect_repair_intent(
            inbound.text,
            current_state=STATE_FERTILIZER_CONFIRM,
            domain_hint="fertilizer",
        )
        if repair is not None and repair.target_state in FERTILIZER_STATES:
            reset_recovery_attempts(context.user_data)
            log_rule_matched(
                rule_name=repair.target,
                domain="fertilizer",
                target_state=repair.target_state,
                scope="confirmed",
            )
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=repair.target_state,
                use_confirmed=True,
            )
            return

        handled_by_llm = await attempt_llm_repair_after_rules(
            update,
            context,
            text=inbound.text,
            domain="fertilizer",
            use_confirmed=True,
        )
        if handled_by_llm:
            reset_recovery_attempts(context.user_data)
            return

    decision = route_message(state, intent, payload)
    catalog = current_catalog(context)

    if decision.route == ROUTE_HELP:
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.help_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_MAIN_MENU:
        reset_session(context.user_data)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.main_menu_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, None),
        )
        return

    if decision.route == ROUTE_OPEN_PROFILE:
        reset_recovery_attempts(context.user_data)
        await start_profile_input(update, context)
        return

    if decision.route == ROUTE_OPEN_YIELD:
        reset_recovery_attempts(context.user_data)
        await start_yield_input(update, context)
        return

    if decision.route == ROUTE_OPEN_MYFIELDS:
        reset_recovery_attempts(context.user_data)
        await myfields_command(update, context)
        return

    if decision.route == ROUTE_OPEN_INPUT_RESOLVE:
        reset_recovery_attempts(context.user_data)
        await input_resolve_command(update, context)
        return

    if decision.route == ROUTE_SUPPORT_GUIDANCE:
        reset_recovery_attempts(context.user_data)
        await show_support_guidance(
            update,
            context,
            user_message=inbound.text,
            source="support_text_intent",
        )
        return

    if decision.route == ROUTE_OPEN_FERTILIZER:
        reset_recovery_attempts(context.user_data)
        await start_fertilizer_input(update, context)
        return

    if decision.route == ROUTE_CANCEL:
        cancel_session(context.user_data)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.cancel_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, None),
        )
        return

    if decision.route == ROUTE_GO_BACK:
        previous_state = go_back(context.user_data)
        reset_recovery_attempts(context.user_data)
        if previous_state in PROFILE_STATES:
            await send_profile_prompt(update, context, previous_state)
            return
        message = service.back_text(previous_state, catalog)
        await send_text(
            update,
            message,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_PROFILE_EDIT:
        set_state(context.user_data, decision.next_state or STATE_PROFILE_EDIT_SELECT, push_history=decision.push_history)
        set_pending_slot(context.user_data, None)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            profile_service.edit_text(catalog),
            keyboard_layout=profile_service.keyboard_for_state(current_state(context.user_data), current_profile(context), catalog),
        )
        return

    if decision.route == ROUTE_YIELD_EDIT:
        set_state(context.user_data, decision.next_state or STATE_YIELD_EDIT_SELECT, push_history=decision.push_history)
        reset_recovery_attempts(context.user_data)
        await send_yield_prompt(update, context, current_state(context.user_data))
        return

    if decision.route == ROUTE_PROFILE_FINALIZE:
        set_confirmed_profile(context.user_data, profile_draft(context.user_data))
        set_state(context.user_data, STATE_MAIN_MENU)
        set_pending_slot(context.user_data, None)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            profile_service.confirmed_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_FERTILIZER_FINALIZE:
        set_confirmed_fertilizer(context.user_data, fertilizer_draft(context.user_data))
        set_state(context.user_data, STATE_MAIN_MENU)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            fertilizer_service.confirmed_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_YIELD_FINALIZE:
        set_confirmed_yield(context.user_data, yield_draft(context.user_data))
        set_state(context.user_data, STATE_MAIN_MENU)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            yield_service.confirmed_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if state in PROFILE_STATES:
        handled = await handle_profile_state(update, context, state, inbound.text)
        if handled:
            reset_recovery_attempts(context.user_data)
            return

    if state in FERTILIZER_STATES:
        handled = await handle_fertilizer_state(update, context, state, inbound.text)
        if handled:
            reset_recovery_attempts(context.user_data)
            return

    if state in YIELD_STATES:
        handled = await handle_yield_state(update, context, state, inbound.text)
        if handled:
            reset_recovery_attempts(context.user_data)
            return

    fallback_key = fallback_key_for_state(current_state(context.user_data))
    late_gate = classify_cheap_gate(
        inbound.text,
        current_step=current_state(context.user_data),
        locale=current_locale(context.user_data),
        recovery_attempt_count=recovery_attempts(context.user_data) + 1,
    )
    if late_gate.classification == ValidationClassification.NEEDS_HANDOFF:
        handoff_route = handoff_route_for_validation(
            reason=late_gate.reason,
            human_handoff_reason=late_gate.human_handoff_reason,
            source="cheap_gate",
        )
        log_event(
            CHEAP_GATE_BLOCKED,
            state=current_state(context.user_data),
            reason=late_gate.reason,
            classification=late_gate.classification.value,
        )
        log_event(
            HANDOFF_REQUESTED,
            source="cheap_gate",
            state=current_state(context.user_data),
            route_hint=handoff_route.value,
            trigger_reason=late_gate.human_handoff_reason or late_gate.reason,
        )
        recovery_context = assemble_recovery_context(
            current_step=current_state(context.user_data),
            latest_user_message=inbound.text,
            locale=current_locale(context.user_data),
            recovery_attempt_count=recovery_attempts(context.user_data) + 1,
            canonical_intent=intent,
            validation_result=late_gate,
            fallback_key=fallback_key,
            profile_draft_data=profile_draft(context.user_data),
            fertilizer_draft_data=fertilizer_draft(context.user_data),
            confirmed_profile_data=None,
            pending_slot=pending_slot(context.user_data),
        )
        set_last_recovery_context(context.user_data, recovery_context.to_dict())
        log_recovery_classification_event(recovery_context, source="late_gate_handoff")
        create_handoff_request_from_runtime(
            update,
            context,
            route_hint=handoff_route,
            reason=late_gate.human_handoff_reason or late_gate.reason or "needs_handoff",
            current_step=current_state(context.user_data),
            user_message=inbound.text,
            failure_count=recovery_attempts(context.user_data) + 1,
            recent_messages_summary=recovery_context.recent_messages_summary,
            source="late_gate_handoff",
        )
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.cheap_gate_text(
                late_gate,
                fallback_key,
                catalog,
                recovery_context.to_dict(),
            ),
            keyboard_layout=fallback_keyboard_layout_for_state(
                current_state(context.user_data),
                catalog,
                profile_draft(context.user_data),
            ),
        )
        log_event(
            FALLBACK_SHOWN,
            source="cheap_gate_handoff",
            state=current_state(context.user_data),
            fallback_key=fallback_key,
        )
        return

    increment_recovery_attempts(context.user_data)
    log_event(
        CHEAP_GATE_BLOCKED,
        state=current_state(context.user_data),
        reason=late_gate.reason,
        classification=late_gate.classification.value,
    )
    await send_text(
        update,
        service.cheap_gate_text(
            late_gate,
            fallback_key,
            catalog,
            last_recovery_context(context.user_data),
        ),
        keyboard_layout=fallback_keyboard_layout_for_state(
            current_state(context.user_data),
            catalog,
            profile_draft(context.user_data),
        ),
    )
    log_event(
        FALLBACK_SHOWN,
        source="cheap_gate_retry",
        state=current_state(context.user_data),
        fallback_key=fallback_key,
    )


async def button_callback(update, context) -> None:
    query = update.callback_query
    if query is None:
        return

    state = current_state(context.user_data)
    action, payload = parse_callback_data(query.data)

    if action == "language_select":
        await clear_callback_markup(update)
        set_locale(context.user_data, payload["locale"])
        set_state(context.user_data, STATE_MAIN_MENU)
        catalog = current_catalog(context)
        await send_text(
            update,
            service.language_changed_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if action == "repair_confirm":
        await clear_callback_markup(update)
        reset_recovery_attempts(context.user_data)
        set_pending_repair_confirmation(context.user_data, None)
        discard_pending_candidate(context, reason="repair_confirm_selected")
        target_state = payload["target_state"]
        use_confirmed = payload["scope"] == "confirmed"
        await continue_repair_flow(
            update,
            context,
            domain=payload["domain"],
            target_state=target_state,
            use_confirmed=use_confirmed,
        )
        return

    if action == "repair_candidate_apply":
        await clear_callback_markup(update)
        reset_recovery_attempts(context.user_data)
        pending_confirmation = pending_repair_confirmation(context.user_data)
        candidate_payload = pending_candidate(context.user_data)
        set_pending_repair_confirmation(context.user_data, None)
        if pending_confirmation is None or candidate_payload is None:
            discard_pending_candidate(context, reason="candidate_payload_missing")
            await send_text(
                update,
                service.fallback_text(
                    fallback_key_for_state(current_state(context.user_data)),
                    current_catalog(context),
                    last_recovery_context(context.user_data),
                ),
                keyboard_layout=fallback_keyboard_layout_for_state(
                    current_state(context.user_data),
                    current_catalog(context),
                    profile_draft(context.user_data),
                ),
            )
            return

        domain = pending_confirmation["domain"]
        target_state = pending_confirmation["target_state"]
        use_confirmed = pending_confirmation["scope"] == "confirmed"
        changes = candidate_changes_from_payload(candidate_payload)
        if changes is None:
            discard_pending_candidate(context, reason="candidate_parse_failed")
            await continue_repair_flow(
                update,
                context,
                domain=domain,
                target_state=target_state,
                use_confirmed=use_confirmed,
            )
            return

        discard_pending_candidate(context, reason="candidate_promoted_to_apply")
        if domain == "profile":
            await apply_profile_changes(update, context, changes=changes, use_confirmed=use_confirmed)
            return
        await apply_fertilizer_changes(
            update,
            context,
            target_state=target_state,
            changes=changes,
            use_confirmed=use_confirmed,
        )
        return

    if action == "repair_cancel":
        await clear_callback_markup(update)
        set_pending_repair_confirmation(context.user_data, None)
        discard_pending_candidate(context, reason="repair_cancelled")
        await send_text(
            update,
            service.fallback_text(
                fallback_key_for_state(current_state(context.user_data)),
                current_catalog(context),
                last_recovery_context(context.user_data),
            ),
            keyboard_layout=fallback_keyboard_layout_for_state(
                current_state(context.user_data),
                current_catalog(context),
                profile_draft(context.user_data),
            ),
        )
        return

    if action == "profile_year_nav":
        await clear_callback_markup(update)
        if state != STATE_PROFILE_BIRTH_YEAR:
            await send_profile_prompt(update, context, current_state(context.user_data))
            return
        draft = current_profile(context)
        delta = -12 if payload["direction"] == "prev" else 12
        updated = profile_service.update_draft(draft, year_page_start=draft.year_page_start + delta)
        set_profile_draft(context.user_data, updated.to_dict())
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_YEAR)
        return

    if action == "profile_year":
        await clear_callback_markup(update)
        if state != STATE_PROFILE_BIRTH_YEAR:
            await send_profile_prompt(update, context, current_state(context.user_data))
            return
        draft = current_profile(context)
        updated = profile_service.update_draft(draft, birth_year=payload["year"], birth_month=None, birth_day=None)
        set_profile_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_PROFILE_BIRTH_MONTH, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_MONTH)
        return

    if action == "profile_month":
        await clear_callback_markup(update)
        if state != STATE_PROFILE_BIRTH_MONTH:
            await send_profile_prompt(update, context, current_state(context.user_data))
            return
        draft = current_profile(context)
        updated = profile_service.update_draft(draft, birth_month=payload["month"], birth_day=None)
        set_profile_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_PROFILE_BIRTH_DAY, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_DAY)
        return

    if action == "profile_day":
        await clear_callback_markup(update)
        if state != STATE_PROFILE_BIRTH_DAY:
            await send_profile_prompt(update, context, current_state(context.user_data))
            return
        draft = current_profile(context)
        updated = profile_service.update_draft(draft, birth_day=payload["day"])
        set_profile_draft(context.user_data, updated.to_dict())
        if await finish_profile_edit_if_needed(update, context, STATE_PROFILE_BIRTH_DAY):
            return
        set_state(context.user_data, STATE_PROFILE_CONFIRM, push_history=True)
        await send_profile_confirmation(update, context)
        return

    if action == "profile_edit_select":
        await clear_callback_markup(update)
        target_state = PROFILE_EDIT_CALLBACK_TO_STATE.get(payload["target"])
        if target_state is None:
            await send_profile_prompt(update, context, STATE_PROFILE_EDIT_SELECT)
            return
        draft = profile_service.reset_draft_for_repair(current_profile(context), target_state)
        set_profile_draft(context.user_data, draft.to_dict())
        set_pending_slot(context.user_data, target_state)
        set_state(context.user_data, target_state, push_history=True)
        await send_text(
            update,
            profile_service.repair_message(target_state, current_catalog(context)),
            keyboard_layout=profile_service.keyboard_for_state(target_state, draft, current_catalog(context)),
        )
        return

    if action == "fertilizer_edit_select":
        await clear_callback_markup(update)
        target_state = FERTILIZER_EDIT_CALLBACK_TO_STATE.get(payload["target"])
        if target_state is None:
            await send_fertilizer_prompt(update, context, STATE_FERTILIZER_CONFIRM)
            return
        draft = fertilizer_service.reset_draft_for_repair(current_fertilizer(context), target_state)
        set_fertilizer_draft(context.user_data, draft.to_dict())
        set_state(context.user_data, target_state, push_history=True)
        await send_text(
            update,
            fertilizer_service.repair_message(target_state, current_catalog(context)),
            keyboard_layout=fertilizer_service.keyboard_for_state(target_state, current_catalog(context)),
        )
        return

    if action == "fertilizer_used":
        await clear_callback_markup(update)
        if state != STATE_FERTILIZER_USED:
            if current_state(context.user_data) in FERTILIZER_STATES:
                await send_fertilizer_prompt(update, context, current_state(context.user_data))
            return
        draft = current_fertilizer(context)
        updated = fertilizer_service.update_draft(draft, used=payload["used"])
        set_fertilizer_draft(context.user_data, updated.to_dict())
        if payload["used"] is False:
            set_state(context.user_data, STATE_FERTILIZER_CONFIRM, push_history=True)
            await send_fertilizer_confirmation(update, context)
            return
        set_state(context.user_data, STATE_FERTILIZER_KIND, push_history=True)
        await send_fertilizer_prompt(update, context, STATE_FERTILIZER_KIND)
        return

    if action == "fertilizer_kind":
        await clear_callback_markup(update)
        if state != STATE_FERTILIZER_KIND:
            if current_state(context.user_data) in FERTILIZER_STATES:
                await send_fertilizer_prompt(update, context, current_state(context.user_data))
            return
        draft = current_fertilizer(context)
        updated = fertilizer_service.update_draft(draft, kind=payload["kind"])
        set_fertilizer_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_FERTILIZER_PRODUCT, push_history=True)
        await send_fertilizer_prompt(update, context, STATE_FERTILIZER_PRODUCT)
        return

    if action == "yield_ready":
        await clear_callback_markup(update)
        if state != STATE_YIELD_READY:
            if current_state(context.user_data) in YIELD_STATES:
                await send_yield_prompt(update, context, current_state(context.user_data))
            return
        draft = current_yield(context)
        updated = yield_service.update_draft(draft, ready=payload["ready"])
        set_yield_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_YIELD_FIELD, push_history=True)
        await send_yield_prompt(update, context, STATE_YIELD_FIELD)
        return

    if action == "yield_edit_start":
        await clear_callback_markup(update)
        if state != STATE_YIELD_EDIT_SELECT:
            if current_state(context.user_data) in YIELD_STATES:
                await send_yield_prompt(update, context, current_state(context.user_data))
            return
        set_yield_draft(context.user_data, yield_service.new_draft().to_dict())
        set_state(context.user_data, STATE_YIELD_READY, push_history=True)
        await send_yield_prompt(update, context, STATE_YIELD_READY)
        return

    if action == "yield_edit_select":
        await clear_callback_markup(update)
        if state != STATE_YIELD_EDIT_SELECT:
            if current_state(context.user_data) in YIELD_STATES:
                await send_yield_prompt(update, context, current_state(context.user_data))
            return
        target_state = YIELD_EDIT_CALLBACK_TO_STATE.get(payload["target"])
        if target_state is None:
            await send_yield_prompt(update, context, STATE_YIELD_EDIT_SELECT)
            return
        draft = yield_service.reset_draft_for_repair(current_yield(context), target_state)
        set_yield_draft(context.user_data, draft.to_dict())
        set_state(context.user_data, target_state, push_history=True)
        await send_yield_prompt(update, context, target_state)
        return

    decision = route_message(state, action, payload)
    await clear_callback_markup(update)
    catalog = current_catalog(context)

    if decision.route == ROUTE_HELP:
        await help_command(update, context)
        return

    if decision.route == ROUTE_MAIN_MENU:
        await menu_command(update, context)
        return

    if decision.route == ROUTE_OPEN_PROFILE:
        await start_profile_input(update, context)
        return

    if decision.route == ROUTE_OPEN_MYFIELDS:
        await myfields_command(update, context)
        return

    if decision.route == ROUTE_OPEN_INPUT_RESOLVE:
        await input_resolve_command(update, context)
        return

    if decision.route == ROUTE_SUPPORT_GUIDANCE:
        await show_support_guidance(update, context)
        return

    if decision.route == ROUTE_OPEN_FERTILIZER:
        await start_fertilizer_input(update, context)
        return

    if decision.route == ROUTE_OPEN_YIELD:
        await start_yield_input(update, context)
        return

    if decision.route == ROUTE_CANCEL:
        await cancel_command(update, context)
        return

    if decision.route == ROUTE_GO_BACK:
        previous_state = go_back(context.user_data)
        if previous_state in PROFILE_STATES:
            await send_profile_prompt(update, context, previous_state)
            return
        message = service.back_text(previous_state, catalog)
        await send_text(
            update,
            message,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_PROFILE_EDIT:
        set_state(context.user_data, decision.next_state or STATE_PROFILE_EDIT_SELECT, push_history=decision.push_history)
        set_pending_slot(context.user_data, None)
        await send_text(
            update,
            profile_service.edit_text(catalog),
            keyboard_layout=profile_service.keyboard_for_state(current_state(context.user_data), current_profile(context), catalog),
        )
        return

    if decision.route == ROUTE_YIELD_EDIT:
        set_state(context.user_data, decision.next_state or STATE_YIELD_EDIT_SELECT, push_history=decision.push_history)
        await send_yield_prompt(update, context, current_state(context.user_data))
        return

    if decision.route == ROUTE_PROFILE_FINALIZE:
        set_confirmed_profile(context.user_data, profile_draft(context.user_data))
        set_state(context.user_data, STATE_MAIN_MENU)
        set_pending_slot(context.user_data, None)
        await send_text(
            update,
            profile_service.confirmed_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_FERTILIZER_FINALIZE:
        set_confirmed_fertilizer(context.user_data, fertilizer_draft(context.user_data))
        set_state(context.user_data, STATE_MAIN_MENU)
        await send_text(
            update,
            fertilizer_service.confirmed_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_YIELD_FINALIZE:
        set_confirmed_yield(context.user_data, yield_draft(context.user_data))
        set_state(context.user_data, STATE_MAIN_MENU)
        await send_text(
            update,
            yield_service.confirmed_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    await send_text(
        update,
        service.fallback_text(
            fallback_key_for_state(current_state(context.user_data)),
            catalog,
            last_recovery_context(context.user_data),
        ),
        keyboard_layout=fallback_keyboard_layout_for_state(
            current_state(context.user_data),
            catalog,
            profile_draft(context.user_data),
        ),
    )
    log_event(
        FALLBACK_SHOWN,
        source="button_callback_default",
        state=current_state(context.user_data),
        fallback_key=fallback_key_for_state(current_state(context.user_data)),
    )


async def unknown_command(update, context) -> None:
    catalog = current_catalog(context)
    inbound = parse_update(update)
    profile_repair = detect_repair_intent(
        inbound.text,
        current_state=STATE_PROFILE_CONFIRM if has_confirmed_profile(context.user_data) else current_state(context.user_data),
        domain_hint="profile",
    )
    if has_confirmed_profile(context.user_data) and profile_repair is not None and profile_repair.target_state in PROFILE_STATES:
        await send_repair_confirmation(
            update,
            context,
            domain="profile",
            target_state=profile_repair.target_state,
            use_confirmed=True,
        )
        return
    fertilizer_repair = detect_repair_intent(
        inbound.text,
        current_state=STATE_FERTILIZER_CONFIRM if has_confirmed_fertilizer(context.user_data) else current_state(context.user_data),
        domain_hint="fertilizer",
    )
    if has_confirmed_fertilizer(context.user_data) and fertilizer_repair is not None and fertilizer_repair.target_state in FERTILIZER_STATES:
        await send_repair_confirmation(
            update,
            context,
            domain="fertilizer",
            target_state=fertilizer_repair.target_state,
            use_confirmed=True,
        )
        return
    if detect_profile_view_intent(inbound.text):
        await show_current_profile(update, context)
        return
    intent = command_to_intent(inbound.command)
    if intent != INTENT_UNKNOWN_COMMAND:
        return
    await send_text(
        update,
        service.unknown_command_text(catalog),
        keyboard_layout=fallback_keyboard_layout_for_state(
            current_state(context.user_data),
            catalog,
            profile_draft(context.user_data),
        ),
    )
    log_event(
        FALLBACK_SHOWN,
        source="unknown_command",
        state=current_state(context.user_data),
        fallback_key=fallback_key_for_state(current_state(context.user_data)),
    )
