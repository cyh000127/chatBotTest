from PROJECT.conversations.profile_intake import parser
from PROJECT.i18n.catalogs import ko


def entry_text() -> str:
    return ko.PROFILE_ENTRY_MESSAGE


def build_followup_message(draft: parser.ProfileDraft) -> str:
    if draft.pending_slot == "name":
        return ko.PROFILE_MISSING_NAME_MESSAGE
    if draft.pending_slot == "birth_date":
        return ko.PROFILE_MISSING_BIRTH_MESSAGE
    if draft.pending_slot == "city_for_district":
        examples = draft.city_candidate or "서울특별시, 경기도"
        return ko.PROFILE_CITY_FOLLOWUP_MESSAGE.format(
            district=draft.district_candidate or draft.followup_keyword or "해당 지역",
            examples=examples,
        )
    if draft.pending_slot == "district_for_city":
        examples = ", ".join(parser.district_examples(draft.city_candidate or ""))
        return ko.PROFILE_DISTRICT_FOLLOWUP_MESSAGE.format(
            city=draft.city_candidate or "시/도",
            examples=examples,
        )
    if draft.pending_slot == "district_choice":
        return ko.PROFILE_AMBIGUOUS_DISTRICT_MESSAGE.format(keyword=draft.followup_keyword or "해당 지역")
    return ko.PROFILE_MISSING_RESIDENCE_MESSAGE


def build_confirmation_message(draft: parser.ProfileDraft) -> str:
    return ko.format_profile_confirmation(
        name=draft.name_candidate or "-",
        birth_date=draft.birth_date_candidate or "-",
        city=draft.city_candidate or "-",
        district=draft.district_candidate or "-",
    )


def confirmed_text() -> str:
    return ko.PROFILE_CONFIRMED_MESSAGE


def edit_text() -> str:
    return ko.PROFILE_EDIT_MESSAGE
