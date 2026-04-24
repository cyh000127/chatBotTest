from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

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
        return catalog.ONBOARDING_STARTED_MESSAGE
    if state == STATE_ONBOARDING_NAME:
        return catalog.ONBOARDING_NAME_PROMPT
    if state == STATE_ONBOARDING_PHONE:
        return catalog.ONBOARDING_PHONE_PROMPT
    if state == STATE_ONBOARDING_CONFIRM:
        return confirmation_text(draft, catalog)
    if state == STATE_ONBOARDING_PENDING_APPROVAL:
        return catalog.ONBOARDING_PENDING_APPROVAL_SUBMITTED_MESSAGE
    return catalog.ONBOARDING_ACCESS_REQUIRED_MESSAGE


def fallback_for_state(state: str, catalog) -> str:
    if state == STATE_ONBOARDING_NAME:
        return catalog.ONBOARDING_NAME_FALLBACK
    if state == STATE_ONBOARDING_PHONE:
        return catalog.ONBOARDING_PHONE_FALLBACK
    if state == STATE_ONBOARDING_CONFIRM:
        return catalog.ONBOARDING_CONFIRM_FALLBACK
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
