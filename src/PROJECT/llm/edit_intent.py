import json
from dataclasses import dataclass, field
from enum import StrEnum

import httpx

from PROJECT.llm.gemini_recovery import (
    GeminiNotConfiguredError,
    GeminiRecoveryError,
    GeminiResponseFormatError,
    extract_gemini_text,
)
from PROJECT.settings import GeminiSettings


class LlmEditAction(StrEnum):
    FERTILIZER_EDIT_SELECT = "fertilizer.edit.select"
    FERTILIZER_EDIT_USED = "fertilizer.edit.used"
    FERTILIZER_EDIT_KIND = "fertilizer.edit.kind"
    FERTILIZER_EDIT_PRODUCT = "fertilizer.edit.product"
    FERTILIZER_EDIT_AMOUNT = "fertilizer.edit.amount"
    FERTILIZER_EDIT_DATE = "fertilizer.edit.date"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class LlmEditIntentResult:
    action: LlmEditAction
    candidate_value: str | None = None
    confidence: float | None = None
    needs_confirmation: bool = True
    needs_human: bool = False
    clarification_question: str | None = None
    reason: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


EDIT_INTENT_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [action.value for action in LlmEditAction],
        },
        "candidate_value": {
            "type": "string",
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "needs_confirmation": {"type": "boolean"},
        "needs_human": {"type": "boolean"},
        "clarification_question": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": [
        "action",
        "needs_confirmation",
        "needs_human",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class GeminiEditIntentResolver:
    settings: GeminiSettings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.api_key)

    async def classify(self, *, text: str, locale: str, allowed_actions: tuple[str, ...]) -> LlmEditIntentResult:
        if not self.enabled:
            raise GeminiNotConfiguredError("GEMINI_API_KEY 가 설정되지 않았습니다.")

        payload = build_gemini_edit_intent_request(text=text, locale=locale, allowed_actions=allowed_actions)
        response_json = await self._generate_content(payload)
        response_text = extract_gemini_text(response_json)
        return parse_gemini_edit_intent_text(response_text)

    async def _generate_content(self, payload: dict) -> dict:
        endpoint = f"{self.settings.api_base.rstrip('/')}/models/{self.settings.model}:generateContent"
        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                endpoint,
                headers={
                    "x-goog-api-key": self.settings.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()


def build_gemini_edit_intent_request(*, text: str, locale: str, allowed_actions: tuple[str, ...]) -> dict:
    return {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": build_edit_intent_prompt(text=text, locale=locale, allowed_actions=allowed_actions),
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": EDIT_INTENT_RESPONSE_JSON_SCHEMA,
            "temperature": 0.1,
        },
    }


def build_edit_intent_prompt(*, text: str, locale: str, allowed_actions: tuple[str, ...]) -> str:
    payload = {
        "locale": locale,
        "latest_user_message": text,
        "allowed_actions": list(allowed_actions),
        "rules": [
            "Classify only edit intent for the latest user message.",
            "Return one of the allowed_actions or unsupported.",
            "If a new candidate value is not explicit, return candidate_value as null or omit it.",
            "Do not approve storage, do not finalize any value, and do not invent missing facts.",
            "needs_confirmation must stay true for any supported edit action.",
        ],
    }
    return (
        "You are a constrained edit-intent classifier for a Telegram workflow.\n"
        "Your job is only to identify which edit action the user most likely wants.\n"
        "Return JSON only that matches the provided schema.\n\n"
        f"Edit intent context:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def parse_gemini_edit_intent_text(response_text: str) -> LlmEditIntentResult:
    parsed = json.loads(_extract_json_text(response_text))
    return LlmEditIntentResult(
        action=LlmEditAction(parsed["action"]),
        candidate_value=parsed.get("candidate_value"),
        confidence=parsed.get("confidence"),
        needs_confirmation=bool(parsed.get("needs_confirmation", True)),
        needs_human=bool(parsed.get("needs_human", False)),
        clarification_question=parsed.get("clarification_question"),
        reason=parsed.get("reason"),
    )


def _extract_json_text(response_text: str) -> str:
    stripped = response_text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```JSON").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    try:
        json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise GeminiResponseFormatError("Gemini edit intent 응답이 JSON 형식이 아닙니다.") from exc
    return stripped
