import asyncio
import json

import pytest

from PROJECT.llm import (
    GeminiNotConfiguredError,
    GeminiRecoveryClassifier,
    LlmRecoveryClassification,
    build_gemini_recovery_request,
    build_recovery_prompt,
    extract_gemini_text,
    parse_gemini_recovery_text,
)
from PROJECT.rule_engine.contracts import RecoveryContextDraft
from PROJECT.settings import GeminiSettings


def sample_recovery_context() -> RecoveryContextDraft:
    return RecoveryContextDraft(
        canonical_intent="fertilizer.input.start",
        current_step="fertilizer_amount",
        current_question="사용량을 입력해주세요.",
        expected_input_type="amount_with_unit",
        allowed_value_shape="supported_amount_unit_pair",
        latest_user_message="대충 스무 킬로쯤 넣었어요",
        recent_messages_summary="User already selected compound fertilizer and now answers amount.",
        locale="ko",
        recovery_attempt_count=1,
        hard_constraints=(
            "Do not invent missing values",
            "Ask at most one clarification question",
        ),
    )


def test_build_recovery_prompt_includes_structured_context():
    prompt = build_recovery_prompt(sample_recovery_context())

    assert "current-step recovery classifier" in prompt
    assert "\"current_step\": \"fertilizer_amount\"" in prompt
    assert "\"latest_user_message\": \"대충 스무 킬로쯤 넣었어요\"" in prompt


def test_build_gemini_recovery_request_uses_json_mode():
    payload = build_gemini_recovery_request(sample_recovery_context())

    assert payload["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseJsonSchema" in payload["generationConfig"]
    assert payload["contents"][0]["role"] == "user"


def test_extract_gemini_text_joins_candidate_parts():
    response_json = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "{\"classification\":\"needs_clarification\","},
                        {"text": "\"relevance_to_current_step\":\"high\",\"needs_clarification\":true,\"needs_human\":false,\"safety_flags\":[]}"},
                    ]
                }
            }
        ]
    }

    text = extract_gemini_text(response_json)

    assert "\"classification\":\"needs_clarification\"" in text


def test_parse_gemini_recovery_text_accepts_json_fence():
    response_text = """```json
{
  "classification": "needs_clarification",
  "relevance_to_current_step": "high",
  "normalized_candidate": {
    "amount_text": "스무 킬로"
  },
  "candidate_confidence": 0.64,
  "needs_clarification": true,
  "clarification_question": "숫자와 단위를 함께 입력해주세요. 예: 20kg",
  "needs_human": false,
  "human_handoff_reason": null,
  "safety_flags": [],
  "reason": "Numeric amount is implied but not explicit enough."
}
```"""

    result = parse_gemini_recovery_text(response_text)

    assert result.classification == LlmRecoveryClassification.NEEDS_CLARIFICATION
    assert result.normalized_candidate == {"amount_text": "스무 킬로"}
    assert result.needs_human is False


def test_classifier_raises_when_gemini_not_configured():
    classifier = GeminiRecoveryClassifier(
        GeminiSettings(
            api_key="",
            model="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta",
            timeout_seconds=15.0,
        )
    )

    with pytest.raises(GeminiNotConfiguredError):
        asyncio.run(classifier.classify(sample_recovery_context()))
