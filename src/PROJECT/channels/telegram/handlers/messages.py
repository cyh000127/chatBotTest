import httpx

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.canonical_intents.mapping import command_to_intent, text_to_intent
from PROJECT.canonical_intents import registry
from PROJECT.canonical_intents.registry import INTENT_UNKNOWN_COMMAND
from PROJECT.channels.telegram.parser import parse_update
from PROJECT.channels.telegram.handlers.commands import (
    attempt_auth,
    cancel_command,
    help_command,
    open_fertilizer_edit_selector,
    menu_command,
    open_fertilizer_target_edit,
    open_profile_edit_selector,
    open_profile_target_edit,
    show_current_profile,
    start_fertilizer_input,
    start_profile_input,
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
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import (
    fallback_keyboard_layout_for_state,
    keyboard_layout_for_state,
    repair_confirmation_keyboard,
)
from PROJECT.conversations.sample_menu.states import STATE_AUTH_ID_INPUT, STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.dispatch.command_router import (
    ROUTE_CANCEL,
    ROUTE_FERTILIZER_FINALIZE,
    ROUTE_GO_BACK,
    ROUTE_HELP,
    ROUTE_MAIN_MENU,
    ROUTE_OPEN_FERTILIZER,
    ROUTE_OPEN_PROFILE,
    ROUTE_PROFILE_EDIT,
    ROUTE_PROFILE_FINALIZE,
    ROUTE_SHOW_DATE,
    ROUTE_SHOW_WEATHER,
    ROUTE_SHOW_WEATHER_MENU,
    route_message,
)
from PROJECT.dispatch.input_fallback import fallback_key_for_state
from PROJECT.dispatch.repair_router import detect_profile_view_intent, detect_repair_intent
from PROJECT.dispatch.session_dispatcher import (
    cancel_session,
    confirmed_fertilizer,
    confirmed_profile,
    current_locale,
    current_state,
    fertilizer_draft,
    go_back,
    has_confirmed_fertilizer,
    has_confirmed_profile,
    increment_recovery_attempts,
    is_authenticated,
    pending_repair_confirmation,
    pending_slot,
    profile_draft,
    recovery_attempts,
    reset_session,
    reset_recovery_attempts,
    set_confirmed_fertilizer,
    set_fertilizer_draft,
    set_last_recovery_context,
    set_confirmed_profile,
    set_locale,
    set_pending_repair_confirmation,
    set_pending_slot,
    set_profile_draft,
    set_selected_city,
    set_state,
)
from PROJECT.i18n.translator import get_catalog, language_keyboard, resolve_language_choice
from PROJECT.llm import LlmEditAction, LlmEditIntentResult
from PROJECT.rule_engine import (
    ValidationClassification,
    assemble_recovery_context,
    classify_cheap_gate,
    detect_fertilizer_direct_update,
    detect_profile_direct_update,
)
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import (
    FALLBACK_SHOWN,
    LLM_REPAIR_GUIDANCE_SHOWN,
    LLM_REPAIR_SIGNAL_DETECTED,
    REPAIR_CANDIDATE_APPLIED,
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


async def continue_repair_flow(update, context, *, domain: str, target_state: str, use_confirmed: bool) -> None:
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
    preview_text = fertilizer_service.change_preview_text(base_draft, updated, target_state, current_catalog(context))
    await send_text(
        update,
        f"{preview_text}\n\n{fertilizer_service.confirmation_text(updated, current_catalog(context))}",
        keyboard_layout=fertilizer_service.keyboard_for_state(STATE_FERTILIZER_CONFIRM, current_catalog(context)),
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
) -> None:
    catalog = current_catalog(context)
    scope = "confirmed" if use_confirmed else "draft"
    if domain == "profile":
        text = profile_service.repair_confirmation_text(target_state, catalog)
    else:
        text = fertilizer_service.repair_confirmation_text(target_state, catalog)
    parsed_candidate = parse_candidate_changes(domain, target_state, candidate_value)
    if parsed_candidate is not None and candidate_value:
        text = f"{text}\n\n{catalog.LLM_REPAIR_CANDIDATE_HINT.format(candidate_value=candidate_value)}"
        set_pending_repair_confirmation(
            context.user_data,
            {
                "domain": domain,
                "scope": scope,
                "target_state": target_state,
                "candidate_value": candidate_value,
            },
        )
    else:
        set_pending_repair_confirmation(context.user_data, None)
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


async def maybe_send_llm_repair_confirmation(
    update,
    context,
    *,
    text: str,
    allowed_actions: tuple[str, ...],
    use_confirmed: bool,
) -> bool:
    resolver = context.bot_data.get("gemini_edit_intent_resolver")
    lowered = text.strip().lower()
    if resolver is None or not lowered:
        return False
    if not any(marker in lowered for marker in EDIT_INTENT_HINT_MARKERS):
        return False

    try:
        result = await resolver.classify(
            text=text,
            locale=current_locale(context.user_data),
            allowed_actions=allowed_actions,
        )
    except Exception:
        return False

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
    if data.startswith("city:"):
        return registry.INTENT_SELECT_CITY, {"city": data.split(":", 1)[1]}
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


async def text_message(update, context) -> None:
    inbound = parse_update(update)
    state = current_state(context.user_data)
    session_locale = current_locale(context.user_data)
    if not is_authenticated(context.user_data):
        catalog = current_catalog(context)
        if state == STATE_AUTH_ID_INPUT:
            await attempt_auth(update, context, inbound.text)
            return
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return

    early_gate = classify_cheap_gate(
        inbound.text,
        current_step=state,
        locale=session_locale,
    )
    if early_gate.classification == ValidationClassification.NEEDS_HANDOFF and early_gate.reason in {
        "explicit_support_request",
        "manual_handoff_request",
    }:
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
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.cheap_gate_text(early_gate, fallback_key_for_state(state), catalog),
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
        profile_direct_update = detect_profile_direct_update(
            inbound.text,
            allow_implicit=state in {STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT},
        )
        if profile_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=profile_direct_update.target_state,
                use_confirmed=False,
            )
            return

        repair = detect_repair_intent(inbound.text)
        if repair is not None and repair.target_state in PROFILE_STATES:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=repair.target_state,
                use_confirmed=False,
            )
            return

        if state in {STATE_PROFILE_CONFIRM, STATE_PROFILE_EDIT_SELECT}:
            handled_by_llm = await maybe_send_llm_repair_confirmation(
                update,
                context,
                text=inbound.text,
                allowed_actions=(
                    LlmEditAction.PROFILE_EDIT_SELECT.value,
                    LlmEditAction.PROFILE_EDIT_NAME.value,
                    LlmEditAction.PROFILE_EDIT_RESIDENCE.value,
                    LlmEditAction.PROFILE_EDIT_CITY.value,
                    LlmEditAction.PROFILE_EDIT_DISTRICT.value,
                    LlmEditAction.PROFILE_EDIT_BIRTH_DATE.value,
                    LlmEditAction.UNSUPPORTED.value,
                ),
                use_confirmed=False,
            )
            if handled_by_llm:
                reset_recovery_attempts(context.user_data)
                return

    if state in FERTILIZER_STATES:
        fertilizer_direct_update = detect_fertilizer_direct_update(
            inbound.text,
            allow_implicit=state == STATE_FERTILIZER_CONFIRM,
        )
        if fertilizer_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=fertilizer_direct_update.target_state,
                use_confirmed=False,
            )
            return

        repair = detect_repair_intent(inbound.text)
        if repair is not None and repair.target_state in FERTILIZER_STATES:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=repair.target_state,
                use_confirmed=False,
            )
            return

        if state == STATE_FERTILIZER_CONFIRM:
            handled_by_llm = await maybe_send_llm_repair_confirmation(
                update,
                context,
                text=inbound.text,
                allowed_actions=(
                    LlmEditAction.FERTILIZER_EDIT_SELECT.value,
                    LlmEditAction.FERTILIZER_EDIT_USED.value,
                    LlmEditAction.FERTILIZER_EDIT_KIND.value,
                    LlmEditAction.FERTILIZER_EDIT_PRODUCT.value,
                    LlmEditAction.FERTILIZER_EDIT_AMOUNT.value,
                    LlmEditAction.FERTILIZER_EDIT_DATE.value,
                    LlmEditAction.UNSUPPORTED.value,
                ),
                use_confirmed=False,
            )
            if handled_by_llm:
                reset_recovery_attempts(context.user_data)
                return

    if state not in PROFILE_STATES and has_confirmed_profile(context.user_data):
        profile_direct_update = detect_profile_direct_update(inbound.text, allow_implicit=True)
        if profile_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="profile",
                target_state=profile_direct_update.target_state,
                use_confirmed=True,
            )
            return

        repair = detect_repair_intent(inbound.text)
        if repair is not None and repair.target_state in PROFILE_STATES:
            reset_recovery_attempts(context.user_data)
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

        handled_by_llm = await maybe_send_llm_repair_confirmation(
            update,
            context,
            text=inbound.text,
            allowed_actions=(
                LlmEditAction.PROFILE_EDIT_SELECT.value,
                LlmEditAction.PROFILE_EDIT_NAME.value,
                LlmEditAction.PROFILE_EDIT_RESIDENCE.value,
                LlmEditAction.PROFILE_EDIT_CITY.value,
                LlmEditAction.PROFILE_EDIT_DISTRICT.value,
                LlmEditAction.PROFILE_EDIT_BIRTH_DATE.value,
                LlmEditAction.UNSUPPORTED.value,
            ),
            use_confirmed=True,
        )
        if handled_by_llm:
            reset_recovery_attempts(context.user_data)
            return

    if state not in FERTILIZER_STATES and has_confirmed_fertilizer(context.user_data):
        fertilizer_direct_update = detect_fertilizer_direct_update(inbound.text, allow_implicit=True)
        if fertilizer_direct_update is not None:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=fertilizer_direct_update.target_state,
                use_confirmed=True,
            )
            return

        repair = detect_repair_intent(inbound.text)
        if repair is not None and repair.target_state in FERTILIZER_STATES:
            reset_recovery_attempts(context.user_data)
            await send_repair_confirmation(
                update,
                context,
                domain="fertilizer",
                target_state=repair.target_state,
                use_confirmed=True,
            )
            return

        handled_by_llm = await maybe_send_llm_repair_confirmation(
            update,
            context,
            text=inbound.text,
            allowed_actions=(
                LlmEditAction.FERTILIZER_EDIT_SELECT.value,
                LlmEditAction.FERTILIZER_EDIT_USED.value,
                LlmEditAction.FERTILIZER_EDIT_KIND.value,
                LlmEditAction.FERTILIZER_EDIT_PRODUCT.value,
                LlmEditAction.FERTILIZER_EDIT_AMOUNT.value,
                LlmEditAction.FERTILIZER_EDIT_DATE.value,
                LlmEditAction.UNSUPPORTED.value,
            ),
            use_confirmed=True,
        )
        if handled_by_llm:
            reset_recovery_attempts(context.user_data)
            return

    intent, payload = text_to_intent(
        inbound.text,
        current_step=state,
        locale=session_locale,
    )
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

    if decision.route == ROUTE_SHOW_DATE:
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.today_date_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_WEATHER_MENU:
        set_state(context.user_data, decision.next_state, push_history=decision.push_history)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.weather_menu_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_WEATHER:
        city = decision.payload["city"]
        set_selected_city(context.user_data, city)
        try:
            snapshot = await service.fetch_weather(city, context.bot_data["settings"])
            message = service.weather_result_text(snapshot, catalog)
        except httpx.HTTPError:
            message = service.weather_error_text(catalog)
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            message,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    fallback_key = fallback_key_for_state(current_state(context.user_data))
    late_gate = classify_cheap_gate(
        inbound.text,
        current_step=current_state(context.user_data),
        locale=current_locale(context.user_data),
        recovery_attempt_count=recovery_attempts(context.user_data) + 1,
    )
    if late_gate.classification == ValidationClassification.NEEDS_HANDOFF:
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
        reset_recovery_attempts(context.user_data)
        await send_text(
            update,
            service.cheap_gate_text(late_gate, fallback_key, catalog),
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
    await send_text(
        update,
        service.cheap_gate_text(late_gate, fallback_key, catalog),
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
    if not is_authenticated(context.user_data):
        await clear_callback_markup(update)
        await send_text(update, service.auth_required_text(current_catalog(context)), keyboard_layout=None)
        return

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
        set_pending_repair_confirmation(context.user_data, None)
        if pending_confirmation is None:
            await send_text(
                update,
                service.fallback_text(fallback_key_for_state(current_state(context.user_data)), current_catalog(context)),
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
        candidate_value = pending_confirmation.get("candidate_value")
        changes = parse_candidate_changes(domain, target_state, candidate_value)
        if changes is None:
            await continue_repair_flow(
                update,
                context,
                domain=domain,
                target_state=target_state,
                use_confirmed=use_confirmed,
            )
            return

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
        await send_text(
            update,
            service.fallback_text(fallback_key_for_state(current_state(context.user_data)), current_catalog(context)),
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

    if decision.route == ROUTE_OPEN_FERTILIZER:
        await start_fertilizer_input(update, context)
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

    if decision.route == ROUTE_SHOW_DATE:
        await send_text(
            update,
            service.today_date_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_WEATHER_MENU:
        set_state(context.user_data, decision.next_state, push_history=decision.push_history)
        await send_text(
            update,
            service.weather_menu_text(catalog),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_WEATHER:
        city = decision.payload["city"]
        set_selected_city(context.user_data, city)
        try:
            snapshot = await service.fetch_weather(city, context.bot_data["settings"])
            message = service.weather_result_text(snapshot, catalog)
        except httpx.HTTPError:
            message = service.weather_error_text(catalog)
        await send_text(
            update,
            message,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), catalog, profile_draft(context.user_data)),
        )
        return

    await send_text(
        update,
        service.fallback_text(fallback_key_for_state(current_state(context.user_data)), catalog),
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
    if not is_authenticated(context.user_data):
        await send_text(update, service.auth_required_text(catalog), keyboard_layout=None)
        return
    inbound = parse_update(update)
    repair = detect_repair_intent(inbound.text)
    if has_confirmed_profile(context.user_data) and repair is not None and repair.target_state in PROFILE_STATES:
        await send_repair_confirmation(
            update,
            context,
            domain="profile",
            target_state=repair.target_state,
            use_confirmed=True,
        )
        return
    if has_confirmed_fertilizer(context.user_data) and repair is not None and repair.target_state in FERTILIZER_STATES:
        await send_repair_confirmation(
            update,
            context,
            domain="fertilizer",
            target_state=repair.target_state,
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
