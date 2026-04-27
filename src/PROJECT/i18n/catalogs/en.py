from datetime import datetime

BUTTON_TODAY_DATE = "Today"
BUTTON_TODAY_WEATHER = "Weather"
BUTTON_FERTILIZER = "Fertilizer"
BUTTON_YIELD = "Yield"
BUTTON_MYFIELDS = "My fields"
BUTTON_EVIDENCE = "Evidence"
BUTTON_FIELD_REGISTER = "Register field"
BUTTON_FIELD_REFRESH = "Refresh"
BUTTON_FIELD_LOOKUP_LOCATION = "Use location"
BUTTON_FIELD_LOOKUP_CODE = "Enter field code"
BUTTON_INPUT_RESOLVE = "Resolve input"
BUTTON_INPUT_RESOLVE_TARGET_FIELD_CODE = "Field code"
BUTTON_INPUT_RESOLVE_TARGET_FIELD_NAME = "Field name"
BUTTON_INPUT_RESOLVE_METHOD_TYPED_TEXT = "Type text"
BUTTON_INPUT_RESOLVE_CONFIRM_CANDIDATE = "Use this candidate"
BUTTON_INPUT_RESOLVE_RETRY = "Retry"
BUTTON_INPUT_RESOLVE_RETRY_LATER = "Later"
BUTTON_INPUT_RESOLVE_MANUAL_REVIEW = "Manual review"
BUTTON_SUPPORT = "Support"
BUTTON_HELP = "Help"
BUTTON_BACK = "Back"
BUTTON_CANCEL = "Cancel"
BUTTON_RESTART = "Start over"
BUTTON_CONFIRM = "Confirm"
BUTTON_EDIT = "Edit"
BUTTON_EDIT_START = "Start edit"
BUTTON_KEEP_CURRENT = "Keep current"
BUTTON_APPLY_SUGGESTED_VALUE = "Use this"
BUTTON_ENTER_VALUE_DIRECTLY = "Type it"
BUTTON_YES = "Yes"
BUTTON_NO = "No"
BUTTON_EDIT_NAME = "Name"
BUTTON_EDIT_PHONE = "Phone"
BUTTON_EDIT_RESIDENCE = "Residence"
BUTTON_EDIT_CITY = "City / province"
BUTTON_EDIT_DISTRICT = "District / county / city"
BUTTON_EDIT_BIRTH_DATE = "Birth date"
BUTTON_FERTILIZER_EDIT_USED = "Fertilizer use"
BUTTON_FERTILIZER_EDIT_KIND = "Fertilizer type"
BUTTON_FERTILIZER_EDIT_PRODUCT = "Product name"
BUTTON_FERTILIZER_EDIT_AMOUNT = "Amount"
BUTTON_FERTILIZER_EDIT_DATE = "Applied date"
BUTTON_YIELD_EDIT_READY = "Harvest ready"
BUTTON_YIELD_EDIT_FIELD = "Field"
BUTTON_YIELD_EDIT_AMOUNT = "Yield amount"
BUTTON_YIELD_EDIT_DATE = "Harvest date"
BUTTON_PREV_YEARS = "Previous 12 years"
BUTTON_NEXT_YEARS = "Next 12 years"
BUTTON_FERTILIZER_KIND_COMPOUND = "Compound"
BUTTON_FERTILIZER_KIND_UREA = "Urea"
BUTTON_FERTILIZER_KIND_COMPOST = "Compost"
BUTTON_FERTILIZER_KIND_LIQUID = "Liquid"

LANGUAGE_NAME = "English"
LANGUAGE_MENU_MESSAGE = "Choose a language."
LANGUAGE_CHANGED_MESSAGE = "Language set to English."
AUTH_START_PROMPT = "Enter your login ID.\nExample: /start sample-user or sample-user"
AUTH_REQUIRED_MESSAGE = "You need to sign in.\nEnter /start, then type your login ID."
AUTH_INVALID_MESSAGE = "That login ID is not valid.\nTry again."
AUTH_RETRY_LIMIT_MESSAGE = "Sign-in failed twice.\nStart over. Enter /start again."
AUTH_WELCOME_MESSAGE = "Hello, {user_name}."
AUTH_ALREADY_LOGGED_IN_MESSAGE = "Welcome back, {user_name}."
START_REQUIRED_MESSAGE = "Start with /start first."
ONBOARDING_INVITE_REQUIRED_MESSAGE = "An invitation code is required.\nIf you have one, start with /start <invite_code>."
ONBOARDING_INVALID_INVITE_MESSAGE = "We could not verify that invitation code.\nCheck the code and enter /start <invite_code> again."
ONBOARDING_IDENTITY_REQUIRED_MESSAGE = "We could not read your Telegram user information.\nTry again soon."
ONBOARDING_STARTED_MESSAGE = "Invitation code verified.\nChoose a language to continue onboarding."
ONBOARDING_ACCESS_REQUIRED_MESSAGE = "Onboarding and admin approval are required before using the service.\nIf you have an invitation code, start with /start <invite_code>."
ONBOARDING_PENDING_APPROVAL_MESSAGE = "Onboarding is not complete yet or is waiting for admin approval.\nYou can use the service after approval."
ONBOARDING_NAME_PROMPT = "Enter your name."
ONBOARDING_NAME_FALLBACK = "Enter your name again.\nExample: Sample Farmer"
ONBOARDING_PHONE_PROMPT = "Enter your phone number with country code.\nExample: +855 12 345 678, +880 17 1234 5678"
ONBOARDING_PHONE_FALLBACK = "Enter your phone number again.\nOnly +855 or +880 country codes are supported for now."
ONBOARDING_CONFIRM_MESSAGE = (
    "Review your onboarding input.\n"
    "- Name: {name}\n"
    "- Phone: {phone}\n"
    "- Language: {language}\n\n"
    "Press [Confirm] if this is correct, or choose an item to edit."
)
ONBOARDING_CONFIRM_FALLBACK = "Press [Confirm] or choose an item to edit."
ONBOARDING_PENDING_APPROVAL_SUBMITTED_MESSAGE = "Your onboarding request was submitted for approval.\nYou can use the service after admin approval."

CITY_BUTTON_TO_KEY = {
    "Seoul": "서울",
    "Busan": "부산",
    "Jeju": "제주",
}

START_MESSAGE = "Started.\nChoose one below."
MAIN_MENU_MESSAGE = "Main menu.\nChoose one below."
WEATHER_MENU_MESSAGE = "Choose a city for today's weather."
PROFILE_ENTRY_MESSAGE = (
    "Profile input starts here.\n"
    "First, enter your name."
)
CANCEL_MESSAGE = "Current task ended.\nUse 'Start over' or /start to begin again."
BACK_LIMIT_MESSAGE = "There is no previous step.\nChoose again from the main menu."
BACK_TO_MAIN_MESSAGE = "You are back.\nChoose again below."
BACK_TO_WEATHER_MESSAGE = "You are back at city selection.\nChoose a city again."
BACK_GENERIC_MESSAGE = "You are back at the previous step."
WEATHER_ERROR_MESSAGE = "Could not get the weather.\nTry again soon."
UNKNOWN_COMMAND_MESSAGE = "This command is not supported.\nChoose one below or use /help."
MYFIELDS_ENTRY_MESSAGE = "This is the my fields entry.\nFor now, it shows the guide and the way back.\nChoose another item below or start over with /start."
MYFIELDS_EMPTY_MESSAGE = "No field is registered yet.\nStart field registration."
MYFIELDS_SUMMARY_MESSAGE = "These are your registered fields."
MYFIELDS_SUMMARY_GUIDANCE = "You can register another field or refresh the list."
MYFIELDS_METHOD_PROMPT = "Choose how to register the field.\nYou can use a location share or a field code."
MYFIELDS_LOCATION_PROMPT = "Send your current location with Telegram's attachment menu.\nOpen the attachment menu in the message box and choose Location."
MYFIELDS_CODE_PROMPT = "Enter the field code.\nExample: FIELD-001"
MYFIELDS_NO_REGISTRY_MESSAGE = "There is no published field registry yet.\nTry again later or ask for support."
MYFIELDS_LOCATION_NO_CANDIDATE_MESSAGE = "No field candidate was found for this location.\nEnter a field code or try again."
MYFIELDS_CODE_NOT_FOUND_MESSAGE = "That field code was not found.\nEnter it again or switch to location lookup."
MYFIELDS_CANDIDATE_PROMPT = "Field candidates were found.\nChoose the matching field below."
MYFIELDS_CONFIRM_MESSAGE = "Review the field binding."
MYFIELDS_CONFIRM_GUIDANCE = "Press [Confirm] if it is correct."
MYFIELDS_BINDING_CONFIRMED_MESSAGE = "The field was registered."
MYFIELDS_BINDING_CONFLICT_MESSAGE = "This field cannot be registered right now.\nIt was sent for operator review. Choose another method."
MYFIELDS_LOOKUP_METHOD_LOCATION_LABEL = "Location share"
MYFIELDS_LOOKUP_METHOD_CODE_LABEL = "Field code"
EVIDENCE_RUNTIME_UNAVAILABLE_MESSAGE = "The evidence submission runtime is not available right now.\nPlease try again later or ask for support."
EVIDENCE_ENTRY_MESSAGE = "Evidence submission starts here.\nSend your current location first."
EVIDENCE_DOCUMENT_PROMPT = "The location was accepted.\nNow upload the original file as a document."
EVIDENCE_LOCATION_FALLBACK = "This step needs your current location.\nUse Telegram's location attachment."
EVIDENCE_DOCUMENT_FALLBACK = "This step needs the original file as a document upload.\nUse a document attachment instead of a photo."
EVIDENCE_VALIDATING_MESSAGE = "The evidence file was received.\nWait for the next guidance or choose a related action."
EVIDENCE_ACCEPTED_MESSAGE = "The evidence submission is complete.\nBasic validation passed."
EVIDENCE_RETRY_REQUIRED_MESSAGE = "Please submit the evidence again."
EVIDENCE_MANUAL_REVIEW_MESSAGE = "The evidence submission was moved to manual review."
EVIDENCE_REASON_MISSING_EXIF = "The EXIF metadata is missing."
EVIDENCE_REASON_MISSING_GPS = "The GPS metadata is missing."
EVIDENCE_REASON_MISSING_CAPTURE_TIME = "The capture time metadata is missing."
EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR = "The distance between the current location and the photo GPS is too large."
INPUT_RESOLVE_ENTRY_MESSAGE = "This is the input resolve entry.\nFor now, the runtime starts with the main value flow.\nCandidate matching and manual review are in a separate scope."
INPUT_RESOLVE_TARGET_FALLBACK = "Choose the value to resolve with the buttons."
INPUT_RESOLVE_METHOD_FALLBACK = "Only typed text is available in this step.\nSelect [Type text]."
INPUT_RESOLVE_RAW_INPUT_FALLBACK = "Enter the raw value again.\nExample: FIELD-001, Plot 1"
INPUT_RESOLVE_CANDIDATE_NONE_MESSAGE = "No matching candidate was found.\nRetry, come back later, or send it to manual review."
INPUT_RESOLVE_MANUAL_REVIEW_MESSAGE = "The input resolve request was sent to manual review.\nFollow-up guidance will continue in this chat."
INPUT_RESOLVE_INVALID_RESUME_MESSAGE = "The resume token could not be verified.\nStart again with /resolve or ask for support."
INPUT_RESOLVE_STEP_TARGET_LABEL = "Choose value"
INPUT_RESOLVE_STEP_METHOD_LABEL = "Choose method"
INPUT_RESOLVE_STEP_RAW_INPUT_LABEL = "Enter raw text"
INPUT_RESOLVE_STEP_CANDIDATES_LABEL = "Review candidates"
INPUT_RESOLVE_STEP_DECISION_LABEL = "Confirm candidate"
SUPPORT_ESCALATION_MESSAGE = "Your support request was sent.\nNo new chat will open. We will keep replying here.\nUse /help, /menu, or /start to go back."
SUPPORT_HANDOFF_MESSAGE_RECORDED = "The extra note was saved to the support thread.\nReplies will stay in this chat.\nUse /start to start over."
SUPPORT_HANDOFF_CLOSED_MESSAGE = "The support thread is closed.\nYou can ask for help again in this chat."
CANONICAL_WRITE_FAILURE_MESSAGE = "There was a problem saving your input.\nTry again or use /support."

HELP_MESSAGE = (
    "Available commands:\n"
    "- /start : go to the start\n"
    "- /help : show help\n"
    "- /menu : open the main menu\n"
    "- /myfields : open my fields\n"
    "- /fertilizer : start fertilizer input\n"
    "- /yield : start yield input\n"
    "- /evidence : start evidence submission\n"
    "- /resolve : open input resolve\n"
    "- /support : open support help\n"
    "- /language : change language\n"
    "- Back : go to the previous step\n"
    "- Start over : reset the session and start again"
)

FALLBACK_MESSAGES = {
    "default": "The input could not be processed.\nChoose one below.",
    "weather": "The input could not be processed.\nChoose a city below or press Back.",
    "cancelled": "This task has ended.\nChoose one below to continue.",
    "fertilizer_input": "Fertilizer input could not be processed.\nChoose which fertilizer item to continue or change.",
    "fertilizer_confirm": "You are at the fertilizer check step.\nChoose Confirm or Back below.",
    "yield_input": "Yield input could not be processed.\nChoose the step below to continue.",
    "yield_confirm": "You are at the yield check step.\nChoose Confirm or Back below.",
    "myfields_input": "The field registration input could not be processed.\nChoose the matching method for this step.",
    "myfields_confirm": "You are at the field check step.\nChoose Confirm or another method below.",
    "evidence_input": "The evidence submission step could not be processed.\nSend the matching location or document upload again.",
    "evidence_status": "The evidence file is already received.\nWait for the next guidance or choose a related action.",
    "input_resolve_input": "The input resolve step could not be processed.\nSend a matching button choice or a short example again.",
    "input_resolve_confirm": "This is the candidate review step.\nChoose a candidate, retry, come back later, or send it to manual review.",
}
RECOVERY_GUIDANCE_SOFT = "Here is what this step needs."
RECOVERY_GUIDANCE_GUIDED = "Use the guide below to continue."
RECOVERY_GUIDANCE_ESCALATION_READY = "If this keeps failing, use one of the related actions below."
RECOVERY_MULTI_SLOT_CANDIDATE_HINT = "Several candidate values were found in one message. Review this draft before continuing."
RECOVERY_MULTI_SLOT_APPLIED_MESSAGE = "Several candidate values were added to the current draft. Review the content below."
CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE = (
    "This is a support request.\n"
    "It will be saved as a support handoff, and replies will stay here.\n"
    "Choose one below or use /help."
)
CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE = (
    "This needs operator review.\n"
    "It will be saved for follow-up, and any needed guidance can continue here.\n"
    "Choose one below to continue."
)
CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE = (
    "This was checked several times, but it cannot be solved automatically.\n"
    "It will be saved for manual review.\n"
    "Choose one below, or start over with /menu or /start."
)

PROFILE_CONFIRMED_MESSAGE = "Saved.\nIt is in the current session."
PROFILE_EDIT_MESSAGE = "Choose the field to edit."
PROFILE_EDIT_SELECTION_CONFIRMATION_MESSAGE = "You want to choose a profile field again.\nPress [{edit_button}] to open the edit screen."
PROFILE_NOT_FOUND_MESSAGE = "No profile is saved yet.\nFinish profile input first."
PROFILE_NAME_PROMPT = "Enter your name."
PROFILE_RESIDENCE_PROMPT = "Enter your residence."
PROFILE_CITY_PROMPT = "Enter your city or province.\nExample: Seoul, Gyeonggi-do"
PROFILE_DISTRICT_PROMPT = "Enter your district, county, or city.\nExample: Gangnam-gu, Bundang-gu"
PROFILE_BIRTH_YEAR_PROMPT = "Choose your birth year with the buttons."
PROFILE_BIRTH_MONTH_PROMPT = "Choose your birth month with the buttons."
PROFILE_BIRTH_DAY_PROMPT = "Choose your birth day with the buttons."
PROFILE_NAME_FALLBACK = "Enter your name again."
PROFILE_RESIDENCE_FALLBACK = "Enter your residence again."
PROFILE_CITY_FALLBACK = "Enter a valid city or province again.\nExample: Seoul, Gyeonggi-do"
PROFILE_DISTRICT_FALLBACK = "Enter a valid district, county, or city again.\nExample: Gangnam-gu, Bundang-gu"
PROFILE_BIRTH_YEAR_FALLBACK = "Choose a birth year button."
PROFILE_BIRTH_MONTH_FALLBACK = "Choose a birth month button."
PROFILE_BIRTH_DAY_FALLBACK = "Choose a birth day button."
PROFILE_CONFIRM_FALLBACK = "Choose Confirm or Back."
PROFILE_EDIT_SELECT_FALLBACK = "Choose a field to edit with the buttons."
PROFILE_REPAIR_NAME_MESSAGE = "Enter the name again."
PROFILE_REPAIR_RESIDENCE_MESSAGE = "Enter the residence again."
PROFILE_REPAIR_CITY_MESSAGE = "Enter the city or province again."
PROFILE_REPAIR_DISTRICT_MESSAGE = "Enter the district, county, or city again."
PROFILE_REPAIR_BIRTH_MESSAGE = "Enter the birth date again.\nChoose the birth year first."
PROFILE_DIRECT_UPDATE_MESSAGE = "The change was applied.\nReview it and press [Confirm]."
LLM_REPAIR_CANDIDATE_HINT = "\"{candidate_value}\" was detected as the requested change.\nIf that is right, press Start edit."
LLM_REPAIR_UNSUPPORTED_MESSAGE = "The field to edit could not be identified.\nChoose it directly from the related items below."
LLM_REPAIR_LOW_CONFIDENCE_MESSAGE = "The field to edit could not be confirmed.\nChoose it directly from the related items below."
LLM_REPAIR_HUMAN_REVIEW_MESSAGE = (
    "This request is hard to narrow down to one field automatically.\n"
    "It may need manual review, so choose directly from the related items below."
)
LLM_REPAIR_RUNTIME_FAILURE_MESSAGE = (
    "Automatic reading is not stable right now.\n"
    "Continue by choosing directly from the related items below."
)

FERTILIZER_KIND_LABELS = {
    "compound": "Compound",
    "urea": "Urea",
    "compost": "Compost",
    "liquid": "Liquid",
}
FERTILIZER_USED_LABEL_YES = "Yes"
FERTILIZER_USED_LABEL_NO = "No"
FERTILIZER_USED_PROMPT = "Did you use fertilizer for this activity?"
FERTILIZER_KIND_PROMPT = "Choose the fertilizer type."
FERTILIZER_PRODUCT_PROMPT = "Enter the product name.\nExample: Compound fertilizer 21-17-17"
FERTILIZER_AMOUNT_PROMPT = "Enter the amount.\nExample: 20kg, one bag"
FERTILIZER_DATE_PROMPT = "Enter the date used.\nExample: 2026-04-21, today, yesterday"
FERTILIZER_CONFIRM_PROMPT = "Check the fertilizer entry."
FERTILIZER_USED_FALLBACK = "Choose Yes or No."
FERTILIZER_KIND_FALLBACK = "Choose a fertilizer type button."
FERTILIZER_PRODUCT_FALLBACK = "Enter the product name again."
FERTILIZER_AMOUNT_FALLBACK = "Enter the amount again.\nExample: 20kg, one bag"
FERTILIZER_DATE_FALLBACK = "Enter the date again.\nExample: 2026-04-21, today, yesterday"
FERTILIZER_CONFIRM_FALLBACK = "Press [Confirm] or go back to change it."
FERTILIZER_CONFIRMED_MESSAGE = "The fertilizer entry is saved in this session."
FERTILIZER_EDIT_MESSAGE = "Choose which fertilizer field to edit."
FERTILIZER_EDIT_SELECTION_CONFIRMATION_MESSAGE = "You want to choose the fertilizer field again.\nPress [{edit_button}] to open the edit screen."
FERTILIZER_NOT_FOUND_MESSAGE = "No fertilizer entry is saved yet.\nFinish fertilizer input first."
FERTILIZER_REPAIR_USED_MESSAGE = "Enter whether fertilizer was used again."
FERTILIZER_REPAIR_KIND_MESSAGE = "Enter the fertilizer type again."
FERTILIZER_REPAIR_PRODUCT_MESSAGE = "Enter the fertilizer product name again."
FERTILIZER_REPAIR_AMOUNT_MESSAGE = "Enter the fertilizer amount again."
FERTILIZER_REPAIR_DATE_MESSAGE = "Enter the fertilizer date again."
FERTILIZER_DIRECT_UPDATE_MESSAGE = "The change was applied.\nReview it and press [Confirm]."
YIELD_READY_PROMPT = "Is the harvest ready?"
YIELD_FIELD_PROMPT = "Choose or enter the harvested field."
YIELD_AMOUNT_PROMPT = "Enter the harvest amount.\nExample: 320kg"
YIELD_DATE_PROMPT = "Enter the harvest date.\nExample: 2026-04-21, today, yesterday"
YIELD_CONFIRM_PROMPT = "Check the yield entry."
YIELD_READY_FALLBACK = "Choose Yes or No."
YIELD_FIELD_FALLBACK = "Enter the harvested field again."
YIELD_AMOUNT_FALLBACK = "Enter the harvest amount again.\nExample: 320kg"
YIELD_DATE_FALLBACK = "Enter the harvest date again.\nExample: 2026-04-21, today, yesterday"
YIELD_CONFIRM_FALLBACK = "Press [Confirm] or go back to revise."
YIELD_EDIT_MESSAGE = "Choose which yield field to edit."
YIELD_EDIT_SELECT_FALLBACK = "Choose a field to edit, or press [Start edit], Back, or Start over."
YIELD_CONFIRMED_MESSAGE = "The yield entry is confirmed and saved in this session."
INPUT_RESOLVE_TARGET_PROMPT = "Choose the value to resolve."
INPUT_RESOLVE_METHOD_PROMPT = "Choose how to enter it.\nUse typed text, OCR image, or retry."
INPUT_RESOLVE_RAW_INPUT_PROMPT = "Enter or upload the raw text to resolve."
INPUT_RESOLVE_CANDIDATES_PROMPT = "Review the choices and pick 1-3, or retry."
INPUT_RESOLVE_DECISION_PROMPT = "Choose resolved, retry, or manual review."


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "Check this.\n"
        f"- Name: {name}\n"
        f"- Residence: {residence}\n"
        f"- City/Province: {city}\n"
        f"- District/County/City: {district}\n"
        f"- Birth date: {birth_date}\n"
        "\nIf it is right, press [Confirm]. If not, press [Edit]."
    )


def format_repair_confirmation(*, field_label: str, edit_button: str) -> str:
    return (
        f"Choose the {field_label} field again.\n"
        f"Press [{edit_button}] to enter it again."
    )


def format_change_preview(*, field_label: str, before_value: str, after_value: str) -> str:
    return (
        f"Review the change for {field_label}.\n"
        f"- Before: {before_value}\n"
        f"- New: {after_value}"
    )


def format_profile_summary(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "Saved profile.\n"
        f"- Name: {name}\n"
        f"- Residence: {residence}\n"
        f"- City/Province: {city}\n"
        f"- District/County/City: {district}\n"
        f"- Birth date: {birth_date}"
    )


def format_fertilizer_confirmation(
    *,
    used: bool | None,
    kind_label: str,
    product_name: str,
    amount_text: str,
    applied_date: str,
) -> str:
    if used is False:
        return (
            "Check the fertilizer entry.\n"
            "- Fertilizer used: No\n\n"
            "Press [Confirm] if it is right."
        )
    return (
        "Check the fertilizer entry.\n"
        f"- Fertilizer used: {'Yes' if used else '-'}\n"
        f"- Type: {kind_label}\n"
        f"- Product: {product_name}\n"
        f"- Amount: {amount_text}\n"
        f"- Applied date: {applied_date}\n\n"
        "Press [Confirm] if it is right."
    )


def format_fertilizer_summary(
    *,
    used: bool | None,
    kind_label: str,
    product_name: str,
    amount_text: str,
    applied_date: str,
) -> str:
    if used is False:
        return (
            "Saved fertilizer entry.\n"
            "- Fertilizer used: No"
        )
    return (
        "Saved fertilizer entry.\n"
        f"- Fertilizer used: {'Yes' if used else '-'}\n"
        f"- Type: {kind_label}\n"
        f"- Product: {product_name}\n"
        f"- Amount: {amount_text}\n"
        f"- Applied date: {applied_date}"
    )


def format_yield_confirmation(
    *,
    ready: bool | None,
    field_name: str,
    amount_text: str,
    harvest_date: str,
) -> str:
    return (
        "Check the yield entry.\n"
        f"- Harvest ready: {'Ready' if ready else 'Not ready' if ready is False else '-'}\n"
        f"- Field: {field_name}\n"
        f"- Amount: {amount_text}\n"
        f"- Harvest date: {harvest_date}\n\n"
        "If it is right, press [Confirm]."
    )


def format_support_admin_reply(*, admin_message: str) -> str:
    return (
        "Reply from support.\n"
        f"{admin_message}\n\n"
        "If you need to add more, continue here."
    )


def format_input_resolve_candidate_list(*, target_label: str, raw_input: str, candidates: tuple[str, ...]) -> str:
    candidate_lines = "\n".join(f"{index}. {candidate}" for index, candidate in enumerate(candidates, start=1))
    return (
        f"Candidates found for {target_label}.\n"
        f"- Raw input: {raw_input}\n\n"
        f"{candidate_lines}\n\n"
        "Choose the matching item or retry."
    )


def format_input_resolve_selected_candidate(*, target_label: str, candidate_label: str) -> str:
    return (
        f"Review the {target_label} candidate.\n"
        f"- Selected candidate: {candidate_label}\n\n"
        "Choose use this candidate, retry, later, or manual review."
    )


def format_input_resolve_resolved(*, target_label: str, candidate_label: str) -> str:
    return (
        "The resolved value was saved.\n"
        f"- Target: {target_label}\n"
        f"- Value: {candidate_label}"
    )


def format_input_resolve_reminder(*, command_text: str) -> str:
    return (
        "It is time to continue the saved input resolve flow.\n"
        f"Enter {command_text} to reopen it."
    )


def format_input_resolve_reminder_created(*, command_text: str) -> str:
    return (
        "Saved so you can continue later.\n"
        f"When you want to continue, enter {command_text}."
    )


def format_input_resolve_resumed(*, step_label: str, prompt_text: str) -> str:
    return f"Reopened the saved input resolve flow.\nCurrent step: {step_label}\n\n{prompt_text}"


def format_evidence_entry(*, field_label: str) -> str:
    return (
        f"{EVIDENCE_ENTRY_MESSAGE}\n"
        f"- Current field link: {field_label}"
    )


def format_evidence_uploaded(*, file_name: str) -> str:
    return (
        "The evidence file was received.\n"
        f"- File name: {file_name}\n\n"
        "The next step will continue in this same flow when basic validation is ready."
    )


def format_evidence_accepted(*, file_name: str) -> str:
    return (
        f"{EVIDENCE_ACCEPTED_MESSAGE}\n"
        f"- File name: {file_name}"
    )


def format_evidence_retry_required(*, file_name: str, reason_lines: tuple[str, ...]) -> str:
    reason_text = "\n".join(f"- {line}" for line in reason_lines)
    return (
        f"{EVIDENCE_RETRY_REQUIRED_MESSAGE}\n"
        f"- File name: {file_name}\n"
        f"{reason_text}\n\n"
        "Upload the document again in this same step."
    )


def format_evidence_manual_review(*, file_name: str, reason_lines: tuple[str, ...]) -> str:
    reason_text = "\n".join(f"- {line}" for line in reason_lines)
    reason_block = f"{reason_text}\n\n" if reason_text else ""
    return (
        f"{EVIDENCE_MANUAL_REVIEW_MESSAGE}\n"
        f"- File name: {file_name}\n"
        f"{reason_block}"
        "Follow-up guidance will continue in this chat."
    )


WEATHER_CODE_LABELS = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Cloudy",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail",
    99: "Thunderstorm with heavy hail",
}


def weather_code_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"Unknown condition ({code})")


def format_today_date(current: datetime) -> str:
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday = weekdays[current.weekday()]
    return (
        "Today's date.\n"
        f"- Date: {current.strftime('%Y-%m-%d')} ({weekday})\n"
        f"- Time: {current.strftime('%H:%M:%S')} KST"
    )


def format_weather(
    *,
    city: str,
    observed_at: datetime,
    weather_label: str,
    temperature: float,
    apparent_temperature: float,
    wind_speed: float,
) -> str:
    return (
        f"Weather in {city}.\n"
        f"- Time: {observed_at.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"- Condition: {weather_label}\n"
        f"- Temperature: {temperature:.1f}°C\n"
        f"- Feels like: {apparent_temperature:.1f}°C\n"
        f"- Wind speed: {wind_speed:.1f} km/h"
    )
