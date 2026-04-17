import httpx

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.canonical_intents.mapping import command_to_intent, text_to_intent
from PROJECT.canonical_intents.registry import INTENT_UNKNOWN_COMMAND
from PROJECT.channels.telegram.parser import parse_update
from PROJECT.conversations.profile_intake import service as profile_service
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_CONFIRM,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)
from PROJECT.conversations.sample_menu import service
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.dispatch.command_router import (
    ROUTE_CANCEL,
    ROUTE_GO_BACK,
    ROUTE_HELP,
    ROUTE_MAIN_MENU,
    ROUTE_OPEN_PROFILE,
    ROUTE_PROFILE_EDIT,
    ROUTE_PROFILE_FINALIZE,
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
from PROJECT.i18n.catalogs import ko

PROFILE_STATES = {
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
    STATE_PROFILE_CITY,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_BIRTH_MONTH,
    STATE_PROFILE_BIRTH_DAY,
    STATE_PROFILE_CONFIRM,
}


def current_profile(context) -> profile_service.ProfileDraft:
    return profile_service.draft_from_dict(profile_draft(context.user_data))


async def send_profile_prompt(update, context, state: str, text: str | None = None) -> None:
    draft = current_profile(context)
    await send_text(
        update,
        text or profile_service.prompt_for_state(state),
        keyboard_layout=profile_service.keyboard_for_state(state, draft),
    )


async def handle_profile_state(update, context, state: str, text: str) -> bool:
    draft = current_profile(context)

    if state == STATE_PROFILE_NAME:
        name = profile_service.parse_name(text)
        if name is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, name=name).to_dict())
        set_state(context.user_data, STATE_PROFILE_RESIDENCE, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_RESIDENCE)
        return True

    if state == STATE_PROFILE_RESIDENCE:
        residence = profile_service.parse_free_text(text)
        if residence is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, residence=residence).to_dict())
        set_state(context.user_data, STATE_PROFILE_CITY, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_CITY)
        return True

    if state == STATE_PROFILE_CITY:
        city = profile_service.parse_free_text(text)
        if city is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, city=city).to_dict())
        set_state(context.user_data, STATE_PROFILE_DISTRICT, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_DISTRICT)
        return True

    if state == STATE_PROFILE_DISTRICT:
        district = profile_service.parse_free_text(text)
        if district is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
            return True
        set_profile_draft(context.user_data, profile_service.update_draft(draft, district=district).to_dict())
        set_state(context.user_data, STATE_PROFILE_BIRTH_YEAR, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_YEAR)
        return True

    if state == STATE_PROFILE_BIRTH_YEAR:
        if text == ko.BUTTON_PREV_YEARS:
            updated = profile_service.update_draft(draft, year_page_start=draft.year_page_start - 12)
            set_profile_draft(context.user_data, updated.to_dict())
            await send_profile_prompt(update, context, state)
            return True
        if text == ko.BUTTON_NEXT_YEARS:
            updated = profile_service.update_draft(draft, year_page_start=draft.year_page_start + 12)
            set_profile_draft(context.user_data, updated.to_dict())
            await send_profile_prompt(update, context, state)
            return True

        year = profile_service.parse_year_button(text)
        current_year = profile_service.datetime.now().year
        if year is None or year < 1900 or year > current_year:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
            return True
        updated = profile_service.update_draft(draft, birth_year=year, birth_month=None, birth_day=None)
        set_profile_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_PROFILE_BIRTH_MONTH, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_MONTH)
        return True

    if state == STATE_PROFILE_BIRTH_MONTH:
        month = profile_service.parse_month_button(text)
        if month is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
            return True
        updated = profile_service.update_draft(draft, birth_month=month, birth_day=None)
        set_profile_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_PROFILE_BIRTH_DAY, push_history=True)
        await send_profile_prompt(update, context, STATE_PROFILE_BIRTH_DAY)
        return True

    if state == STATE_PROFILE_BIRTH_DAY:
        day = profile_service.parse_day_button(text)
        if day is None:
            await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
            return True
        updated = profile_service.update_draft(draft, birth_day=day)
        set_profile_draft(context.user_data, updated.to_dict())
        set_state(context.user_data, STATE_PROFILE_CONFIRM, push_history=True)
        await send_text(
            update,
            profile_service.confirmation_text(updated),
            keyboard_layout=profile_service.keyboard_for_state(STATE_PROFILE_CONFIRM, updated),
        )
        return True

    if state == STATE_PROFILE_CONFIRM:
        await send_profile_prompt(update, context, state, profile_service.fallback_text_for_state(state))
        return True

    return False


async def text_message(update, context) -> None:
    inbound = parse_update(update)
    state = current_state(context.user_data)
    intent, payload = text_to_intent(inbound.text)
    decision = route_message(state, intent, payload)

    if decision.route == ROUTE_HELP:
        await send_text(
            update,
            service.help_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_MAIN_MENU:
        reset_session(context.user_data)
        await send_text(
            update,
            service.main_menu_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), None),
        )
        return

    if decision.route == ROUTE_OPEN_PROFILE:
        reset_session(context.user_data)
        set_state(context.user_data, STATE_PROFILE_NAME)
        draft = profile_service.new_draft()
        set_profile_draft(context.user_data, draft.to_dict())
        set_pending_slot(context.user_data, None)
        await send_profile_prompt(update, context, STATE_PROFILE_NAME)
        return

    if decision.route == ROUTE_CANCEL:
        cancel_session(context.user_data)
        await send_text(
            update,
            service.cancel_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), None),
        )
        return

    if decision.route == ROUTE_GO_BACK:
        previous_state = go_back(context.user_data)
        if previous_state in PROFILE_STATES:
            await send_profile_prompt(update, context, previous_state)
            return
        message = service.back_text(previous_state)
        await send_text(
            update,
            message,
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_PROFILE_EDIT:
        set_state(context.user_data, STATE_PROFILE_NAME)
        draft = profile_service.new_draft()
        set_profile_draft(context.user_data, draft.to_dict())
        set_pending_slot(context.user_data, None)
        await send_text(
            update,
            profile_service.edit_text(),
            keyboard_layout=profile_service.keyboard_for_state(STATE_PROFILE_NAME, draft),
        )
        return

    if decision.route == ROUTE_PROFILE_FINALIZE:
        set_state(context.user_data, STATE_MAIN_MENU)
        set_pending_slot(context.user_data, None)
        await send_text(
            update,
            profile_service.confirmed_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
        )
        return

    if state in PROFILE_STATES:
        handled = await handle_profile_state(update, context, state, inbound.text)
        if handled:
            return

    if decision.route == ROUTE_SHOW_DATE:
        await send_text(
            update,
            service.today_date_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
        )
        return

    if decision.route == ROUTE_SHOW_WEATHER_MENU:
        set_state(context.user_data, decision.next_state, push_history=decision.push_history)
        await send_text(
            update,
            service.weather_menu_text(),
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
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
            keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
        )
        return

    await send_text(
        update,
        service.fallback_text(fallback_key_for_state(current_state(context.user_data))),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
    )


async def unknown_command(update, context) -> None:
    inbound = parse_update(update)
    intent = command_to_intent(inbound.command)
    if intent != INTENT_UNKNOWN_COMMAND:
        return
    await send_text(
        update,
        service.unknown_command_text(),
        keyboard_layout=keyboard_layout_for_state(current_state(context.user_data), profile_draft(context.user_data)),
    )
