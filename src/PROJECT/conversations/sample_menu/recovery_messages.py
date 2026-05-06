from typing import Any


def render_fallback_message(
    *,
    fallback_key: str,
    catalog,
    recovery_context: dict[str, Any] | Any | None = None,
) -> str:
    base_message = catalog.FALLBACK_MESSAGES[fallback_key]
    guidance = _render_recovery_guidance(recovery_context, catalog)
    if guidance is None:
        return base_message
    return f"{base_message}\n\n{guidance}"


def render_cheap_gate_message(
    *,
    result,
    fallback_key: str,
    catalog,
    recovery_context: dict[str, Any] | Any | None = None,
) -> str:
    if result.reason == "explicit_support_request":
        base_message = catalog.CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE
    elif result.reason == "manual_handoff_request":
        base_message = catalog.CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE
    elif result.reason == "recovery_retry_limit_exceeded":
        base_message = catalog.CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE
    else:
        base_message = catalog.FALLBACK_MESSAGES[fallback_key]

    guidance = _render_recovery_guidance(recovery_context, catalog)
    if guidance is None:
        return base_message
    return f"{base_message}\n\n{guidance}"


def _render_recovery_guidance(recovery_context: dict[str, Any] | Any | None, catalog) -> str | None:
    if recovery_context is None:
        return None

    if isinstance(recovery_context, dict):
        current_question = str(recovery_context.get("current_question") or "").strip()
        metadata = recovery_context.get("metadata") or {}
    else:
        current_question = recovery_context.current_question.strip()
        metadata = recovery_context.metadata

    if not current_question and not metadata.get("step_progress"):
        return None

    headline = _guidance_headline(metadata.get("recovery_policy_level"), catalog)
    lines = [headline]

    step_progress = str(metadata.get("step_progress") or "").strip()
    if step_progress:
        lines.append(f"{catalog.RECOVERY_CURRENT_STEP_LABEL}: {step_progress}")

    input_mode_hint = _input_mode_hint(catalog, metadata.get("input_mode"))
    if input_mode_hint:
        lines.append(input_mode_hint)

    question_hint = _question_hint(current_question)
    if question_hint:
        lines.append(question_hint)

    return "\n".join(lines)


def _guidance_headline(recovery_policy_level: str | None, catalog) -> str:
    if recovery_policy_level == "guided":
        return catalog.RECOVERY_GUIDANCE_GUIDED
    if recovery_policy_level == "escalation_ready":
        return catalog.RECOVERY_GUIDANCE_ESCALATION_READY
    return catalog.RECOVERY_GUIDANCE_SOFT


def _question_hint(current_question: str) -> str | None:
    paragraphs = [part.strip() for part in current_question.split("\n\n") if part.strip()]
    if not paragraphs:
        return None
    lines = [line.strip() for line in paragraphs[0].splitlines() if line.strip()]
    if not lines:
        return None
    if len(lines) >= 2 and len(lines[0]) <= 80:
        return "\n".join(lines[:2])
    if len(paragraphs[0]) <= 140:
        return paragraphs[0]
    return lines[0] or None


def _input_mode_hint(catalog, input_mode: str | None) -> str | None:
    if input_mode == "button_only":
        return catalog.RECOVERY_BUTTON_ONLY_HINT
    if input_mode == "text_allowed":
        return catalog.RECOVERY_TEXT_ALLOWED_HINT
    if input_mode == "location_attachment":
        return catalog.RECOVERY_LOCATION_ATTACHMENT_HINT
    if input_mode == "document_upload":
        return catalog.RECOVERY_DOCUMENT_UPLOAD_HINT
    if input_mode == "status_wait":
        return catalog.RECOVERY_STATUS_WAIT_HINT
    return None
