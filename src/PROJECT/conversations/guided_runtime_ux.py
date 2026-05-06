BUTTON_ONLY = "button_only"
TEXT_ALLOWED = "text_allowed"
LOCATION_ATTACHMENT = "location_attachment"
DOCUMENT_UPLOAD = "document_upload"
STATUS_WAIT = "status_wait"


def format_guided_message(
    catalog,
    *,
    flow_label: str,
    progress_label: str,
    input_mode: str | None,
    prompt_text: str,
    draft_summary: str | None = None,
) -> str:
    header = f"{flow_label} {progress_label}".strip()
    input_mode_label = _input_mode_label(catalog, input_mode)
    if input_mode_label:
        header = f"{header} · {input_mode_label}"

    parts = [header]
    if draft_summary:
        parts.append(f"{catalog.GUIDED_DRAFT_SUMMARY_PREFIX}: {draft_summary}")
    parts.append(prompt_text)
    return "\n".join(part for part in parts if part)


def format_waiting_message(
    catalog,
    *,
    flow_label: str,
    progress_label: str,
    prompt_text: str,
    draft_summary: str | None = None,
    next_actions: tuple[str, ...] = (),
) -> str:
    message = format_guided_message(
        catalog,
        flow_label=flow_label,
        progress_label=progress_label,
        input_mode=STATUS_WAIT,
        prompt_text=prompt_text,
        draft_summary=draft_summary,
    )
    if not next_actions:
        return message
    return (
        f"{message}\n\n"
        f"{catalog.GUIDED_NEXT_ACTIONS_LABEL}: "
        f"{', '.join(f'[{action}]' for action in next_actions)}"
    )


def format_text_input_prompt(
    catalog,
    *,
    prompt_text: str,
    examples: tuple[str, ...] = (),
    unsupported_hint: str | None = None,
) -> str:
    parts = [prompt_text, catalog.GUIDED_TEXT_VALUE_ONLY_HINT]
    if examples:
        parts.append(f"{catalog.GUIDED_TEXT_EXAMPLES_LABEL}: {', '.join(examples)}")
    if unsupported_hint:
        parts.append(f"{catalog.GUIDED_TEXT_NOT_SUPPORTED_LABEL}: {unsupported_hint}")
    return "\n".join(part for part in parts if part)


def _input_mode_label(catalog, input_mode: str | None) -> str:
    if input_mode == BUTTON_ONLY:
        return catalog.GUIDED_INPUT_MODE_BUTTON_ONLY
    if input_mode == TEXT_ALLOWED:
        return catalog.GUIDED_INPUT_MODE_TEXT_ALLOWED
    if input_mode == LOCATION_ATTACHMENT:
        return catalog.GUIDED_INPUT_MODE_LOCATION_ATTACHMENT
    if input_mode == DOCUMENT_UPLOAD:
        return catalog.GUIDED_INPUT_MODE_DOCUMENT_UPLOAD
    if input_mode == STATUS_WAIT:
        return catalog.GUIDED_INPUT_MODE_STATUS_WAIT
    return ""
