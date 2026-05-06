from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

from PROJECT.conversations import guided_runtime_ux as guided_ux
from PROJECT.conversations.onboarding.states import (
    STATE_ONBOARDING_CONFIRM,
    STATE_ONBOARDING_LANGUAGE_SELECT,
    STATE_ONBOARDING_NAME,
    STATE_ONBOARDING_PENDING_APPROVAL,
    STATE_ONBOARDING_PHONE,
)
from PROJECT.i18n.translator import LANGUAGE_LABELS, language_keyboard


ALLOWED_PHONE_COUNTRY_CODES = ("+855", "+880")


@dataclass(frozen=True)
class OnboardingDraft:
    invite_code: str | None = None
    project_id: str | None = None
    preferred_locale: str | None = None
    name: str | None = None
    phone_raw: str | None = None
    phone_normalized: str | None = None

    def to_dict(self) -> dict:
        return {key: value for key, value in asdict(self).items() if value is not None}


def draft_from_dict(payload: dict | None) -> OnboardingDraft:
    payload = payload or {}
    return OnboardingDraft(
        invite_code=payload.get("invite_code"),
        project_id=payload.get("project_id"),
        preferred_locale=payload.get("preferred_locale"),
        name=payload.get("name"),
        phone_raw=payload.get("phone_raw"),
        phone_normalized=payload.get("phone_normalized"),
    )


def draft_from_json(payload_json: str | None) -> OnboardingDraft:
    if not payload_json:
        return OnboardingDraft()
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError:
        return OnboardingDraft()
    if not isinstance(payload, dict):
        return OnboardingDraft()
    return draft_from_dict(payload)


def update_draft(draft: OnboardingDraft, **changes) -> OnboardingDraft:
    payload = draft.to_dict()
    payload.update({key: value for key, value in changes.items() if value is not None})
    return draft_from_dict(payload)


def draft_ready_for_submission(draft: OnboardingDraft) -> bool:
    return bool(draft.preferred_locale and draft.name and draft.phone_normalized)


def parse_name(text: str) -> str | None:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return None
    if len(normalized) > 80:
        return None
    if not any(ch.isalpha() for ch in normalized):
        return None
    return normalized


def normalize_phone(text: str) -> str | None:
    compact = re.sub(r"[\s().-]", "", text.strip())
    if compact.startswith("00"):
        compact = f"+{compact[2:]}"
    elif compact.startswith(tuple(code[1:] for code in ALLOWED_PHONE_COUNTRY_CODES)):
        compact = f"+{compact}"

    if not re.fullmatch(r"\+\d{8,15}", compact):
        return None
    if not compact.startswith(ALLOWED_PHONE_COUNTRY_CODES):
        return None
    return compact


def prompt_for_state(state: str, catalog, draft: OnboardingDraft | None = None) -> str:
    draft = draft or OnboardingDraft()
    if state == STATE_ONBOARDING_LANGUAGE_SELECT:
        return guided_ux.format_guided_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label="1/3",
            input_mode=guided_ux.BUTTON_ONLY,
            prompt_text=catalog.ONBOARDING_STARTED_MESSAGE,
        )
    if state == STATE_ONBOARDING_NAME:
        return guided_ux.format_guided_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label="2/3",
            input_mode=guided_ux.TEXT_ALLOWED,
            prompt_text=_text_prompt_for_state(STATE_ONBOARDING_NAME, catalog),
            draft_summary=_draft_summary(draft, catalog),
        )
    if state == STATE_ONBOARDING_PHONE:
        return guided_ux.format_guided_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label="3/3",
            input_mode=guided_ux.TEXT_ALLOWED,
            prompt_text=_text_prompt_for_state(STATE_ONBOARDING_PHONE, catalog),
            draft_summary=_draft_summary(draft, catalog),
        )
    if state == STATE_ONBOARDING_CONFIRM:
        return guided_ux.format_guided_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label=catalog.GUIDED_REVIEW_STAGE_LABEL,
            input_mode=guided_ux.BUTTON_ONLY,
            prompt_text=confirmation_text(draft, catalog),
        )
    if state == STATE_ONBOARDING_PENDING_APPROVAL:
        return guided_ux.format_waiting_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label=catalog.GUIDED_RECEIVED_STAGE_LABEL,
            prompt_text=catalog.ONBOARDING_PENDING_APPROVAL_SUBMITTED_MESSAGE,
            draft_summary=_draft_summary(draft, catalog),
            next_actions=(catalog.BUTTON_SUPPORT, catalog.BUTTON_RESTART),
        )
    return catalog.ONBOARDING_ACCESS_REQUIRED_MESSAGE


def fallback_for_state(state: str, catalog, draft: OnboardingDraft | None = None) -> str:
    draft = draft or OnboardingDraft()
    if state == STATE_ONBOARDING_NAME:
        return guided_ux.format_guided_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label="2/3",
            input_mode=guided_ux.TEXT_ALLOWED,
            prompt_text=_text_prompt_for_state(
                STATE_ONBOARDING_NAME,
                catalog,
                prompt_text=catalog.ONBOARDING_NAME_FALLBACK,
            ),
            draft_summary=_draft_summary(draft, catalog),
        )
    if state == STATE_ONBOARDING_PHONE:
        return guided_ux.format_guided_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label="3/3",
            input_mode=guided_ux.TEXT_ALLOWED,
            prompt_text=_text_prompt_for_state(
                STATE_ONBOARDING_PHONE,
                catalog,
                prompt_text=catalog.ONBOARDING_PHONE_FALLBACK,
            ),
            draft_summary=_draft_summary(draft, catalog),
        )
    if state == STATE_ONBOARDING_CONFIRM:
        return guided_ux.format_guided_message(
            catalog,
            flow_label=catalog.GUIDED_FLOW_ONBOARDING,
            progress_label=catalog.GUIDED_REVIEW_STAGE_LABEL,
            input_mode=guided_ux.BUTTON_ONLY,
            prompt_text=catalog.ONBOARDING_CONFIRM_FALLBACK,
        )
    if state == STATE_ONBOARDING_PENDING_APPROVAL:
        return prompt_for_state(state, catalog, draft)
    return catalog.ONBOARDING_ACCESS_REQUIRED_MESSAGE


def keyboard_for_state(state: str, catalog) -> list[list[dict[str, str]]] | None:
    if state == STATE_ONBOARDING_LANGUAGE_SELECT:
        return language_keyboard()
    if state == STATE_ONBOARDING_CONFIRM:
        return [
            [{"text": catalog.BUTTON_CONFIRM, "data": "onboarding:confirm"}],
            [
                {"text": catalog.BUTTON_EDIT_NAME, "data": "onboarding:edit:name"},
                {"text": catalog.BUTTON_EDIT_PHONE, "data": "onboarding:edit:phone"},
            ],
            [{"text": catalog.BUTTON_RESTART, "data": "intent:restart"}],
            [{"text": catalog.BUTTON_SUPPORT, "data": "intent:support.escalate"}],
        ]
    if state in {STATE_ONBOARDING_NAME, STATE_ONBOARDING_PHONE, STATE_ONBOARDING_PENDING_APPROVAL}:
        return [
            [{"text": catalog.BUTTON_RESTART, "data": "intent:restart"}],
            [{"text": catalog.BUTTON_SUPPORT, "data": "intent:support.escalate"}],
        ]
    return None


def confirmation_text(draft: OnboardingDraft, catalog) -> str:
    language_label = LANGUAGE_LABELS.get(draft.preferred_locale or "", draft.preferred_locale or "-")
    return catalog.ONBOARDING_CONFIRM_MESSAGE.format(
        name=draft.name or "-",
        phone=draft.phone_normalized or "-",
        language=language_label,
    )


def _text_prompt_for_state(state: str, catalog, *, prompt_text: str | None = None) -> str:
    if state == STATE_ONBOARDING_NAME:
        return guided_ux.format_text_input_prompt(
            catalog,
            prompt_text=prompt_text or catalog.ONBOARDING_NAME_PROMPT,
            examples=catalog.ONBOARDING_NAME_EXAMPLES,
            unsupported_hint=catalog.ONBOARDING_NAME_UNSUPPORTED_INPUT_HINT,
        )
    if state == STATE_ONBOARDING_PHONE:
        return guided_ux.format_text_input_prompt(
            catalog,
            prompt_text=prompt_text or catalog.ONBOARDING_PHONE_PROMPT,
            examples=catalog.ONBOARDING_PHONE_EXAMPLES,
            unsupported_hint=catalog.ONBOARDING_PHONE_UNSUPPORTED_INPUT_HINT,
        )
    return prompt_text or ""


def _draft_summary(draft: OnboardingDraft, catalog) -> str | None:
    parts: list[str] = []
    if draft.preferred_locale:
        parts.append(
            f"{catalog.ONBOARDING_DRAFT_LANGUAGE_LABEL}="
            f"{LANGUAGE_LABELS.get(draft.preferred_locale, draft.preferred_locale)}"
        )
    if draft.name:
        parts.append(f"{catalog.ONBOARDING_DRAFT_NAME_LABEL}={draft.name}")
    if draft.phone_normalized:
        parts.append(f"{catalog.ONBOARDING_DRAFT_PHONE_LABEL}={draft.phone_normalized}")
    return ", ".join(parts) if parts else None
