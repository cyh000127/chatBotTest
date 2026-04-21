import asyncio

import pytest

from PROJECT.llm import (
    GeminiEditIntentResolver,
    GeminiNotConfiguredError,
    LlmEditAction,
    build_edit_intent_prompt,
    build_gemini_edit_intent_request,
    parse_gemini_edit_intent_text,
)
from PROJECT.settings import GeminiSettings


def test_build_edit_intent_prompt_includes_allowed_actions():
    prompt = build_edit_intent_prompt(
        text="제품명 변경하고 싶어",
        locale="ko",
        allowed_actions=(
            LlmEditAction.FERTILIZER_EDIT_SELECT.value,
            LlmEditAction.FERTILIZER_EDIT_PRODUCT.value,
            LlmEditAction.UNSUPPORTED.value,
        ),
    )

    assert "constrained edit-intent classifier" in prompt
    assert "\"latest_user_message\": \"제품명 변경하고 싶어\"" in prompt
    assert LlmEditAction.FERTILIZER_EDIT_PRODUCT.value in prompt


def test_build_gemini_edit_intent_request_uses_json_mode():
    payload = build_gemini_edit_intent_request(
        text="생일 수정할래",
        locale="ko",
        allowed_actions=(
            LlmEditAction.PROFILE_EDIT_BIRTH_DATE.value,
            LlmEditAction.UNSUPPORTED.value,
        ),
    )

    assert payload["generationConfig"]["responseMimeType"] == "application/json"
    assert "responseJsonSchema" in payload["generationConfig"]


def test_parse_gemini_edit_intent_text_accepts_json_fence():
    response_text = """```json
{
  "action": "fertilizer.edit.product",
  "candidate_value": "한아름 복합비료",
  "confidence": 0.88,
  "needs_confirmation": true,
  "needs_human": false,
  "clarification_question": null,
  "reason": "The user explicitly wants to change fertilizer product."
}
```"""

    result = parse_gemini_edit_intent_text(response_text)

    assert result.action == LlmEditAction.FERTILIZER_EDIT_PRODUCT
    assert result.candidate_value == "한아름 복합비료"
    assert result.confidence == 0.88


def test_edit_intent_resolver_raises_when_not_configured():
    resolver = GeminiEditIntentResolver(
        GeminiSettings(
            api_key="",
            model="gemini-2.5-flash",
            api_base="https://generativelanguage.googleapis.com/v1beta",
            timeout_seconds=15.0,
        )
    )

    with pytest.raises(GeminiNotConfiguredError):
        asyncio.run(
            resolver.classify(
                text="제품명 변경할래",
                locale="ko",
                allowed_actions=(
                    LlmEditAction.FERTILIZER_EDIT_PRODUCT.value,
                    LlmEditAction.UNSUPPORTED.value,
                ),
            )
        )
