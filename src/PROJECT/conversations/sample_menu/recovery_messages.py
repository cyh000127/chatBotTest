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
    STATE_YIELD_EDIT_SELECT,
    STATE_YIELD_FIELD,
    STATE_YIELD_READY,
)
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
        current_step = str(recovery_context.get("current_step") or "").strip()
        metadata = recovery_context.get("metadata") or {}
    else:
        current_question = recovery_context.current_question.strip()
        current_step = recovery_context.current_step
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

    retry_copy = _retry_copy_for_state(current_step, catalog)
    if retry_copy:
        lines.append(retry_copy)

    quick_action_hint = _quick_action_hint(current_step, catalog)
    if quick_action_hint:
        lines.append(quick_action_hint)

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


def _retry_copy_for_state(current_step: str, catalog) -> str | None:
    mapping = {
        STATE_FERTILIZER_USED: catalog.FERTILIZER_USED_FALLBACK,
        STATE_FERTILIZER_KIND: catalog.FERTILIZER_KIND_FALLBACK,
        STATE_FERTILIZER_PRODUCT: catalog.FERTILIZER_PRODUCT_FALLBACK,
        STATE_FERTILIZER_AMOUNT: catalog.FERTILIZER_AMOUNT_FALLBACK,
        STATE_FERTILIZER_DATE: catalog.FERTILIZER_DATE_FALLBACK,
        STATE_FERTILIZER_CONFIRM: catalog.FERTILIZER_CONFIRM_FALLBACK,
        STATE_YIELD_READY: catalog.YIELD_READY_FALLBACK,
        STATE_YIELD_FIELD: catalog.YIELD_FIELD_FALLBACK,
        STATE_YIELD_AMOUNT: catalog.YIELD_AMOUNT_FALLBACK,
        STATE_YIELD_DATE: catalog.YIELD_DATE_FALLBACK,
        STATE_YIELD_CONFIRM: catalog.YIELD_CONFIRM_FALLBACK,
        STATE_YIELD_EDIT_SELECT: catalog.YIELD_EDIT_SELECT_FALLBACK,
        STATE_FIELD_BINDING_METHOD: getattr(catalog, "MYFIELDS_METHOD_PROMPT", None),
        STATE_FIELD_BINDING_LOCATION: catalog.MYFIELDS_LOCATION_PROMPT,
        STATE_FIELD_BINDING_CODE: catalog.MYFIELDS_CODE_PROMPT,
        STATE_FIELD_BINDING_CANDIDATE_SELECT: catalog.MYFIELDS_CANDIDATE_PROMPT,
        STATE_FIELD_BINDING_CONFIRM: catalog.MYFIELDS_CONFIRM_GUIDANCE,
        STATE_INPUT_RESOLVE_TARGET: catalog.INPUT_RESOLVE_TARGET_FALLBACK,
        STATE_INPUT_RESOLVE_METHOD: catalog.INPUT_RESOLVE_METHOD_FALLBACK,
        STATE_INPUT_RESOLVE_RAW_INPUT: catalog.INPUT_RESOLVE_RAW_INPUT_FALLBACK,
        STATE_INPUT_RESOLVE_CANDIDATES: catalog.FALLBACK_MESSAGES["input_resolve_confirm"],
        STATE_INPUT_RESOLVE_DECISION: catalog.INPUT_RESOLVE_DECISION_PROMPT,
        STATE_EVIDENCE_WAITING_LOCATION: catalog.EVIDENCE_LOCATION_FALLBACK,
        STATE_EVIDENCE_WAITING_DOCUMENT: catalog.EVIDENCE_DOCUMENT_FALLBACK,
        STATE_EVIDENCE_VALIDATING: catalog.EVIDENCE_VALIDATING_MESSAGE,
        STATE_MYFIELDS_SUMMARY: catalog.MYFIELDS_SUMMARY_GUIDANCE,
    }
    return mapping.get(current_step)


def _quick_action_hint(current_step: str, catalog) -> str | None:
    actions = _quick_action_labels(current_step, catalog)
    if not actions:
        return None
    return f"{catalog.RECOVERY_QUICK_ACTIONS_LABEL}: {', '.join(f'[{action}]' for action in actions)}"


def _quick_action_labels(current_step: str, catalog) -> tuple[str, ...]:
    if current_step == STATE_FERTILIZER_USED:
        return (catalog.BUTTON_YES, catalog.BUTTON_NO, catalog.BUTTON_BACK)
    if current_step == STATE_FERTILIZER_KIND:
        return (
            catalog.BUTTON_FERTILIZER_KIND_COMPOUND,
            catalog.BUTTON_FERTILIZER_KIND_UREA,
            catalog.BUTTON_BACK,
        )
    if current_step in {STATE_FERTILIZER_PRODUCT, STATE_FERTILIZER_AMOUNT, STATE_FERTILIZER_DATE}:
        return (catalog.BUTTON_BACK, catalog.BUTTON_RESTART)
    if current_step == STATE_FERTILIZER_CONFIRM:
        return (catalog.BUTTON_CONFIRM, catalog.BUTTON_BACK, catalog.BUTTON_RESTART)
    if current_step == STATE_YIELD_READY:
        return (catalog.BUTTON_YES, catalog.BUTTON_NO, catalog.BUTTON_BACK)
    if current_step in {STATE_YIELD_FIELD, STATE_YIELD_AMOUNT, STATE_YIELD_DATE}:
        return (catalog.BUTTON_BACK, catalog.BUTTON_RESTART)
    if current_step in {STATE_YIELD_CONFIRM, STATE_YIELD_EDIT_SELECT}:
        return (catalog.BUTTON_CONFIRM, catalog.BUTTON_BACK, catalog.BUTTON_RESTART)
    if current_step == STATE_MYFIELDS_SUMMARY:
        return (
            getattr(catalog, "BUTTON_FIELD_REGISTER", "농지 등록"),
            getattr(catalog, "BUTTON_FIELD_REFRESH", "새로고침"),
            catalog.BUTTON_SUPPORT,
        )
    if current_step == STATE_FIELD_BINDING_METHOD:
        return (
            getattr(catalog, "BUTTON_FIELD_LOOKUP_LOCATION", "위치로 찾기"),
            getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"),
            catalog.BUTTON_BACK,
        )
    if current_step == STATE_FIELD_BINDING_LOCATION:
        return (
            getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"),
            catalog.BUTTON_BACK,
            catalog.BUTTON_RESTART,
        )
    if current_step == STATE_FIELD_BINDING_CODE:
        return (
            getattr(catalog, "BUTTON_FIELD_LOOKUP_LOCATION", "위치로 찾기"),
            catalog.BUTTON_BACK,
            catalog.BUTTON_RESTART,
        )
    if current_step == STATE_FIELD_BINDING_CANDIDATE_SELECT:
        return (
            getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"),
            catalog.BUTTON_BACK,
            catalog.BUTTON_RESTART,
        )
    if current_step == STATE_FIELD_BINDING_CONFIRM:
        return (
            catalog.BUTTON_CONFIRM,
            getattr(catalog, "BUTTON_FIELD_LOOKUP_LOCATION", "위치로 찾기"),
            getattr(catalog, "BUTTON_FIELD_LOOKUP_CODE", "고유 번호 입력"),
        )
    if current_step == STATE_INPUT_RESOLVE_TARGET:
        return (
            catalog.BUTTON_INPUT_RESOLVE_TARGET_FIELD_CODE,
            catalog.BUTTON_INPUT_RESOLVE_TARGET_FIELD_NAME,
            catalog.BUTTON_CANCEL,
        )
    if current_step == STATE_INPUT_RESOLVE_METHOD:
        return (
            catalog.BUTTON_INPUT_RESOLVE_METHOD_TYPED_TEXT,
            catalog.BUTTON_BACK,
            catalog.BUTTON_CANCEL,
        )
    if current_step == STATE_INPUT_RESOLVE_RAW_INPUT:
        return (catalog.BUTTON_BACK, catalog.BUTTON_CANCEL)
    if current_step == STATE_INPUT_RESOLVE_CANDIDATES:
        return (
            catalog.BUTTON_INPUT_RESOLVE_RETRY,
            catalog.BUTTON_INPUT_RESOLVE_RETRY_LATER,
            catalog.BUTTON_INPUT_RESOLVE_MANUAL_REVIEW,
        )
    if current_step == STATE_INPUT_RESOLVE_DECISION:
        return (
            catalog.BUTTON_INPUT_RESOLVE_CONFIRM_CANDIDATE,
            catalog.BUTTON_INPUT_RESOLVE_RETRY,
            catalog.BUTTON_INPUT_RESOLVE_RETRY_LATER,
        )
    if current_step == STATE_EVIDENCE_WAITING_LOCATION:
        return (catalog.BUTTON_SUPPORT, catalog.BUTTON_CANCEL, catalog.BUTTON_RESTART)
    if current_step == STATE_EVIDENCE_WAITING_DOCUMENT:
        return (catalog.BUTTON_SUPPORT, catalog.BUTTON_BACK, catalog.BUTTON_CANCEL)
    if current_step == STATE_EVIDENCE_VALIDATING:
        return (catalog.BUTTON_SUPPORT, catalog.BUTTON_HELP, catalog.BUTTON_RESTART)
    return ()
