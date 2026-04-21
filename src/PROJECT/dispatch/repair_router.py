from dataclasses import dataclass

from PROJECT.canonical_intents import registry
from PROJECT.conversations.profile_intake.states import (
    STATE_PROFILE_BIRTH_YEAR,
    STATE_PROFILE_CITY,
    STATE_PROFILE_DISTRICT,
    STATE_PROFILE_EDIT_SELECT,
    STATE_PROFILE_NAME,
    STATE_PROFILE_RESIDENCE,
)
from PROJECT.rule_engine import classify_global_intent_text

REPAIR_NAME = "repair_name"
REPAIR_RESIDENCE = "repair_residence"
REPAIR_CITY = "repair_city"
REPAIR_DISTRICT = "repair_district"
REPAIR_BIRTH_DATE = "repair_birth_date"
REPAIR_PROFILE = "repair_profile"


@dataclass(frozen=True)
class RepairDecision:
    target: str
    target_state: str


def detect_repair_intent(text: str) -> RepairDecision | None:
    decision = classify_global_intent_text(text, locale="ko")
    if decision is None:
        return None

    mapping = {
        registry.INTENT_PROFILE_EDIT_NAME: RepairDecision(REPAIR_NAME, STATE_PROFILE_NAME),
        registry.INTENT_PROFILE_EDIT_RESIDENCE: RepairDecision(REPAIR_RESIDENCE, STATE_PROFILE_RESIDENCE),
        registry.INTENT_PROFILE_EDIT_CITY: RepairDecision(REPAIR_CITY, STATE_PROFILE_CITY),
        registry.INTENT_PROFILE_EDIT_DISTRICT: RepairDecision(REPAIR_DISTRICT, STATE_PROFILE_DISTRICT),
        registry.INTENT_PROFILE_EDIT_BIRTH_DATE: RepairDecision(REPAIR_BIRTH_DATE, STATE_PROFILE_BIRTH_YEAR),
        registry.INTENT_PROFILE_EDIT_START: RepairDecision(REPAIR_PROFILE, STATE_PROFILE_EDIT_SELECT),
    }
    repair = mapping.get(decision.canonical_intent)
    if repair is not None:
        return repair
    return None


def detect_profile_view_intent(text: str) -> bool:
    decision = classify_global_intent_text(text, locale="ko")
    return decision is not None and decision.canonical_intent == registry.INTENT_PROFILE_VIEW
