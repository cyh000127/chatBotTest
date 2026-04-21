import json
from dataclasses import dataclass

import httpx

from PROJECT.llm.contracts import (
    LlmRecoveryClassification,
    LlmRecoveryResult,
    LlmRelevance,
)
from PROJECT.rule_engine.contracts import RecoveryContextDraft
from PROJECT.settings import GeminiSettings


class GeminiRecoveryError(RuntimeError):
    pass


class GeminiNotConfiguredError(GeminiRecoveryError):
    pass


class GeminiResponseFormatError(GeminiRecoveryError):
    pass


RECOVERY_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": [classification.value for classification in LlmRecoveryClassification],
        },
        "relevance_to_current_step": {
            "type": "string",
            "enum": [relevance.value for relevance in LlmRelevance],
        },
        "normalized_candidate": {
            "type": "object",
            "additionalProperties": True,
        },
        "candidate_confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "needs_clarification": {"type": "boolean"},
        "clarification_question": {"type": "string"},
        "needs_human": {"type": "boolean"},
        "human_handoff_reason": {"type": "string"},
        "safety_flags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reason": {"type": "string"},
    },
    "required": [
        "classification",
        "relevance_to_current_step",
        "needs_clarification",
        "needs_human",
        "safety_flags",
    ],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class GeminiRecoveryClassifier:
    settings: GeminiSettings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.api_key)

    async def classify(self, recovery_context: RecoveryContextDraft) -> LlmRecoveryResult:
        if not self.enabled:
            raise GeminiNotConfiguredError("GEMINI_API_KEY 가 설정되지 않았습니다.")

        payload = build_gemini_recovery_request(recovery_context)
        response_json = await self._generate_content(payload)
        response_text = extract_gemini_text(response_json)
        return parse_gemini_recovery_text(response_text)

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


def build_gemini_recovery_request(recovery_context: RecoveryContextDraft) -> dict:
    return {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": build_recovery_prompt(recovery_context),
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": RECOVERY_RESPONSE_JSON_SCHEMA,
            "temperature": 0.1,
        },
    }


def build_recovery_prompt(recovery_context: RecoveryContextDraft) -> str:
    payload = {
        "canonical_intent": recovery_context.canonical_intent,
        "current_step": recovery_context.current_step,
        "current_question": recovery_context.current_question,
        "expected_input_type": recovery_context.expected_input_type,
        "allowed_value_shape": recovery_context.allowed_value_shape,
        "latest_user_message": recovery_context.latest_user_message,
        "recent_messages_summary": recovery_context.recent_messages_summary,
        "locale": recovery_context.locale,
        "recovery_attempt_count": recovery_context.recovery_attempt_count,
        "hard_constraints": list(recovery_context.hard_constraints),
        "metadata": recovery_context.metadata,
    }
    return (
        "You are a current-step recovery classifier for a Telegram farming workflow.\n"
        "Classify only the latest user message for the current step.\n"
        "Do not invent missing values that are not grounded in the user message.\n"
        "Do not approve or reject submissions.\n"
        "Return JSON only that matches the provided schema.\n\n"
        f"Recovery context:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def extract_gemini_text(response_json: dict) -> str:
    candidates = response_json.get("candidates") or []
    if not candidates:
        raise GeminiResponseFormatError("Gemini 응답에 candidates 가 없습니다.")

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    texts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")]
    if not texts:
        raise GeminiResponseFormatError("Gemini 응답에서 text part 를 찾지 못했습니다.")
    return "\n".join(texts).strip()


def parse_gemini_recovery_text(response_text: str) -> LlmRecoveryResult:
    parsed = json.loads(_extract_json_text(response_text))
    return LlmRecoveryResult(
        classification=LlmRecoveryClassification(parsed["classification"]),
        relevance_to_current_step=LlmRelevance(parsed["relevance_to_current_step"]),
        normalized_candidate=parsed.get("normalized_candidate"),
        candidate_confidence=parsed.get("candidate_confidence"),
        needs_clarification=bool(parsed.get("needs_clarification", False)),
        clarification_question=parsed.get("clarification_question"),
        needs_human=bool(parsed.get("needs_human", False)),
        human_handoff_reason=parsed.get("human_handoff_reason"),
        safety_flags=tuple(parsed.get("safety_flags", [])),
        reason=parsed.get("reason"),
    )


def _extract_json_text(response_text: str) -> str:
    stripped = response_text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```JSON").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    json.loads(stripped)
    return stripped
