from PROJECT.rule_engine.contracts import IntentDecision, NormalizedInput
from PROJECT.rule_engine.normalizer import normalize_user_input


def classify_step_local_intent(normalized_input: NormalizedInput, *, current_step: str | None) -> IntentDecision | None:
    _ = normalized_input
    _ = current_step
    return None


def classify_step_local_intent_text(text: str, *, locale: str = "ko", current_step: str | None = None) -> IntentDecision | None:
    return classify_step_local_intent(
        normalize_user_input(text, locale=locale),
        current_step=current_step,
    )
