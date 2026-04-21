import re

from PROJECT.rule_engine.contracts import NormalizedInput

WHITESPACE_PATTERN = re.compile(r"\s+")
COMMAND_TOKEN_PATTERN = re.compile(r"^/([^\s@]+)(?:@[^\s]+)?$")
BODY_SEPARATOR_PATTERN = re.compile(r"[,/]+")
DASH_PATTERN = re.compile(r"[-]+")


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", text.strip())


def extract_command_token(text: str) -> str | None:
    stripped = normalize_whitespace(text)
    if not stripped.startswith("/"):
        return None
    first_token = stripped.split(" ", 1)[0]
    match = COMMAND_TOKEN_PATTERN.fullmatch(first_token)
    if match is None:
        return None
    return f"/{match.group(1).casefold()}"


def normalize_body_text(text: str, *, locale: str = "ko") -> str:
    normalized = normalize_whitespace(text)
    normalized = normalized.replace("’", "'").replace("`", "'")
    normalized = BODY_SEPARATOR_PATTERN.sub(" ", normalized)
    normalized = DASH_PATTERN.sub(" ", normalized)
    normalized = normalize_whitespace(normalized)
    return normalized.casefold()


def normalize_user_input(text: str, *, locale: str = "ko") -> NormalizedInput:
    stripped = normalize_whitespace(text)
    command = extract_command_token(stripped)

    if command is not None:
        parts = stripped.split(" ", 1)
        body = parts[1] if len(parts) > 1 else ""
        normalized_body = normalize_body_text(body, locale=locale)
        normalized_text = f"{command} {normalized_body}".strip()
    else:
        normalized_text = normalize_body_text(stripped, locale=locale)

    tokens = tuple(token for token in normalized_text.split(" ") if token)
    return NormalizedInput(
        raw_text=text,
        normalized_text=normalized_text,
        locale=locale,
        tokens=tokens,
        command=command,
    )
