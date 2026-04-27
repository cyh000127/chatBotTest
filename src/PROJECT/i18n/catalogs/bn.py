from datetime import datetime

BUTTON_TODAY_DATE = "আজকের তারিখ"
BUTTON_TODAY_WEATHER = "আজকের আবহাওয়া"
BUTTON_FERTILIZER = "সার দেওয়া"
BUTTON_YIELD = "ফসলের পরিমাণ"
BUTTON_MYFIELDS = "আমার ক্ষেত"
BUTTON_EVIDENCE = "প্রমাণ জমা"
BUTTON_FIELD_REGISTER = "ক্ষেত নিবন্ধন"
BUTTON_FIELD_REFRESH = "রিফ্রেশ"
BUTTON_FIELD_LOOKUP_LOCATION = "অবস্থান দিয়ে খুঁজুন"
BUTTON_FIELD_LOOKUP_CODE = "ক্ষেতের কোড লিখুন"
BUTTON_INPUT_RESOLVE = "ইনপুট বুঝে নিন"
BUTTON_INPUT_RESOLVE_TARGET_FIELD_CODE = "ক্ষেতের কোড"
BUTTON_INPUT_RESOLVE_TARGET_FIELD_NAME = "ক্ষেতের নাম"
BUTTON_INPUT_RESOLVE_METHOD_TYPED_TEXT = "লিখে দিন"
BUTTON_INPUT_RESOLVE_CONFIRM_CANDIDATE = "এইটিই নিন"
BUTTON_INPUT_RESOLVE_RETRY = "আবার দিন"
BUTTON_INPUT_RESOLVE_RETRY_LATER = "পরে"
BUTTON_INPUT_RESOLVE_MANUAL_REVIEW = "হাতে দেখে নিন"
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
BUTTON_EDIT_PHONE = "ফোন"
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
AUTH_START_PROMPT = "আপনার আইডি লিখুন।\nউদাহরণ: /start sample-user বা sample-user"
AUTH_REQUIRED_MESSAGE = "আগে লগইন করতে হবে।\n/start চাপুন, তারপর আপনার আইডি লিখুন।"
AUTH_INVALID_MESSAGE = "এই আইডি ঠিক নয়। আবার লিখুন।"
AUTH_RETRY_LIMIT_MESSAGE = "দুইবার ভুল হয়েছে।\nআবার শুরু করুন। /start দিন।"
AUTH_WELCOME_MESSAGE = "স্বাগতম {user_name}।"
AUTH_ALREADY_LOGGED_IN_MESSAGE = "ফিরে এলেন {user_name}।"
START_REQUIRED_MESSAGE = "আগে /start দিয়ে শুরু করুন।"
ONBOARDING_INVITE_REQUIRED_MESSAGE = "আমন্ত্রণ কোড দরকার।\nকোড থাকলে /start <invite_code> দিয়ে শুরু করুন।"
ONBOARDING_INVALID_INVITE_MESSAGE = "আমন্ত্রণ কোড যাচাই করা যায়নি।\nকোড দেখে আবার /start <invite_code> লিখুন।"
ONBOARDING_IDENTITY_REQUIRED_MESSAGE = "আপনার Telegram ব্যবহারকারী তথ্য পড়া যায়নি।\nকিছুক্ষণ পরে আবার চেষ্টা করুন।"
ONBOARDING_STARTED_MESSAGE = "আমন্ত্রণ কোড যাচাই হয়েছে।\nঅনবোর্ডিং চালিয়ে যেতে ভাষা বেছে নিন।"
ONBOARDING_ACCESS_REQUIRED_MESSAGE = "সেবা ব্যবহারের আগে অনবোর্ডিং এবং অ্যাডমিন অনুমোদন দরকার।\nআমন্ত্রণ কোড থাকলে /start <invite_code> দিয়ে শুরু করুন।"
ONBOARDING_PENDING_APPROVAL_MESSAGE = "অনবোর্ডিং এখনও শেষ হয়নি বা অ্যাডমিন অনুমোদনের অপেক্ষায় আছে।\nঅনুমোদনের পরে সেবা ব্যবহার করতে পারবেন।"
ONBOARDING_NAME_PROMPT = "আপনার নাম লিখুন।"
ONBOARDING_NAME_FALLBACK = "নাম আবার লিখুন।\nউদাহরণ: Sample Farmer"
ONBOARDING_PHONE_PROMPT = "দেশের কোডসহ ফোন নম্বর লিখুন।\nউদাহরণ: +855 12 345 678, +880 17 1234 5678"
ONBOARDING_PHONE_FALLBACK = "ফোন নম্বর আবার লিখুন।\nএখন শুধু +855 বা +880 দেশের কোড চালু আছে।"
ONBOARDING_CONFIRM_MESSAGE = (
    "অনবোর্ডিং তথ্য দেখে নিন।\n"
    "- নাম: {name}\n"
    "- ফোন: {phone}\n"
    "- ভাষা: {language}\n\n"
    "ঠিক থাকলে [ঠিক আছে] চাপুন, বদলাতে হলে একটি অংশ বেছে নিন।"
)
ONBOARDING_CONFIRM_FALLBACK = "[ঠিক আছে] চাপুন বা বদলানোর অংশ বেছে নিন।"
ONBOARDING_PENDING_APPROVAL_SUBMITTED_MESSAGE = "আপনার অনবোর্ডিং অনুরোধ অনুমোদনের জন্য পাঠানো হয়েছে।\nঅ্যাডমিন অনুমোদনের পরে সেবা ব্যবহার করতে পারবেন।"

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
UNKNOWN_COMMAND_MESSAGE = "এই কমান্ডটি চালু নেই।\nনিচ থেকে একটি বেছে নিন বা /help দিন।"
MYFIELDS_ENTRY_MESSAGE = "এটি আমার ক্ষেত অংশ।\nএখন শুধু দেখার পথ আর ফিরে যাওয়ার পথ আছে।\nনিচ থেকে অন্য কিছু বেছে নিন বা /start দিয়ে আবার শুরু করুন।"
MYFIELDS_EMPTY_MESSAGE = "এখনও কোনো ক্ষেত নিবন্ধিত নেই।\nক্ষেত নিবন্ধন শুরু করুন।"
MYFIELDS_SUMMARY_MESSAGE = "এগুলো আপনার নিবন্ধিত ক্ষেত।"
MYFIELDS_SUMMARY_GUIDANCE = "আপনি আরও ক্ষেত যোগ করতে পারেন বা তালিকা রিফ্রেশ করতে পারেন।"
MYFIELDS_METHOD_PROMPT = "ক্ষেত নিবন্ধনের পদ্ধতি বেছে নিন।\nঅবস্থান বা ক্ষেতের কোড দিয়ে এগোনো যাবে।"
MYFIELDS_LOCATION_PROMPT = "Telegram attachment menu ব্যবহার করে আপনার বর্তমান অবস্থান পাঠান।\nমেসেজ বক্সের attachment menu খুলে Location বেছে নিন।"
MYFIELDS_CODE_PROMPT = "ক্ষেতের কোড লিখুন।\nউদাহরণ: FIELD-001"
MYFIELDS_NO_REGISTRY_MESSAGE = "এখনও কোনো প্রকাশিত ক্ষেত রেজিস্ট্রি নেই।\nপরে আবার চেষ্টা করুন বা সহায়তা চান।"
MYFIELDS_LOCATION_NO_CANDIDATE_MESSAGE = "এই অবস্থানের জন্য কোনো ক্ষেত পাওয়া যায়নি।\nক্ষেতের কোড লিখুন বা আবার চেষ্টা করুন।"
MYFIELDS_CODE_NOT_FOUND_MESSAGE = "এই ক্ষেতের কোড পাওয়া যায়নি।\nআবার লিখুন বা অবস্থান দিয়ে খোঁজা বেছে নিন।"
MYFIELDS_CANDIDATE_PROMPT = "সম্ভাব্য ক্ষেত পাওয়া গেছে।\nনিচে সঠিক ক্ষেতটি বেছে নিন।"
MYFIELDS_CONFIRM_MESSAGE = "ক্ষেত সংযোগটি যাচাই করুন।"
MYFIELDS_CONFIRM_GUIDANCE = "সঠিক হলে [Confirm] চাপুন।"
MYFIELDS_BINDING_CONFIRMED_MESSAGE = "ক্ষেত নিবন্ধিত হয়েছে।"
MYFIELDS_BINDING_CONFLICT_MESSAGE = "এই ক্ষেত এখনই নিবন্ধন করা যাবে না।\nএটি অপারেশন পর্যালোচনায় পাঠানো হয়েছে। অন্য পদ্ধতি বেছে নিন।"
MYFIELDS_LOOKUP_METHOD_LOCATION_LABEL = "অবস্থান"
MYFIELDS_LOOKUP_METHOD_CODE_LABEL = "ক্ষেতের কোড"
EVIDENCE_RUNTIME_UNAVAILABLE_MESSAGE = "প্রমাণ জমা দেওয়ার রানটাইম এখন পাওয়া যাচ্ছে না।\nপরে আবার চেষ্টা করুন বা সহায়তা নিন।"
EVIDENCE_ENTRY_MESSAGE = "প্রমাণ জমা শুরু হচ্ছে।\nআগে আপনার বর্তমান অবস্থান পাঠান।"
EVIDENCE_DOCUMENT_PROMPT = "অবস্থান গ্রহণ করা হয়েছে।\nএখন মূল ফাইলটি document হিসেবে আপলোড করুন।"
EVIDENCE_LOCATION_FALLBACK = "এই ধাপে আপনার বর্তমান অবস্থান দরকার।\nTelegram-এর location attachment ব্যবহার করুন।"
EVIDENCE_DOCUMENT_FALLBACK = "এই ধাপে মূল ফাইলটি document upload হিসেবে দরকার।\nছবির বদলে document attachment ব্যবহার করুন।"
EVIDENCE_VALIDATING_MESSAGE = "প্রমাণ ফাইলটি পাওয়া গেছে।\nপরের নির্দেশনার জন্য অপেক্ষা করুন বা সম্পর্কিত কাজ বেছে নিন।"
EVIDENCE_ACCEPTED_MESSAGE = "প্রমাণ জমা সম্পূর্ণ হয়েছে।\nমৌলিক যাচাই পেরিয়েছে।"
EVIDENCE_RETRY_REQUIRED_MESSAGE = "অনুগ্রহ করে প্রমাণটি আবার জমা দিন।"
EVIDENCE_MANUAL_REVIEW_MESSAGE = "প্রমাণ জমা ম্যানুয়াল রিভিউতে পাঠানো হয়েছে।"
EVIDENCE_REASON_MISSING_EXIF = "EXIF তথ্য নেই।"
EVIDENCE_REASON_MISSING_GPS = "GPS তথ্য নেই।"
EVIDENCE_REASON_MISSING_CAPTURE_TIME = "ছবি তোলার সময়ের তথ্য নেই।"
EVIDENCE_REASON_LOCATION_DISTANCE_TOO_FAR = "বর্তমান অবস্থান ও ছবির GPS-এর দূরত্ব বেশি।"
INPUT_RESOLVE_ENTRY_MESSAGE = "এটি ইনপুট বুঝে নেওয়ার অংশ।\nএখন কোন মান নিতে হবে, আগে সেটা গুছিয়ে নিচ্ছি।\nপরের ধাপে মিল খোঁজা আর হাতে দেখা হবে।"
INPUT_RESOLVE_TARGET_FALLBACK = "যে মান ঠিক করতে হবে, তা বোতাম দিয়ে বেছে নিন।"
INPUT_RESOLVE_METHOD_FALLBACK = "এই ধাপে এখন শুধু লিখে দেওয়া যাবে।\n[লিখে দিন] বেছে নিন।"
INPUT_RESOLVE_RAW_INPUT_FALLBACK = "মূল মানটি আবার লিখুন।\nউদাহরণ: FIELD-001, Plot 1"
INPUT_RESOLVE_CANDIDATE_NONE_MESSAGE = "মিল পাওয়া যায়নি।\nআবার দিন, পরে করুন, বা হাতে দেখার জন্য পাঠান।"
INPUT_RESOLVE_MANUAL_REVIEW_MESSAGE = "ইনপুট বুঝে নেওয়ার অনুরোধ হাতে দেখার জন্য পাঠানো হয়েছে।\nপরের নির্দেশনা এই একই চ্যাটে আসবে।"
INPUT_RESOLVE_INVALID_RESUME_MESSAGE = "পরে চালিয়ে যাওয়ার তথ্য যাচাই করা যায়নি।\n/resolve দিয়ে আবার শুরু করুন বা সহায়তা চান।"
INPUT_RESOLVE_STEP_TARGET_LABEL = "মান বেছে নেওয়া"
INPUT_RESOLVE_STEP_METHOD_LABEL = "পদ্ধতি বেছে নেওয়া"
INPUT_RESOLVE_STEP_RAW_INPUT_LABEL = "মূল লেখা দেওয়া"
INPUT_RESOLVE_STEP_CANDIDATES_LABEL = "পছন্দ দেখা"
INPUT_RESOLVE_STEP_DECISION_LABEL = "পছন্দ ঠিক করা"
SUPPORT_ESCALATION_MESSAGE = "সহায়তার অনুরোধ পাঠানো হয়েছে।\nনতুন চ্যাট খুলছি না। এই চ্যাটেই উত্তর আসবে।\nফিরে যেতে /help, /menu, বা /start দিন।"
SUPPORT_HANDOFF_MESSAGE_RECORDED = "অতিরিক্ত কথা সহায়তার নোটে রাখা হয়েছে।\nএই চ্যাটেই উত্তর আসবে।\nআবার শুরু করতে /start দিন।"
SUPPORT_HANDOFF_CLOSED_MESSAGE = "সহায়তা শেষ হয়েছে।\nচাইলে এই চ্যাটে আবার সাহায্য চাইতে পারেন।"
CANONICAL_WRITE_FAILURE_MESSAGE = "ইনপুট সংরক্ষণ করতে সমস্যা হয়েছে।\nআবার চেষ্টা করুন বা /support ব্যবহার করুন।"

HELP_MESSAGE = (
    "ব্যবহার করতে পারেন:\n"
    "- /start : শুরুতে যান\n"
    "- /help : সাহায্য দেখুন\n"
    "- /menu : মূল মেনু খুলুন\n"
    "- /myfields : আমার ক্ষেত খুলুন\n"
    "- /fertilizer : সার দেওয়া শুরু করুন\n"
    "- /yield : ফসলের পরিমাণ শুরু করুন\n"
    "- /evidence : প্রমাণ জমা শুরু করুন\n"
    "- /resolve : ইনপুট বুঝে নিন\n"
    "- /support : সহায়তা খুলুন\n"
    "- /language : ভাষা বদলান\n"
    "- ফিরে যান : আগের ধাপে যান\n"
    "- আবার শুরু : শুরু থেকে আবার করুন"
)

FALLBACK_MESSAGES = {
    "default": "ইনপুটটি নেওয়া যায়নি।\nনিচ থেকে একটি বেছে নিন।",
    "weather": "ইনপুটটি নেওয়া যায়নি।\nনিচে শহর বেছে নিন বা ফিরে যান চাপুন।",
    "cancelled": "এই কাজ শেষ হয়েছে।\nচালিয়ে যেতে নিচ থেকে একটি বেছে নিন।",
    "fertilizer_input": "সারের ইনপুট নেওয়া যায়নি।\nচালিয়ে যেতে নিচের অংশ থেকে একটি বেছে নিন।",
    "fertilizer_confirm": "সার দেখার ধাপে আছেন।\nঠিক আছে বা ফিরে যান বেছে নিন।",
    "yield_input": "ফসলের ইনপুট নেওয়া যায়নি।\nচালিয়ে যেতে নিচের অংশ থেকে একটি বেছে নিন।",
    "yield_confirm": "ফসল দেখার ধাপে আছেন।\nঠিক আছে বা ফিরে যান বেছে নিন।",
    "myfields_input": "ক্ষেত নিবন্ধনের ইনপুট প্রক্রিয়া করা যায়নি।\nএই ধাপের জন্য সঠিক পদ্ধতিটি বেছে নিন।",
    "myfields_confirm": "আপনি ক্ষেত যাচাই ধাপে আছেন।\nনিচে Confirm অথবা অন্য পদ্ধতি বেছে নিন।",
    "evidence_input": "প্রমাণ জমা ধাপটি প্রক্রিয়া করা যায়নি।\nএই ধাপের সঙ্গে মিলে এমন অবস্থান বা document upload আবার পাঠান।",
    "evidence_status": "প্রমাণ ফাইলটি আগেই পাওয়া গেছে।\nপরের নির্দেশনার জন্য অপেক্ষা করুন বা সম্পর্কিত কাজ বেছে নিন।",
    "input_resolve_input": "ইনপুট বুঝে নেওয়ার ধাপটি করা যায়নি।\nমিল থাকা বোতাম বা ছোট উদাহরণ আবার পাঠান।",
    "input_resolve_confirm": "এটি পছন্দ দেখার ধাপ।\nএকটি পছন্দ নিন, আবার দিন, পরে করুন, বা হাতে দেখার জন্য পাঠান।",
}
RECOVERY_GUIDANCE_SOFT = "এই ধাপে কী লাগবে, আবার বলছি।"
RECOVERY_GUIDANCE_GUIDED = "চালিয়ে যেতে নিচের নির্দেশনা দেখুন।"
RECOVERY_GUIDANCE_ESCALATION_READY = "বারবার সমস্যা হলে নিচের বিকল্প নিন।"
RECOVERY_MULTI_SLOT_CANDIDATE_HINT = "একটি বার্তায় কয়েকটি মান পেয়েছি।\nচালিয়ে যাওয়ার আগে খসড়া দেখুন।"
RECOVERY_MULTI_SLOT_APPLIED_MESSAGE = "কয়েকটি মান খসড়ায় বসানো হয়েছে।\nনিচের লেখা দেখে নিন।"
CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE = (
    "এটি সহায়তার অনুরোধ।\n"
    "সহায়তার নোটে রাখা হয়েছে। উত্তর এই চ্যাটেই আসবে।\n"
    "চালিয়ে যেতে নিচ থেকে একটি বেছে নিন বা /help দিন।"
)
CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE = (
    "এটি পরে একজন মানুষের দেখা দরকার।\n"
    "পরের দেখার জন্য রাখা হয়েছে। দরকারি কথা এই চ্যাটেই থাকবে।\n"
    "চালিয়ে যেতে নিচ থেকে একটি বেছে নিন।"
)
CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE = (
    "কয়েকবার দেখা হয়েছে, কিন্তু এখনো স্বয়ংক্রিয়ভাবে মেলানো যাচ্ছে না।\n"
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
PROFILE_DIRECT_UPDATE_MESSAGE = "পরিবর্তন রাখা হয়েছে।\nদেখে [ঠিক আছে] চাপুন।"
LLM_REPAIR_CANDIDATE_HINT = "\"{candidate_value}\" বদলানোর অনুরোধ পাওয়া গেছে।\nঠিক হলে বদলানো শুরু চাপুন।"
LLM_REPAIR_UNSUPPORTED_MESSAGE = "কোন অংশ বদলাতে হবে, বোঝা যায়নি।\nনিচের অংশ থেকে সরাসরি বেছে নিন।"
LLM_REPAIR_LOW_CONFIDENCE_MESSAGE = "কোন অংশ বদলাতে হবে, নিশ্চিত করা যায়নি।\nনিচের অংশ থেকে সরাসরি বেছে নিন।"
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
FERTILIZER_DIRECT_UPDATE_MESSAGE = "পরিবর্তন রাখা হয়েছে।\nদেখে [ঠিক আছে] চাপুন।"
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


def format_input_resolve_candidate_list(*, target_label: str, raw_input: str, candidates: tuple[str, ...]) -> str:
    candidate_lines = "\n".join(f"{index}. {candidate}" for index, candidate in enumerate(candidates, start=1))
    return (
        f"{target_label} এর জন্য পছন্দ পাওয়া গেছে।\n"
        f"- মূল লেখা: {raw_input}\n\n"
        f"{candidate_lines}\n\n"
        "মিল থাকা পছন্দটি নিন বা আবার দিন।"
    )


def format_input_resolve_selected_candidate(*, target_label: str, candidate_label: str) -> str:
    return (
        f"{target_label} এর পছন্দটি দেখুন।\n"
        f"- বেছে নেওয়া পছন্দ: {candidate_label}\n\n"
        "এইটিই নিন, আবার দিন, পরে করুন, বা হাতে দেখে নিতে পাঠান।"
    )


def format_input_resolve_resolved(*, target_label: str, candidate_label: str) -> str:
    return (
        "বুঝে নেওয়া মানটি সংরক্ষণ করা হয়েছে।\n"
        f"- লক্ষ্য: {target_label}\n"
        f"- মান: {candidate_label}"
    )


def format_input_resolve_reminder(*, command_text: str) -> str:
    return (
        "সংরক্ষিত ইনপুট বুঝে নেওয়ার কাজ আবার চালানোর সময় হয়েছে।\n"
        f"আবার খুলতে {command_text} লিখুন।"
    )


def format_input_resolve_reminder_created(*, command_text: str) -> str:
    return (
        "পরে চালিয়ে যাওয়ার জন্য সংরক্ষণ করা হয়েছে।\n"
        f"চালাতে চাইলে {command_text} লিখুন।"
    )


def format_input_resolve_resumed(*, step_label: str, prompt_text: str) -> str:
    return f"সংরক্ষিত ইনপুট বুঝে নেওয়ার ধাপ আবার খোলা হয়েছে।\nবর্তমান ধাপ: {step_label}\n\n{prompt_text}"


def format_evidence_entry(*, field_label: str) -> str:
    return (
        f"{EVIDENCE_ENTRY_MESSAGE}\n"
        f"- বর্তমান যুক্ত ক্ষেত: {field_label}"
    )


def format_evidence_uploaded(*, file_name: str) -> str:
    return (
        "প্রমাণ ফাইলটি পাওয়া গেছে।\n"
        f"- ফাইলের নাম: {file_name}\n\n"
        "মৌলিক যাচাই প্রস্তুত হলে একই ধাপে পরের নির্দেশনা চলবে।"
    )


def format_evidence_accepted(*, file_name: str) -> str:
    return (
        f"{EVIDENCE_ACCEPTED_MESSAGE}\n"
        f"- ফাইলের নাম: {file_name}"
    )


def format_evidence_retry_required(*, file_name: str, reason_lines: tuple[str, ...]) -> str:
    reason_text = "\n".join(f"- {line}" for line in reason_lines)
    return (
        f"{EVIDENCE_RETRY_REQUIRED_MESSAGE}\n"
        f"- ফাইলের নাম: {file_name}\n"
        f"{reason_text}\n\n"
        "একই ধাপে document আবার আপলোড করুন।"
    )


def format_evidence_manual_review(*, file_name: str, reason_lines: tuple[str, ...]) -> str:
    reason_text = "\n".join(f"- {line}" for line in reason_lines)
    reason_block = f"{reason_text}\n\n" if reason_text else ""
    return (
        f"{EVIDENCE_MANUAL_REVIEW_MESSAGE}\n"
        f"- ফাইলের নাম: {file_name}\n"
        f"{reason_block}"
        "পরের নির্দেশনা এই একই চ্যাটে চলবে।"
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
