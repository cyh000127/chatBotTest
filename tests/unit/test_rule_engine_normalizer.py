from PROJECT.rule_engine import extract_command_token, normalize_body_text, normalize_user_input


def test_extract_command_token_normalizes_case_and_bot_suffix():
    assert extract_command_token("/PROFILE@TestBot edit") == "/profile"


def test_normalize_body_text_collapses_common_separators():
    assert normalize_body_text("서울/강남-gu, 20KG") == "서울 강남 gu 20kg"


def test_normalize_user_input_preserves_command_and_normalizes_body():
    normalized = normalize_user_input("  /Fertilizer@TestBot   입력-할게요  ", locale="ko")

    assert normalized.command == "/fertilizer"
    assert normalized.normalized_text == "/fertilizer 입력 할게요"
    assert normalized.tokens == ("/fertilizer", "입력", "할게요")
