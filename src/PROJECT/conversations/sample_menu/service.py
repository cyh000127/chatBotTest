from PROJECT.conversations.sample_menu.recovery_messages import render_cheap_gate_message, render_fallback_message
from PROJECT.conversations.sample_menu.states import STATE_LANGUAGE_SELECT, STATE_MAIN_MENU
from PROJECT.rule_engine.contracts import ValidationResult


def start_text(catalog) -> str:
    return catalog.START_MESSAGE


def help_text(catalog) -> str:
    return catalog.HELP_MESSAGE


def main_menu_text(catalog) -> str:
    return catalog.MAIN_MENU_MESSAGE


def cancel_text(catalog) -> str:
    return catalog.CANCEL_MESSAGE


def back_text(previous_state: str | None, catalog) -> str:
    if previous_state is None:
        return catalog.BACK_LIMIT_MESSAGE
    if previous_state == STATE_MAIN_MENU:
        return catalog.BACK_TO_MAIN_MESSAGE
    if previous_state == STATE_LANGUAGE_SELECT:
        return catalog.BACK_GENERIC_MESSAGE
    return catalog.BACK_GENERIC_MESSAGE


def fallback_text(key: str, catalog, recovery_context=None) -> str:
    return render_fallback_message(
        fallback_key=key,
        catalog=catalog,
        recovery_context=recovery_context,
    )


def cheap_gate_text(result: ValidationResult, fallback_key: str, catalog, recovery_context=None) -> str:
    return render_cheap_gate_message(
        result=result,
        fallback_key=fallback_key,
        catalog=catalog,
        recovery_context=recovery_context,
    )


def unknown_command_text(catalog) -> str:
    return catalog.UNKNOWN_COMMAND_MESSAGE


def myfields_entry_text(catalog) -> str:
    return catalog.MYFIELDS_ENTRY_MESSAGE


def input_resolve_entry_text(catalog) -> str:
    return f"{catalog.INPUT_RESOLVE_ENTRY_MESSAGE}\n\n{catalog.INPUT_RESOLVE_TARGET_PROMPT}"


def support_escalation_text(catalog) -> str:
    return catalog.SUPPORT_ESCALATION_MESSAGE


def language_menu_text(catalog) -> str:
    return catalog.LANGUAGE_MENU_MESSAGE


def language_changed_text(catalog) -> str:
    return catalog.LANGUAGE_CHANGED_MESSAGE
