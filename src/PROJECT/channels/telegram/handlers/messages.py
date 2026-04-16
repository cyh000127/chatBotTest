import httpx

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.canonical_intents.mapping import command_to_intent, text_to_intent
from PROJECT.canonical_intents.registry import (
    INTENT_UNKNOWN_TEXT,
    INTENT_UNKNOWN_COMMAND,
)
from PROJECT.channels.telegram.parser import parse_update
from PROJECT.conversations.profile_intake import parser as profile_parser
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.keyboards import profile_confirm_keyboard, profile_followup_keyboard, profile_input_keyboard
from PROJECT.conversations.profile_intake.states import STATE_PROFILE_CONFIRM, STATE_PROFILE_FOLLOWUP, STATE_PROFILE_INPUT
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.command_router import (
    ROUTE_CANCEL,
    ROUTE_GO_BACK,
    ROUTE_HELP,
    ROUTE_MAIN_MENU,
    ROUTE_OPEN_PROFILE,
    ROUTE_PARSE_PROFILE,
    ROUTE_PROFILE_EDIT,
    ROUTE_PROFILE_FINALIZE,
    ROUTE_PROFILE_FOLLOWUP,
    ROUTE_SHOW_DATE,
    ROUTE_SHOW_WEATHER,
    ROUTE_SHOW_WEATHER_MENU,
    route_message,
)
from PROJECT.dispatch.input_fallback import fallback_key_for_state
from PROJECT.dispatch.session_dispatcher import (
    cancel_session,
    current_state,
    go_back,
    profile_draft,
    reset_session,
    set_pending_slot,
    set_profile_draft,
    set_selected_city,
    set_state,
)


async def text_message(update, context) -> None:
    inbound = parse_update(update)
    intent, payload = text_to_intent(inbound.text)
    if intent == INTENT_UNKNOWN_TEXT:
        payload = {"text": inbound.text}
    decision = route_message(current_state(context.user_data), intent, payload)

    if decision.route == ROUTE_HELP:
        await send_text(
            update,
            service.help_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    if decision.route == ROUTE_MAIN_MENU:
        reset_session(context.user_data)
        await send_text(
            update,
            service.main_menu_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    if decision.route == ROUTE_OPEN_PROFILE:
        reset_session(context.user_data)
        set_state(context.user_data, STATE_PROFILE_INPUT)
        set_profile_draft(context.user_data, None)
        set_pending_slot(context.user_data, None)
        await send_text(
            update,
            profile_service.entry_text(),
            keyboard_layout=profile_input_keyboard(),
        )
        return

    if decision.route == ROUTE_CANCEL:
        cancel_session(context.user_data)
        await send_text(
            update,
            service.cancel_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    if decision.route == ROUTE_GO_BACK:
        previous_state = go_back(context.user_data)
        message = service.back_text(previous_state)
        await send_text(
            update,
            message,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    if decision.route == ROUTE_PARSE_PROFILE:
        draft = profile_parser.parse_profile_text(payload["text"])
        set_profile_draft(context.user_data, draft.to_dict())
        set_pending_slot(context.user_data, draft.pending_slot)
        if draft.parse_status == profile_parser.PARSE_PARSED:
            set_state(context.user_data, STATE_PROFILE_CONFIRM, push_history=True)
            await send_text(
                update,
                profile_service.build_confirmation_message(draft),
                keyboard_layout=profile_confirm_keyboard(),
            )
            return
        set_state(context.user_data, STATE_PROFILE_FOLLOWUP, push_history=True)
        await send_text(
            update,
            profile_service.build_followup_message(draft),
            keyboard_layout=profile_followup_keyboard(list(draft.followup_options)),
        )
        return

    if decision.route == ROUTE_PROFILE_FOLLOWUP:
        draft_dict = profile_draft(context.user_data)
        if not draft_dict:
            set_state(context.user_data, STATE_PROFILE_INPUT)
            await send_text(update, profile_service.entry_text(), keyboard_layout=profile_input_keyboard())
            return
        updated_draft = profile_parser.apply_followup_response(profile_parser.ProfileDraft(**draft_dict), inbound.text)
        set_profile_draft(context.user_data, updated_draft.to_dict())
        set_pending_slot(context.user_data, updated_draft.pending_slot)
        if updated_draft.parse_status == profile_parser.PARSE_PARSED:
            set_state(context.user_data, STATE_PROFILE_CONFIRM)
            await send_text(
                update,
                profile_service.build_confirmation_message(updated_draft),
                keyboard_layout=profile_confirm_keyboard(),
            )
            return
        await send_text(
            update,
            profile_service.build_followup_message(updated_draft),
            keyboard_layout=profile_followup_keyboard(list(updated_draft.followup_options)),
        )
        return

    if decision.route == ROUTE_PROFILE_EDIT:
        set_state(context.user_data, STATE_PROFILE_INPUT)
        set_profile_draft(context.user_data, None)
        set_pending_slot(context.user_data, None)
        await send_text(
            update,
            profile_service.edit_text(),
            keyboard_layout=profile_input_keyboard(),
        )
        return

    if decision.route == ROUTE_PROFILE_FINALIZE:
        set_state(context.user_data, STATE_MAIN_MENU)
        set_pending_slot(context.user_data, None)
        await send_text(
            update,
            profile_service.confirmed_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_DATE:
        await send_text(
            update,
            service.today_date_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_WEATHER_MENU:
        set_state(context.user_data, decision.next_state, push_history=decision.push_history)
        await send_text(
            update,
            service.weather_menu_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_WEATHER:
        city = decision.payload["city"]
        set_selected_city(context.user_data, city)
        try:
            snapshot = await service.fetch_weather(city, context.bot_data["settings"])
            message = service.weather_result_text(snapshot)
        except httpx.HTTPError:
            message = service.weather_error_text()
        await send_text(
            update,
            message,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
        )
        return

    await send_text(
        update,
        service.fallback_text(fallback_key_for_state(current_state(context.user_data))),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
    )


async def unknown_command(update, context) -> None:
    inbound = parse_update(update)
    intent = command_to_intent(inbound.command)
    if intent != INTENT_UNKNOWN_COMMAND:
        return
    await send_text(
        update,
        service.unknown_command_text(),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data)),
    )
