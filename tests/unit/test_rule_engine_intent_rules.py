from PROJECT.canonical_intents import registry
from PROJECT.rule_engine import classify_global_intent_text


def test_classify_global_intent_matches_exact_button_and_city_labels():
    help_decision = classify_global_intent_text("도움말")
    city_decision = classify_global_intent_text("서울")

    assert help_decision is not None
    assert help_decision.canonical_intent == registry.INTENT_HELP
    assert city_decision is not None
    assert city_decision.canonical_intent == registry.INTENT_SELECT_CITY
    assert city_decision.payload["city"] == "서울"


def test_classify_global_intent_supports_profile_view_phrases():
    decision = classify_global_intent_text("내 프로필 보여줘")

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_PROFILE_VIEW


def test_classify_global_intent_supports_profile_edit_variants():
    decision = classify_global_intent_text("생일 잘못 입력했어 수정할래")

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_PROFILE_EDIT_BIRTH_DATE


def test_classify_global_intent_supports_korean_slash_profile_edit():
    decision = classify_global_intent_text("/프로필 수정")

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_PROFILE_EDIT_START


def test_classify_global_intent_supports_command_routing():
    decision = classify_global_intent_text("/menu")

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_MENU


def test_classify_global_intent_supports_fertilizer_start_phrase():
    decision = classify_global_intent_text("비료 입력할게요")

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_FERTILIZER_INPUT_START


def test_classify_global_intent_supports_fertilizer_repair_phrase():
    decision = classify_global_intent_text("비료 양 잘못 입력했어요")

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_FERTILIZER_EDIT_AMOUNT


def test_classify_global_intent_supports_korean_profile_view_command():
    decision = classify_global_intent_text("/프로필")

    assert decision is not None
    assert decision.canonical_intent == registry.INTENT_PROFILE_VIEW
