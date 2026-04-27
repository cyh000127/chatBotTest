from __future__ import annotations

from PROJECT.storage.fields import FIELD_BINDING_SOURCE_FIELD_CODE, FIELD_BINDING_SOURCE_LOCATION


def _lookup_method_label(method: str, catalog) -> str:
    if method == FIELD_BINDING_SOURCE_LOCATION:
        return getattr(catalog, "MYFIELDS_LOOKUP_METHOD_LOCATION_LABEL", "위치 공유")
    if method == FIELD_BINDING_SOURCE_FIELD_CODE:
        return getattr(catalog, "MYFIELDS_LOOKUP_METHOD_CODE_LABEL", "고유 번호")
    return method


def summary_text(*, participant_name: str, bindings: tuple, catalog) -> str:
    if not bindings:
        return getattr(
            catalog,
            "MYFIELDS_EMPTY_MESSAGE",
            f"{participant_name}님에게 등록된 농지가 없습니다.\n농지 등록을 시작해 주세요.",
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
    return "\n".join(lines)


def method_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_METHOD_PROMPT",
        "농지 등록 방법을 선택하세요.\n위치 공유 또는 고유 번호 입력으로 진행할 수 있습니다.",
    )


def location_prompt_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_LOCATION_PROMPT",
        "이제 Telegram의 위치 첨부 기능으로 현재 위치를 보내주세요.\n메시지 입력창의 첨부 메뉴에서 위치를 선택하면 됩니다.",
    )


def code_prompt_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_CODE_PROMPT",
        "농지 고유 번호를 입력하세요.\n예: FIELD-001",
    )


def no_registry_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_NO_REGISTRY_MESSAGE",
        "현재 공개된 농지 레지스트리가 없습니다.\n잠시 뒤 다시 시도하거나 지원을 요청하세요.",
    )


def location_no_candidate_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_LOCATION_NO_CANDIDATE_MESSAGE",
        "이 위치에서는 등록 가능한 농지 후보를 찾지 못했습니다.\n고유 번호를 입력하거나 다시 시도해 주세요.",
    )


def field_code_not_found_text(catalog) -> str:
    return getattr(
        catalog,
        "MYFIELDS_CODE_NOT_FOUND_MESSAGE",
        "입력한 고유 번호를 찾지 못했습니다.\n다시 입력하거나 위치 공유로 찾기를 선택해 주세요.",
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
    return "\n".join(lines)


def confirm_text(*, field_name: str, field_code: str, lookup_method: str, catalog) -> str:
    method_label = _lookup_method_label(lookup_method, catalog)
    return (
        getattr(catalog, "MYFIELDS_CONFIRM_MESSAGE", "농지 바인딩 내용을 확인하세요.")
        + "\n"
        + f"- 농지명: {field_name}\n"
        + f"- 고유 번호: {field_code}\n"
        + f"- 확인 방식: {method_label}\n\n"
        + getattr(catalog, "MYFIELDS_CONFIRM_GUIDANCE", "맞으면 [확인]을 누르세요.")
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
