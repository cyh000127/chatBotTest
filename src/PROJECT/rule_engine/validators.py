from PROJECT.rule_engine.aliases import DistrictRule, detect_city_alias, detect_district_rule
from PROJECT.rule_engine.contracts import ResolutionCandidate, RuleSource, ValidationClassification, ValidationResult
from PROJECT.rule_engine.normalizer import normalize_body_text

PROFILE_PENDING_NAME = "name"
PROFILE_PENDING_BIRTH_DATE = "birth_date"
PROFILE_PENDING_RESIDENCE = "residence"
PROFILE_PENDING_CITY_FOR_DISTRICT = "city_for_district"
PROFILE_PENDING_DISTRICT_FOR_CITY = "district_for_city"
PROFILE_PENDING_DISTRICT_CHOICE = "district_choice"


def validate_profile_candidates(
    *,
    name_candidate: str | None,
    birth_date_candidate: str | None,
    city_candidate: str | None,
    district_rule: DistrictRule | None,
) -> ValidationResult:
    district_candidate = None
    pending_slot = None
    followup_options: tuple[str, ...] = ()
    followup_keyword = None

    if district_rule is not None:
        followup_keyword = district_rule.trigger
        if district_rule.ambiguous_options:
            city_candidate = city_candidate or district_rule.city
            pending_slot = PROFILE_PENDING_DISTRICT_CHOICE
            followup_options = district_rule.ambiguous_options
        elif city_candidate is None and district_rule.ask_city_when_missing:
            district_candidate = district_rule.district
            pending_slot = PROFILE_PENDING_CITY_FOR_DISTRICT
        else:
            city_candidate = city_candidate or district_rule.city
            district_candidate = district_rule.district
    elif city_candidate:
        pending_slot = PROFILE_PENDING_DISTRICT_FOR_CITY
    else:
        pending_slot = PROFILE_PENDING_RESIDENCE

    if name_candidate is None:
        pending_slot = PROFILE_PENDING_NAME
    elif birth_date_candidate is None:
        pending_slot = PROFILE_PENDING_BIRTH_DATE

    classification = (
        ValidationClassification.RESOLVED
        if pending_slot is None
        else ValidationClassification.REASK
    )

    return ValidationResult(
        classification=classification,
        source=RuleSource.VALIDATOR,
        normalized_candidate=ResolutionCandidate(
            field_name="profile",
            raw_value="profile_candidates",
            candidate_type="profile_input",
            source=RuleSource.SLOT_EXTRACTOR,
            normalized_value={
                "name_candidate": name_candidate,
                "birth_date_candidate": birth_date_candidate,
                "city_candidate": city_candidate,
                "district_candidate": district_candidate,
            },
        ),
        reason=None if pending_slot is None else f"missing_or_ambiguous_{pending_slot}",
        metadata={
            "pending_slot": pending_slot,
            "followup_options": followup_options,
            "followup_keyword": followup_keyword,
            "city_candidate": city_candidate,
            "district_candidate": district_candidate,
        },
    )


def validate_profile_followup(
    *,
    pending_slot: str | None,
    raw_text: str,
    city_candidate: str | None = None,
    district_candidate: str | None = None,
    followup_options: tuple[str, ...] = (),
) -> ValidationResult:
    normalized = normalize_body_text(raw_text, locale="ko")

    if pending_slot == PROFILE_PENDING_CITY_FOR_DISTRICT:
        resolved_city = detect_city_alias(normalized)
        if resolved_city is None:
            return ValidationResult(
                classification=ValidationClassification.REASK,
                source=RuleSource.VALIDATOR,
                reason="invalid_city_followup",
            )
        return ValidationResult(
            classification=ValidationClassification.RESOLVED,
            source=RuleSource.VALIDATOR,
            metadata={
                "city_candidate": resolved_city,
                "district_candidate": district_candidate,
            },
        )

    if pending_slot == PROFILE_PENDING_DISTRICT_FOR_CITY:
        rule = detect_district_rule(normalized)
        if rule is None or rule.district is None:
            return ValidationResult(
                classification=ValidationClassification.REASK,
                source=RuleSource.VALIDATOR,
                reason="invalid_district_followup",
            )
        return ValidationResult(
            classification=ValidationClassification.RESOLVED,
            source=RuleSource.VALIDATOR,
            metadata={
                "city_candidate": city_candidate,
                "district_candidate": rule.district,
            },
        )

    if pending_slot == PROFILE_PENDING_DISTRICT_CHOICE:
        options = {option.replace("고양시 ", ""): option for option in followup_options}
        chosen = options.get(normalized)
        if chosen is None and normalized in followup_options:
            chosen = normalized
        if chosen is None:
            return ValidationResult(
                classification=ValidationClassification.REASK,
                source=RuleSource.VALIDATOR,
                reason="invalid_district_choice_followup",
            )
        return ValidationResult(
            classification=ValidationClassification.RESOLVED,
            source=RuleSource.VALIDATOR,
            metadata={
                "city_candidate": city_candidate,
                "district_candidate": chosen,
            },
        )

    return ValidationResult(
        classification=ValidationClassification.UNSUPPORTED,
        source=RuleSource.VALIDATOR,
        reason="unsupported_followup_slot",
    )
