from __future__ import annotations

from PROJECT.conversations import guided_runtime_ux
from PROJECT.storage.fields import FIELD_BINDING_SOURCE_FIELD_CODE, FIELD_BINDING_SOURCE_LOCATION


def _lookup_method_label(method: str, catalog) -> str:
    if method == FIELD_BINDING_SOURCE_LOCATION:
        return getattr(catalog, "MYFIELDS_LOOKUP_METHOD_LOCATION_LABEL", "위치 공유")
    if method == FIELD_BINDING_SOURCE_FIELD_CODE:
        return getattr(catalog, "MYFIELDS_LOOKUP_METHOD_CODE_LABEL", "고유 번호")
    return method


def summary_text(*, participant_name: str, bindings: tuple, catalog) -> str:
    if not bindings:
        return guided_runtime_ux.format_guided_message(
            catalog,
            flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
            progress_label=getattr(catalog, "GUIDED_SUMMARY_STAGE_LABEL", "요약 단계"),
            input_mode=guided_runtime_ux.BUTTON_ONLY,
            prompt_text=getattr(
                catalog,
                "MYFIELDS_EMPTY_MESSAGE",
                f"{participant_name}님에게 등록된 농지가 없습니다.\n농지 등록을 시작해 주세요.",
            ),
        )
    lines = [
        getattr(catalog, "MYFIELDS_SUMMARY_MESSAGE", f"{participant_name}님의 등록된 농지입니다."),
    ]
    for index, binding in enumerate(bindings, start=1):
        lines.append(
            f"{index}. {binding.field.display_name} ({binding.field.field_code})"
        )
    lines.append("")
    lines.append(getattr(catalog, "MYFIELDS_SUMMARY_GUIDANCE", "농지를 더 등록하거나 목록을 새로고침할 수 있습니다."))
    return guided_runtime_ux.format_guided_message(
        catalog,
        flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
        progress_label=getattr(catalog, "GUIDED_SUMMARY_STAGE_LABEL", "요약 단계"),
        input_mode=guided_runtime_ux.BUTTON_ONLY,
        prompt_text="\n".join(lines),
        draft_summary=_draft_summary(catalog, binding_count=len(bindings)),
    )


def method_text(catalog, *, has_bindings: bool = False) -> str:
    return guided_runtime_ux.format_guided_message(
        catalog,
        flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
        progress_label="1/4",
        input_mode=guided_runtime_ux.BUTTON_ONLY,
        prompt_text=getattr(
            catalog,
            "MYFIELDS_METHOD_PROMPT",
            "농지 등록 방법을 선택하세요.\n위치 공유 또는 고유 번호 입력으로 진행할 수 있습니다.",
        ),
        draft_summary=_draft_summary(catalog, binding_count=1 if has_bindings else 0) if has_bindings else None,
    )


def location_prompt_text(catalog) -> str:
    return guided_runtime_ux.format_guided_message(
        catalog,
        flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
        progress_label="2/4",
        input_mode=guided_runtime_ux.LOCATION_ATTACHMENT,
        prompt_text=getattr(
            catalog,
            "MYFIELDS_LOCATION_PROMPT",
            "이제 Telegram의 위치 첨부 기능으로 현재 위치를 보내주세요.\n메시지 입력창의 첨부 메뉴에서 위치를 선택하면 됩니다.",
        ),
        draft_summary=_draft_summary(
            catalog,
            method_label=getattr(catalog, "MYFIELDS_LOOKUP_METHOD_LOCATION_LABEL", "위치 공유"),
        ),
    )


def code_prompt_text(catalog, *, method: str = FIELD_BINDING_SOURCE_FIELD_CODE) -> str:
    return guided_runtime_ux.format_guided_message(
        catalog,
        flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
        progress_label="2/4",
        input_mode=guided_runtime_ux.TEXT_ALLOWED,
        prompt_text=guided_runtime_ux.format_text_input_prompt(
            catalog,
            prompt_text=getattr(
                catalog,
                "MYFIELDS_CODE_PROMPT",
                "농지 고유 번호를 입력하세요.",
            ),
            examples=getattr(catalog, "MYFIELDS_CODE_EXAMPLES", ("FIELD-001",)),
            unsupported_hint=getattr(
                catalog,
                "MYFIELDS_CODE_UNSUPPORTED_INPUT_HINT",
                "설명 문장이나 위치 요청은 이 단계에서 처리하지 않아요.",
            ),
        ),
        draft_summary=_draft_summary(catalog, method_label=_lookup_method_label(method, catalog)),
    )


def code_retry_text(
    catalog,
    *,
    method: str = FIELD_BINDING_SOURCE_FIELD_CODE,
    requested_code: str | None = None,
    from_location_retry: bool = False,
) -> str:
    prompt_key = "MYFIELDS_LOCATION_TO_CODE_REPAIR_PROMPT" if from_location_retry else "MYFIELDS_CODE_REPAIR_PROMPT"
    summary = _draft_summary(catalog, method_label=_lookup_method_label(method, catalog))
    if requested_code:
        requested_code_label = getattr(catalog, "MYFIELDS_DRAFT_REQUESTED_CODE_LABEL", "입력한 고유 번호")
        summary = _join_summary(summary, f"{requested_code_label}={requested_code}")
    return guided_runtime_ux.format_guided_message(
        catalog,
        flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
        progress_label="2/4",
        input_mode=guided_runtime_ux.TEXT_ALLOWED,
        prompt_text=guided_runtime_ux.format_text_input_prompt(
            catalog,
            prompt_text=getattr(catalog, prompt_key, getattr(catalog, "MYFIELDS_CODE_PROMPT", "농지 고유 번호를 입력하세요.")),
            examples=getattr(catalog, "MYFIELDS_CODE_EXAMPLES", ("FIELD-001",)),
            unsupported_hint=getattr(
                catalog,
                "MYFIELDS_CODE_UNSUPPORTED_INPUT_HINT",
                "설명 문장이나 위치 요청은 이 단계에서 처리하지 않아요.",
            ),
        ),
        draft_summary=summary,
    )


def no_registry_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_NO_REGISTRY_MESSAGE",
        "현재 공개된 농지 레지스트리가 없습니다.\n잠시 뒤 다시 시도하거나 지원을 요청하세요.",
    )


def location_no_candidate_text(catalog) -> str:
    return code_retry_text(
        catalog,
        method=FIELD_BINDING_SOURCE_LOCATION,
        from_location_retry=True,
    )


def field_code_not_found_text(catalog, *, requested_code: str | None = None) -> str:
    return code_retry_text(
        catalog,
        method=FIELD_BINDING_SOURCE_FIELD_CODE,
        requested_code=requested_code,
    )


def candidate_text(*, candidates: tuple[dict, ...], catalog) -> str:
    lines = [
        getattr(
            catalog,
            "MYFIELDS_CANDIDATE_PROMPT",
            "관련 농지 후보를 찾았습니다.\n아래에서 맞는 농지를 선택하세요.",
        )
    ]
    for index, candidate in enumerate(candidates, start=1):
        lines.append(f"{index}. {candidate['display_name']} ({candidate['field_code']})")
    return guided_runtime_ux.format_guided_message(
        catalog,
        flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
        progress_label="3/4",
        input_mode=guided_runtime_ux.BUTTON_ONLY,
        prompt_text="\n".join(lines),
        draft_summary=_draft_summary(catalog, candidate_count=len(candidates)),
    )


def confirm_text(*, field_name: str, field_code: str, lookup_method: str, catalog) -> str:
    method_label = _lookup_method_label(lookup_method, catalog)
    prompt_text = (
        getattr(catalog, "MYFIELDS_CONFIRM_MESSAGE", "농지 바인딩 내용을 확인하세요.")
        + "\n"
        + f"- 농지명: {field_name}\n"
        + f"- 고유 번호: {field_code}\n"
        + f"- 확인 방식: {method_label}\n\n"
        + getattr(catalog, "MYFIELDS_CONFIRM_GUIDANCE", "맞으면 [확인]을 누르세요.")
    )
    return guided_runtime_ux.format_guided_message(
        catalog,
        flow_label=getattr(catalog, "GUIDED_FLOW_MYFIELDS", getattr(catalog, "BUTTON_MYFIELDS", "자기 조회")),
        progress_label=getattr(catalog, "GUIDED_REVIEW_STAGE_LABEL", "검토 단계"),
        input_mode=guided_runtime_ux.BUTTON_ONLY,
        prompt_text=prompt_text,
        draft_summary=_draft_summary(catalog, method_label=method_label, field_label=f"{field_name} ({field_code})"),
    )


def binding_confirmed_text(*, field_name: str, field_code: str, catalog) -> str:
    return (
        getattr(catalog, "MYFIELDS_BINDING_CONFIRMED_MESSAGE", "농지가 등록되었습니다.")
        + "\n"
        + f"- 농지명: {field_name}\n"
        + f"- 고유 번호: {field_code}"
    )


def conflict_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_BINDING_CONFLICT_MESSAGE",
        "이 농지는 바로 등록할 수 없습니다.\n운영 검토로 넘기고 다른 방법을 선택해 주세요.",
    )


def _draft_summary(
    catalog,
    *,
    binding_count: int | None = None,
    method_label: str | None = None,
    candidate_count: int | None = None,
    field_label: str | None = None,
) -> str | None:
    segments: list[str] = []
    if binding_count is not None:
        segments.append(
            f"{getattr(catalog, 'MYFIELDS_DRAFT_BINDING_COUNT_LABEL', '등록 농지 수')}={binding_count}"
        )
    if method_label:
        segments.append(
            f"{getattr(catalog, 'MYFIELDS_DRAFT_METHOD_LABEL', '등록 방법')}={method_label}"
        )
    if candidate_count is not None:
        segments.append(
            f"{getattr(catalog, 'MYFIELDS_DRAFT_CANDIDATE_COUNT_LABEL', '후보 수')}={candidate_count}"
        )
    if field_label:
        segments.append(
            f"{getattr(catalog, 'MYFIELDS_DRAFT_FIELD_LABEL', '농지')}={field_label}"
        )
    return ", ".join(segments) if segments else None


def _join_summary(current: str | None, extra: str) -> str:
    if not current:
        return extra
    return f"{current}, {extra}"
