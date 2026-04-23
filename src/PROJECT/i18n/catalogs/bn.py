from datetime import datetime

BUTTON_TODAY_DATE = "আজকের তারিখ"
BUTTON_TODAY_WEATHER = "আজকের আবহাওয়া"
BUTTON_PROFILE = "প্রোফাইল"
BUTTON_FERTILIZER = "সার দেওয়া"
BUTTON_YIELD = "ফসলের পরিমাণ"
BUTTON_MYFIELDS = "আমার ক্ষেত"
BUTTON_INPUT_RESOLVE = "ইনপুট বুঝে নিন"
BUTTON_SUPPORT = "সহায়তা"
BUTTON_HELP = "সাহায্য"
BUTTON_BACK = "ফিরে যান"
BUTTON_CANCEL = "বাতিল"
BUTTON_RESTART = "আবার শুরু"
BUTTON_CONFIRM = "ঠিক আছে"
BUTTON_EDIT = "বদলান"
BUTTON_EDIT_START = "বদলানো শুরু"
BUTTON_KEEP_CURRENT = "এভাবেই রাখুন"
BUTTON_APPLY_SUGGESTED_VALUE = "এই মান নিন"
BUTTON_ENTER_VALUE_DIRECTLY = "নিজে লিখুন"
BUTTON_YES = "হ্যাঁ"
BUTTON_NO = "না"
BUTTON_EDIT_NAME = "নাম"
BUTTON_EDIT_RESIDENCE = "ঠিকানা"
BUTTON_EDIT_CITY = "জেলা/বিভাগ"
BUTTON_EDIT_DISTRICT = "উপজেলা/থানা"
BUTTON_EDIT_BIRTH_DATE = "জন্মতারিখ"
BUTTON_FERTILIZER_EDIT_USED = "সার ব্যবহার"
BUTTON_FERTILIZER_EDIT_KIND = "সারের ধরন"
BUTTON_FERTILIZER_EDIT_PRODUCT = "পণ্যের নাম"
BUTTON_FERTILIZER_EDIT_AMOUNT = "পরিমাণ"
BUTTON_FERTILIZER_EDIT_DATE = "ব্যবহারের তারিখ"
BUTTON_YIELD_EDIT_READY = "ফসল প্রস্তুত"
BUTTON_YIELD_EDIT_FIELD = "ক্ষেত"
BUTTON_YIELD_EDIT_AMOUNT = "ফসলের পরিমাণ"
BUTTON_YIELD_EDIT_DATE = "ফসল তোলার তারিখ"
BUTTON_PREV_YEARS = "আগের 12 বছর"
BUTTON_NEXT_YEARS = "পরের 12 বছর"
BUTTON_FERTILIZER_KIND_COMPOUND = "মিশ্র সার"
BUTTON_FERTILIZER_KIND_UREA = "ইউরিয়া"
BUTTON_FERTILIZER_KIND_COMPOST = "কম্পোস্ট"
BUTTON_FERTILIZER_KIND_LIQUID = "তরল সার"

LANGUAGE_NAME = "বাংলা"
LANGUAGE_MENU_MESSAGE = "ভাষা বেছে নিন।"
LANGUAGE_CHANGED_MESSAGE = "ভাষা বাংলা করা হয়েছে।"
AUTH_START_PROMPT = "আপনার আইডি লিখুন।\nউদাহরণ: /start okccc5 বা okccc5"
AUTH_REQUIRED_MESSAGE = "আগে লগইন করতে হবে।\n/start চাপুন, তারপর আপনার আইডি লিখুন।"
AUTH_INVALID_MESSAGE = "এই আইডি ঠিক নয়। আবার লিখুন।"
AUTH_RETRY_LIMIT_MESSAGE = "দুইবার ভুল হয়েছে।\nআবার শুরু করুন। /start দিন।"
AUTH_WELCOME_MESSAGE = "স্বাগতম {user_name}।"
AUTH_ALREADY_LOGGED_IN_MESSAGE = "ফিরে এলেন {user_name}।"

CITY_BUTTON_TO_KEY = {
    "সিওল": "서울",
    "বুসান": "부산",
    "জেজু": "제주",
}

START_MESSAGE = "শুরু হয়েছে।\nনিচ থেকে একটি বেছে নিন।"
MAIN_MENU_MESSAGE = "মূল মেনু।\nনিচ থেকে একটি বেছে নিন।"
WEATHER_MENU_MESSAGE = "আজকের আবহাওয়া দেখতে একটি শহর বেছে নিন।"
PROFILE_ENTRY_MESSAGE = (
    "প্রোফাইল শুরু করছি।\n"
    "আগে নাম লিখুন।"
)
CANCEL_MESSAGE = "চলমান কাজ বন্ধ করা হয়েছে।\nআবার শুরু করতে 'আবার শুরু' বা /start দিন।"
BACK_LIMIT_MESSAGE = "আগের ধাপ নেই।\nমূল মেনু থেকে আবার বেছে নিন।"
BACK_TO_MAIN_MESSAGE = "ফিরে এসেছেন।\nনিচ থেকে আবার বেছে নিন।"
BACK_TO_WEATHER_MESSAGE = "শহর বাছাইয়ে ফিরে এসেছেন।\nআবার শহর বেছে নিন।"
BACK_GENERIC_MESSAGE = "আগের ধাপে ফিরে এসেছেন।"
WEATHER_ERROR_MESSAGE = "আবহাওয়া পাওয়া যায়নি।\nকিছুক্ষণ পরে আবার চেষ্টা করুন।"
UNKNOWN_COMMAND_MESSAGE = "এই কমান্ড বুঝিনি।\nনিচ থেকে একটি বেছে নিন বা /help দিন।"
MYFIELDS_ENTRY_MESSAGE = "এটি আমার ক্ষেত অংশ।\nএখন শুধু দেখার পথ আর ফিরে যাওয়ার পথ আছে।\nনিচ থেকে অন্য কিছু বেছে নিন বা /start দিয়ে আবার শুরু করুন।"
INPUT_RESOLVE_ENTRY_MESSAGE = "এটি ইনপুট বুঝে নেওয়ার অংশ।\nএখন কোন মান নিতে হবে, আগে সেটা গুছিয়ে নিচ্ছি।\nপরের ধাপে মিল খোঁজা আর হাতে দেখা হবে।"
SUPPORT_ESCALATION_MESSAGE = "সহায়তার অনুরোধ পাঠানো হয়েছে।\nনতুন চ্যাট খুলছি না। এই চ্যাটেই উত্তর আসবে।\nফিরে যেতে /help, /menu, বা /start দিন।"
SUPPORT_HANDOFF_MESSAGE_RECORDED = "অতিরিক্ত কথা সহায়তার নোটে রাখা হয়েছে।\nএই চ্যাটেই উত্তর আসবে।\nআবার শুরু করতে /start দিন।"
SUPPORT_HANDOFF_CLOSED_MESSAGE = "সহায়তা শেষ হয়েছে।\nচাইলে এই চ্যাটে আবার সাহায্য চাইতে পারেন।"

HELP_MESSAGE = (
    "ব্যবহার করতে পারেন:\n"
    "- /start : শুরুতে যান\n"
    "- /help : সাহায্য দেখুন\n"
    "- /menu : মূল মেনু খুলুন\n"
    "- /profile : প্রোফাইল শুরু করুন\n"
    "- /myfields : আমার ক্ষেত খুলুন\n"
    "- /fertilizer : সার দেওয়া শুরু করুন\n"
    "- /yield : ফসলের পরিমাণ শুরু করুন\n"
    "- /resolve : ইনপুট বুঝে নিন\n"
    "- /support : সহায়তা খুলুন\n"
    "- /language : ভাষা বদলান\n"
    "- ফিরে যান : আগের ধাপে যান\n"
    "- আবার শুরু : শুরু থেকে আবার করুন"
)

FALLBACK_MESSAGES = {
    "default": "এটা বুঝতে পারিনি।\nনিচ থেকে একটি বেছে নিন।",
    "weather": "এটা বুঝতে পারিনি।\nনিচে শহর বেছে নিন বা ফিরে যান চাপুন।",
    "cancelled": "এই কাজ শেষ হয়েছে।\nচালিয়ে যেতে নিচ থেকে একটি বেছে নিন।",
    "profile_input": "প্রোফাইল ইনপুট এখনই বুঝতে পারিনি।\nচালিয়ে যেতে নিচের অংশ থেকে একটি বেছে নিন।",
    "profile_followup": "আরও একটু দেখে নিতে হবে।\nনিচ থেকে একটি বেছে নিন।",
    "profile_confirm": "প্রোফাইল দেখার ধাপে আছেন।\nঠিক আছে বা ফিরে যান বেছে নিন।",
    "fertilizer_input": "সারের ইনপুট এখনই বুঝতে পারিনি।\nচালিয়ে যেতে নিচের অংশ থেকে একটি বেছে নিন।",
    "fertilizer_confirm": "সার দেখার ধাপে আছেন।\nঠিক আছে বা ফিরে যান বেছে নিন।",
    "yield_input": "ফসলের ইনপুট এখনই বুঝতে পারিনি।\nচালিয়ে যেতে নিচের অংশ থেকে একটি বেছে নিন।",
    "yield_confirm": "ফসল দেখার ধাপে আছেন।\nঠিক আছে বা ফিরে যান বেছে নিন।",
}
RECOVERY_GUIDANCE_SOFT = "এই ধাপে কী লাগবে, আবার বলছি।"
RECOVERY_GUIDANCE_GUIDED = "চালিয়ে যেতে নিচের নির্দেশনা দেখুন।"
RECOVERY_GUIDANCE_ESCALATION_READY = "বারবার সমস্যা হলে নিচের বিকল্প নিন।"
RECOVERY_MULTI_SLOT_CANDIDATE_HINT = "একটি বার্তায় কয়েকটি মান পেয়েছি।\nচালিয়ে যাওয়ার আগে খসড়া দেখুন।"
RECOVERY_MULTI_SLOT_APPLIED_MESSAGE = "কয়েকটি মান খসড়ায় বসানো হয়েছে।\nনিচের লেখা দেখে নিন।"
CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE = (
    "এটা সহায়তার অনুরোধ মনে হচ্ছে।\n"
    "আমি এটাকে সহায়তার নোট হিসেবে রাখছি, আর উত্তর এই চ্যাটেই আসবে।\n"
    "চালিয়ে যেতে নিচ থেকে একটি বেছে নিন বা /help দিন।"
)
CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE = (
    "এটা দেখে মনে হচ্ছে পরে একজন মানুষের দেখা দরকার।\n"
    "আমি এটাকে পরের দেখার জন্য রেখে দিচ্ছি, আর দরকারি কথা এই চ্যাটেই থাকবে।\n"
    "চালিয়ে যেতে নিচ থেকে একটি বেছে নিন।"
)
CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE = (
    "কয়েকবার দেখে ফেলেছি, কিন্তু এখনো স্বয়ংক্রিয়ভাবে মেলাতে পারছি না।\n"
    "এটা হাতে দেখে ঠিক করতে হবে।\n"
    "নিচ থেকে একটি বেছে নিন বা /menu, /start দিন।"
)

PROFILE_CONFIRMED_MESSAGE = "তথ্য ঠিক আছে।\nএ সেশনে রেখে দিলাম।"
PROFILE_EDIT_MESSAGE = "কোন অংশ বদলাবেন, বেছে নিন।"
PROFILE_EDIT_SELECTION_CONFIRMATION_MESSAGE = "প্রোফাইলের অংশ আবার বেছে নিতে চান?\n[{edit_button}] চাপলে বদলানোর পর্দা খুলবে।"
PROFILE_NOT_FOUND_MESSAGE = "এখনো কোনো প্রোফাইল নেই।\nআগে প্রোফাইল শেষ করুন।"
PROFILE_NAME_PROMPT = "নাম লিখুন।"
PROFILE_RESIDENCE_PROMPT = "ঠিকানা লিখুন।"
PROFILE_CITY_PROMPT = "জেলা/বিভাগ লিখুন।\nউদাহরণ: ঢাকা বিভাগ"
PROFILE_DISTRICT_PROMPT = "উপজেলা/থানা লিখুন।\nউদাহরণ: গুলশান, সাভার"
PROFILE_BIRTH_YEAR_PROMPT = "বছরটি বোতাম থেকে বেছে নিন।"
PROFILE_BIRTH_MONTH_PROMPT = "মাসটি বোতাম থেকে বেছে নিন।"
PROFILE_BIRTH_DAY_PROMPT = "দিনটি বোতাম থেকে বেছে নিন।"
PROFILE_NAME_FALLBACK = "নামটি আবার লিখুন।"
PROFILE_RESIDENCE_FALLBACK = "ঠিকানাটি আবার লিখুন।"
PROFILE_CITY_FALLBACK = "সঠিক জেলা/বিভাগ আবার লিখুন।\nউদাহরণ: ঢাকা বিভাগ"
PROFILE_DISTRICT_FALLBACK = "সঠিক উপজেলা/থানা আবার লিখুন।\nউদাহরণ: গুলশান, সাভার"
PROFILE_BIRTH_YEAR_FALLBACK = "জন্মসালটি বোতাম থেকে বেছে নিন।"
PROFILE_BIRTH_MONTH_FALLBACK = "জন্মমাসটি বোতাম থেকে বেছে নিন।"
PROFILE_BIRTH_DAY_FALLBACK = "জন্মদিনটি বোতাম থেকে বেছে নিন।"
PROFILE_CONFIRM_FALLBACK = "[ঠিক আছে] বা [বদলান] বেছে নিন।"
PROFILE_EDIT_SELECT_FALLBACK = "বদলাতে চান এমন অংশের বোতাম বেছে নিন।"
PROFILE_REPAIR_NAME_MESSAGE = "নামটি আবার লিখুন।"
PROFILE_REPAIR_RESIDENCE_MESSAGE = "ঠিকানাটি আবার লিখুন।"
PROFILE_REPAIR_CITY_MESSAGE = "জেলা/বিভাগটি আবার লিখুন।"
PROFILE_REPAIR_DISTRICT_MESSAGE = "উপজেলা/থানাটি আবার লিখুন।"
PROFILE_REPAIR_BIRTH_MESSAGE = "জন্মতারিখটি আবার লিখুন।\nআগে জন্মসাল বেছে নিন।"
PROFILE_DIRECT_UPDATE_MESSAGE = "পরিবর্তন নিলাম।\nদেখে [ঠিক আছে] চাপুন।"
LLM_REPAIR_CANDIDATE_HINT = "\"{candidate_value}\" বুঝেছি বলে মনে হচ্ছে।\nঠিক হলে বদলানো শুরু চাপুন।"
LLM_REPAIR_UNSUPPORTED_MESSAGE = "কোন অংশ বদলাতে চান, বুঝতে পারিনি।\nনিচের অংশ থেকে সরাসরি বেছে নিন।"
LLM_REPAIR_LOW_CONFIDENCE_MESSAGE = "কোন অংশ বদলাতে চান, আমি নিশ্চিত নই।\nনিচের অংশ থেকে সরাসরি বেছে নিন।"
LLM_REPAIR_HUMAN_REVIEW_MESSAGE = (
    "এই অনুরোধটি এক অংশে নামানো কঠিন।\n"
    "হাতে দেখে ঠিক করতে হতে পারে, তাই নিচের অংশ থেকে সরাসরি বেছে নিন।"
)
LLM_REPAIR_RUNTIME_FAILURE_MESSAGE = (
    "স্বয়ংক্রিয় বোঝা এখন ঠিক চলছে না।\n"
    "নিচের অংশ থেকে সরাসরি বেছে নিয়ে এগোন।"
)

FERTILIZER_KIND_LABELS = {
    "compound": "মিশ্র সার",
    "urea": "ইউরিয়া",
    "compost": "কম্পোস্ট",
    "liquid": "তরল সার",
}
FERTILIZER_USED_LABEL_YES = "ব্যবহার হয়েছে"
FERTILIZER_USED_LABEL_NO = "ব্যবহার হয়নি"
FERTILIZER_USED_PROMPT = "এই কাজে সার ব্যবহার করেছেন কি?"
FERTILIZER_KIND_PROMPT = "সারের ধরন বেছে নিন।"
FERTILIZER_PRODUCT_PROMPT = "পণ্যের নাম লিখুন।\nউদাহরণ: মিশ্র সার 21-17-17"
FERTILIZER_AMOUNT_PROMPT = "পরিমাণ লিখুন।\nউদাহরণ: 20kg, ১ বস্তা"
FERTILIZER_DATE_PROMPT = "ব্যবহারের তারিখ লিখুন।\nউদাহরণ: 2026-04-21, আজ, কাল"
FERTILIZER_CONFIRM_PROMPT = "সারের তথ্য দেখে নিন।"
FERTILIZER_USED_FALLBACK = "হ্যাঁ বা না বেছে নিন।"
FERTILIZER_KIND_FALLBACK = "সারের ধরন বোতাম বেছে নিন।"
FERTILIZER_PRODUCT_FALLBACK = "পণ্যের নাম আবার লিখুন।"
FERTILIZER_AMOUNT_FALLBACK = "পরিমাণ আবার লিখুন।\nউদাহরণ: 20kg, ১ বস্তা"
FERTILIZER_DATE_FALLBACK = "তারিখ আবার লিখুন।\nউদাহরণ: 2026-04-21, আজ, কাল"
FERTILIZER_CONFIRM_FALLBACK = "[ঠিক আছে] চাপুন বা ফিরে গিয়ে বদলান।"
FERTILIZER_CONFIRMED_MESSAGE = "সারের তথ্য এ সেশনে রাখা হয়েছে।"
FERTILIZER_EDIT_MESSAGE = "কোন সারের অংশ বদলাবেন, বেছে নিন।"
FERTILIZER_EDIT_SELECTION_CONFIRMATION_MESSAGE = "সারের অংশ আবার বেছে নিতে চান?\n[{edit_button}] চাপলে বদলানোর পর্দা খুলবে।"
FERTILIZER_NOT_FOUND_MESSAGE = "এখনো কোনো সারের তথ্য নেই।\nআগে সারের ইনপুট শেষ করুন।"
FERTILIZER_REPAIR_USED_MESSAGE = "সার ব্যবহার হয়েছে কি না, আবার লিখুন।"
FERTILIZER_REPAIR_KIND_MESSAGE = "সারের ধরন আবার লিখুন।"
FERTILIZER_REPAIR_PRODUCT_MESSAGE = "সারের পণ্যের নাম আবার লিখুন।"
FERTILIZER_REPAIR_AMOUNT_MESSAGE = "সারের পরিমাণ আবার লিখুন।"
FERTILIZER_REPAIR_DATE_MESSAGE = "সার ব্যবহারের তারিখ আবার লিখুন।"
FERTILIZER_DIRECT_UPDATE_MESSAGE = "পরিবর্তন নিলাম।\nদেখে [ঠিক আছে] চাপুন।"
YIELD_READY_PROMPT = "ফসল তোলার জন্য প্রস্তুত কি?"
YIELD_FIELD_PROMPT = "যে ক্ষেত থেকে ফসল তোলা হয়েছে, তা বেছে নিন বা লিখুন।"
YIELD_AMOUNT_PROMPT = "ফসলের পরিমাণ লিখুন।\nউদাহরণ: 320kg"
YIELD_DATE_PROMPT = "ফসল তোলার তারিখ লিখুন।\nউদাহরণ: 2026-04-21, আজ, কাল"
YIELD_CONFIRM_PROMPT = "ফসলের তথ্য দেখে নিন।"
YIELD_READY_FALLBACK = "হ্যাঁ বা না বেছে নিন।"
YIELD_FIELD_FALLBACK = "ক্ষেতের নাম আবার লিখুন।"
YIELD_AMOUNT_FALLBACK = "ফসলের পরিমাণ আবার লিখুন।\nউদাহরণ: 320kg"
YIELD_DATE_FALLBACK = "ফসল তোলার তারিখ আবার লিখুন।\nউদাহরণ: 2026-04-21, আজ, কাল"
YIELD_CONFIRM_FALLBACK = "[ঠিক আছে] চাপুন বা ফিরে গিয়ে বদলান।"
YIELD_EDIT_MESSAGE = "ফসলের কোন অংশ বদলাবেন, বেছে নিন।"
YIELD_EDIT_SELECT_FALLBACK = "বদলাতে চান এমন অংশ বেছে নিন। [বদলানো শুরু], ফিরে যান, আবার শুরু - এর মধ্যে একটি নিন।"
YIELD_CONFIRMED_MESSAGE = "ফসলের তথ্য এ সেশনে রাখা হয়েছে।"
INPUT_RESOLVE_TARGET_PROMPT = "যে মান ঠিক করতে হবে, তা বেছে নিন।"
INPUT_RESOLVE_METHOD_PROMPT = "কীভাবে দেবেন, তা বেছে নিন।\nলিখে, ছবি দিয়ে, বা আবার চেষ্টা করে এগোন।"
INPUT_RESOLVE_RAW_INPUT_PROMPT = "ঠিক করার জন্য মূল লেখা লিখুন বা পাঠান।"
INPUT_RESOLVE_CANDIDATES_PROMPT = "পছন্দগুলো দেখে 1-3 বেছে নিন বা আবার চেষ্টা করুন।"
INPUT_RESOLVE_DECISION_PROMPT = "ঠিক করা, আবার চেষ্টা, বা হাতে দেখা - একটি বেছে নিন।"


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "দেখে নিন।\n"
        f"- নাম: {name}\n"
        f"- ঠিকানা: {residence}\n"
        f"- জেলা/বিভাগ: {city}\n"
        f"- উপজেলা/থানা: {district}\n"
        f"- জন্মতারিখ: {birth_date}\n"
        "\nঠিক হলে [ঠিক আছে], না হলে [বদলান] চাপুন।"
    )


def format_repair_confirmation(*, field_label: str, edit_button: str) -> str:
    return (
        f"{field_label} অংশটি আবার বেছে নিতে চান?\n"
        f"[{edit_button}] চাপলে আবার লিখতে পারবেন।"
    )


def format_change_preview(*, field_label: str, before_value: str, after_value: str) -> str:
    return (
        f"{field_label} বদলানো হয়েছে। দেখে নিন।\n"
        f"- আগে: {before_value}\n"
        f"- এখন: {after_value}"
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
        "এখনকার প্রোফাইল।\n"
        f"- নাম: {name}\n"
        f"- ঠিকানা: {residence}\n"
        f"- জেলা/বিভাগ: {city}\n"
        f"- উপজেলা/থানা: {district}\n"
        f"- জন্মতারিখ: {birth_date}"
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
            "সারের তথ্য দেখে নিন।\n"
            "- সার ব্যবহার: না\n\n"
            "ঠিক হলে [ঠিক আছে] চাপুন।"
        )
    return (
        "সারের তথ্য দেখে নিন।\n"
        f"- সার ব্যবহার: {'হ্যাঁ' if used else '-'}\n"
        f"- ধরন: {kind_label}\n"
        f"- পণ্য: {product_name}\n"
        f"- পরিমাণ: {amount_text}\n"
        f"- তারিখ: {applied_date}\n\n"
        "ঠিক হলে [ঠিক আছে] চাপুন।"
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
            "সংরক্ষিত সারের তথ্য।\n"
            "- সার ব্যবহার: না"
        )
    return (
        "সংরক্ষিত সারের তথ্য।\n"
        f"- সার ব্যবহার: {'হ্যাঁ' if used else '-'}\n"
        f"- ধরন: {kind_label}\n"
        f"- পণ্য: {product_name}\n"
        f"- পরিমাণ: {amount_text}\n"
        f"- তারিখ: {applied_date}"
    )


def format_yield_confirmation(
    *,
    ready: bool | None,
    field_name: str,
    amount_text: str,
    harvest_date: str,
) -> str:
    return (
        "ফসলের তথ্য দেখে নিন।\n"
        f"- ফসল প্রস্তুত: {'প্রস্তুত' if ready else 'এখনও না' if ready is False else '-'}\n"
        f"- ক্ষেত: {field_name}\n"
        f"- পরিমাণ: {amount_text}\n"
        f"- তারিখ: {harvest_date}\n\n"
        "ঠিক হলে [ঠিক আছে] চাপুন।"
    )


def format_support_admin_reply(*, admin_message: str) -> str:
    return (
        "সহায়তা থেকে উত্তর এসেছে।\n"
        f"{admin_message}\n\n"
        "আর কিছু যোগ করতে চাইলে এই চ্যাটেই লিখুন।"
    )


WEATHER_CODE_LABELS = {
    0: "মেঘমুক্ত",
    1: "প্রায় পরিষ্কার",
    2: "আংশিক মেঘলা",
    3: "মেঘলা",
    45: "কুয়াশা",
    48: "তুষার কুয়াশা",
    51: "হালকা কুড়ি বৃষ্টি",
    53: "কুড়ি বৃষ্টি",
    55: "জোর কুড়ি বৃষ্টি",
    56: "হালকা জমাট কুড়ি বৃষ্টি",
    57: "জোর জমাট কুড়ি বৃষ্টি",
    61: "হালকা বৃষ্টি",
    63: "বৃষ্টি",
    65: "জোর বৃষ্টি",
    66: "হালকা জমাট বৃষ্টি",
    67: "জোর জমাট বৃষ্টি",
    71: "হালকা তুষার",
    73: "তুষার",
    75: "জোর তুষার",
    77: "তুষার দানা",
    80: "হালকা ঝরনা",
    81: "ঝরনা",
    82: "জোর ঝরনা",
    85: "হালকা তুষার ঝরনা",
    86: "জোর তুষার ঝরনা",
    95: "বজ্রঝড়",
    96: "হালকা শিলাবৃষ্টি সহ বজ্রঝড়",
    99: "জোর শিলাবৃষ্টি সহ বজ্রঝড়",
}


def weather_code_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"অজানা অবস্থা ({code})")


def format_today_date(current: datetime) -> str:
    weekdays = ["সোম", "মঙ্গল", "বুধ", "বৃহ", "শুক্র", "শনি", "রবি"]
    weekday = weekdays[current.weekday()]
    return (
        "আজকের তারিখ।\n"
        f"- তারিখ: {current.strftime('%Y-%m-%d')} ({weekday})\n"
        f"- সময়: {current.strftime('%H:%M:%S')} KST"
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
        f"{city} - এখনকার আবহাওয়া।\n"
        f"- সময়: {observed_at.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"- অবস্থা: {weather_label}\n"
        f"- তাপমাত্রা: {temperature:.1f}°C\n"
        f"- অনুভূত তাপমাত্রা: {apparent_temperature:.1f}°C\n"
        f"- বাতাসের গতি: {wind_speed:.1f} km/h"
    )
