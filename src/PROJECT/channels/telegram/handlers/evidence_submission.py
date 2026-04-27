from __future__ import annotations

from PROJECT.adapters.outbound.reply_sender import send_text
from PROJECT.conversations.sample_menu.keyboards import keyboard_layout_for_state
from PROJECT.conversations.sample_menu.states import STATE_MAIN_MENU
from PROJECT.conversations.evidence_submission import service as evidence_conversation_service
from PROJECT.conversations.evidence_submission.states import (
    STATE_EVIDENCE_VALIDATING,
    STATE_EVIDENCE_WAITING_DOCUMENT,
    STATE_EVIDENCE_WAITING_LOCATION,
)
from PROJECT.dispatch.session_dispatcher import (
    clear_evidence_submission_draft,
    current_locale,
    current_state,
    evidence_submission_draft,
    reset_recovery_attempts,
    set_evidence_submission_draft,
    set_state,
)
from PROJECT.dispatch.support_handoff_dispatcher import admin_runtime_for_context, create_support_handoff_request
from PROJECT.evidence import EVIDENCE_VALIDATION_OUTCOME_ACCEPTED
from PROJECT.i18n.translator import get_catalog
from PROJECT.telemetry.event_logger import log_event
from PROJECT.telemetry.events import EVIDENCE_MANUAL_REVIEW_REQUESTED

DEFAULT_EVIDENCE_REQUEST_TYPE = "field_photo"
DEFAULT_EVIDENCE_REQUEST_REASON = "manual_submission"
DEFAULT_EVIDENCE_REQUESTED_VIA = "chat_command"


def _catalog(context):
    return get_catalog(current_locale(context.user_data))


def _evidence_service(context):
    return getattr(context, "bot_data", {}).get("evidence_submission_service")


def _draft(context):
    return evidence_conversation_service.draft_from_dict(evidence_submission_draft(context.user_data))


async def _stage_document_if_possible(context, document):
    stager = getattr(context, "bot_data", {}).get("evidence_artifact_stager")
    if stager is None or document is None:
        return None
    bot = getattr(context, "bot", None)
    try:
        return await stager.stage_document(bot, document)
    except Exception:
        return None


async def start_evidence_submission_flow(update, context) -> bool:
    evidence_service = _evidence_service(context)
    effective_user = update.effective_user
    effective_chat = update.effective_chat
    catalog = _catalog(context)
    if evidence_service is None or effective_user is None or effective_chat is None:
        await send_text(update, catalog.EVIDENCE_RUNTIME_UNAVAILABLE_MESSAGE)
        return False

    request_context = evidence_service.create_request(
        provider_user_id=str(effective_user.id),
        request_type_code=DEFAULT_EVIDENCE_REQUEST_TYPE,
        request_reason_code=DEFAULT_EVIDENCE_REQUEST_REASON,
        requested_via_code=DEFAULT_EVIDENCE_REQUESTED_VIA,
    )
    session = evidence_service.start_submission_session(
        provider_user_id=str(effective_user.id),
        chat_id=effective_chat.id,
        request_event_id=request_context.request_event.id,
        draft_payload={"request_type_code": DEFAULT_EVIDENCE_REQUEST_TYPE},
    )
    field_label = request_context.field_id or request_context.binding_resolution_code
    draft = evidence_conversation_service.new_draft(
        request_event_id=request_context.request_event.id,
        session_id=session.id,
        request_type_code=request_context.request_event.request_type_code,
        field_label=field_label,
    )
    set_evidence_submission_draft(context.user_data, draft.to_dict())
    set_state(context.user_data, STATE_EVIDENCE_WAITING_LOCATION)
    reset_recovery_attempts(context.user_data)
    await send_text(
        update,
        evidence_conversation_service.start_text(catalog, draft),
        keyboard_layout=evidence_conversation_service.keyboard_for_state(
            STATE_EVIDENCE_WAITING_LOCATION,
            catalog,
            draft,
        ),
    )
    return True


async def handle_evidence_location(update, context) -> bool:
    if current_state(context.user_data) != STATE_EVIDENCE_WAITING_LOCATION:
        return False
    evidence_service = _evidence_service(context)
    message = update.effective_message
    draft = _draft(context)
    if evidence_service is None or message is None or message.location is None or draft is None:
        return False
    accepted = evidence_service.accept_location(
        draft.session_id,
        latitude=message.location.latitude,
        longitude=message.location.longitude,
        accuracy_meters=message.location.horizontal_accuracy,
    )
    updated = evidence_conversation_service.update_draft(
        draft,
        accepted_location=True,
        accepted_latitude=accepted.accepted_location_latitude,
        accepted_longitude=accepted.accepted_location_longitude,
        accepted_accuracy_meters=accepted.accepted_location_accuracy_meters,
    )
    set_evidence_submission_draft(context.user_data, updated.to_dict())
    set_state(context.user_data, STATE_EVIDENCE_WAITING_DOCUMENT, push_history=True)
    reset_recovery_attempts(context.user_data)
    catalog = _catalog(context)
    await send_text(
        update,
        evidence_conversation_service.prompt_for_state(STATE_EVIDENCE_WAITING_DOCUMENT, catalog, updated),
        keyboard_layout=evidence_conversation_service.keyboard_for_state(
            STATE_EVIDENCE_WAITING_DOCUMENT,
            catalog,
            updated,
        ),
    )
    return True


async def handle_evidence_document(update, context) -> bool:
    if current_state(context.user_data) != STATE_EVIDENCE_WAITING_DOCUMENT:
        return False
    evidence_service = _evidence_service(context)
    message = update.effective_message
    draft = _draft(context)
    if evidence_service is None or message is None or message.document is None or draft is None:
        return False
    staged_artifact = await _stage_document_if_possible(context, message.document)
    submission = evidence_service.register_document_upload(
        draft.session_id,
        provider_file_id=message.document.file_id,
        provider_file_unique_id=message.document.file_unique_id,
        provider_message_id=str(message.message_id),
        file_name=message.document.file_name,
        mime_type=message.document.mime_type,
        file_size_bytes=message.document.file_size,
        staged_artifact_uri=staged_artifact.artifact_uri if staged_artifact is not None else None,
        checksum_sha256=staged_artifact.checksum_sha256 if staged_artifact is not None else None,
        payload={"telegram_document": True},
    )
    updated = evidence_conversation_service.update_draft(
        draft,
        document_uploaded=True,
        provider_file_id=submission.provider_file_id or "",
        provider_file_unique_id=submission.provider_file_unique_id or "",
        file_name=submission.file_name or "",
        mime_type=submission.mime_type or "",
        file_size_bytes=submission.file_size_bytes,
        evidence_submission_id=submission.id,
        artifact_status_code=submission.artifact_status_code,
    )
    set_evidence_submission_draft(context.user_data, updated.to_dict())
    set_state(context.user_data, STATE_EVIDENCE_VALIDATING, push_history=True)
    reset_recovery_attempts(context.user_data)
    decision = evidence_service.evaluate_submission(submission.id)
    updated = evidence_conversation_service.update_draft(
        updated,
        artifact_status_code=decision.artifact_status_code,
    )
    set_evidence_submission_draft(context.user_data, updated.to_dict())
    catalog = _catalog(context)
    if decision.outcome_code == EVIDENCE_VALIDATION_OUTCOME_ACCEPTED:
        set_state(context.user_data, STATE_MAIN_MENU)
        await send_text(
            update,
            evidence_conversation_service.accepted_text(catalog, updated),
            keyboard_layout=keyboard_layout_for_state(STATE_MAIN_MENU, catalog, None),
        )
        return True

    manual_review = evidence_service.assess_manual_review_requirement(submission.id, decision)
    if manual_review.required:
        escalated_submission = evidence_service.escalate_submission_manual_review(
            submission.id,
            trigger_reason_code=manual_review.trigger_reason_code or "manual_review_required",
            detail={
                "reason_codes": list(decision.reason_codes),
                "location_distance_meters": decision.location_distance_meters,
            },
        )
        updated = evidence_conversation_service.update_draft(
            updated,
            artifact_status_code=escalated_submission.artifact_status_code,
        )
        summary = (
            f"evidence_submission session={draft.session_id} "
            f"submission={submission.id} "
            f"file={updated.file_name or '-'} "
            f"reasons={','.join(decision.reason_codes) or '-'}"
        )
        create_support_handoff_request(
            context.user_data,
            route_hint="admin_follow_up_queue",
            reason="evidence_submission_manual_review",
            current_step=STATE_EVIDENCE_WAITING_DOCUMENT,
            chat_id=update.effective_chat.id if update.effective_chat is not None else None,
            user_id=update.effective_user.id if update.effective_user is not None else None,
            locale=current_locale(context.user_data),
            user_message=summary,
            failure_count=manual_review.rejected_submission_count,
            recent_messages_summary=summary,
            source="evidence_submission_manual_review",
            runtime=admin_runtime_for_context(context),
        )
        log_event(
            EVIDENCE_MANUAL_REVIEW_REQUESTED,
            submission_id=submission.id,
            session_id=draft.session_id,
            trigger_reason_code=manual_review.trigger_reason_code,
            rejected_submission_count=manual_review.rejected_submission_count,
            reason_codes=list(decision.reason_codes),
        )
        clear_evidence_submission_draft(context.user_data)
        set_state(context.user_data, STATE_MAIN_MENU)
        await send_text(
            update,
            evidence_conversation_service.manual_review_text(
                catalog,
                updated,
                reason_codes=decision.reason_codes,
            ),
            keyboard_layout=keyboard_layout_for_state(STATE_MAIN_MENU, catalog, None),
        )
        return True

    set_state(context.user_data, STATE_EVIDENCE_WAITING_DOCUMENT)
    await send_text(
        update,
        evidence_conversation_service.retry_text(
            catalog,
            updated,
            reason_codes=decision.reason_codes,
        ),
        keyboard_layout=evidence_conversation_service.keyboard_for_state(
            STATE_EVIDENCE_WAITING_DOCUMENT,
            catalog,
            updated,
        ),
    )
    return True
