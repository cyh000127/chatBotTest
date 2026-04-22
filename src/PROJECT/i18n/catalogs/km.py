from datetime import datetime

BUTTON_TODAY_DATE = "កាលបរិច្ឆេទថ្ងៃនេះ"
BUTTON_TODAY_WEATHER = "អាកាសធាតុថ្ងៃនេះ"
BUTTON_PROFILE = "បញ្ចូលប្រវត្តិ"
BUTTON_FERTILIZER = "បញ្ចូលជី"
BUTTON_HELP = "ជំនួយ"
BUTTON_BACK = "ថយក្រោយ"
BUTTON_CANCEL = "បោះបង់"
BUTTON_RESTART = "ចាប់ផ្តើមឡើងវិញ"
BUTTON_CONFIRM = "បញ្ជាក់"
BUTTON_EDIT = "កែប្រែ"
BUTTON_EDIT_START = "ចាប់ផ្តើមកែ"
BUTTON_KEEP_CURRENT = "ទុកដដែល"
BUTTON_APPLY_SUGGESTED_VALUE = "ប្រើតម្លៃនេះ"
BUTTON_ENTER_VALUE_DIRECTLY = "បញ្ចូលម្តងទៀតដោយដៃ"
BUTTON_YES = "បាទ/ចាស"
BUTTON_NO = "ទេ"
BUTTON_EDIT_NAME = "ឈ្មោះ"
BUTTON_EDIT_RESIDENCE = "ទីលំនៅ"
BUTTON_EDIT_CITY = "រាជធានី/ខេត្ត"
BUTTON_EDIT_DISTRICT = "ខណ្ឌ/ស្រុក/ក្រុង"
BUTTON_EDIT_BIRTH_DATE = "ថ្ងៃខែឆ្នាំកំណើត"
BUTTON_FERTILIZER_EDIT_USED = "ការប្រើជី"
BUTTON_FERTILIZER_EDIT_KIND = "ប្រភេទជី"
BUTTON_FERTILIZER_EDIT_PRODUCT = "ឈ្មោះផលិតផល"
BUTTON_FERTILIZER_EDIT_AMOUNT = "បរិមាណ"
BUTTON_FERTILIZER_EDIT_DATE = "ថ្ងៃប្រើ"
BUTTON_PREV_YEARS = "12 ឆ្នាំមុន"
BUTTON_NEXT_YEARS = "12 ឆ្នាំបន្ទាប់"
BUTTON_FERTILIZER_KIND_COMPOUND = "ជីចម្រុះ"
BUTTON_FERTILIZER_KIND_UREA = "យូរ៉េ"
BUTTON_FERTILIZER_KIND_COMPOST = "ជីកំប៉ុស"
BUTTON_FERTILIZER_KIND_LIQUID = "ជីរាវ"

LANGUAGE_NAME = "ខ្មែរ"
LANGUAGE_MENU_MESSAGE = "សូមជ្រើសរើសភាសា។"
LANGUAGE_CHANGED_MESSAGE = "បានប្តូរភាសាទៅជាខ្មែរ។"
AUTH_START_PROMPT = "សូមបញ្ចូលអត្តសញ្ញាណចូលប្រើ។\nឧទាហរណ៍៖ /start okccc5 ឬ okccc5"
AUTH_REQUIRED_MESSAGE = "ត្រូវការការផ្ទៀងផ្ទាត់ជាមុនសិន។\nសូមវាយ /start ហើយបញ្ចូលអត្តសញ្ញាណរបស់អ្នក។"
AUTH_INVALID_MESSAGE = "អត្តសញ្ញាណមិនត្រឹមត្រូវទេ។ សូមបញ្ចូលម្ដងទៀត។"
AUTH_RETRY_LIMIT_MESSAGE = "ការផ្ទៀងផ្ទាត់បានបរាជ័យ 2 ដង។\nសូមចាប់ផ្តើមម្ដងទៀតដោយវាយ /start។"
AUTH_WELCOME_MESSAGE = "សូមស្វាគមន៍ {user_name}!"
AUTH_ALREADY_LOGGED_IN_MESSAGE = "សូមស្វាគមន៍មកវិញ {user_name}!"

CITY_BUTTON_TO_KEY = {
    "សេអ៊ូល": "서울",
    "ប៊ូសាន": "부산",
    "ជេជូ": "제주",
}

START_MESSAGE = "បានចាប់ផ្តើម។\nសូមជ្រើសរើសកាលបរិច្ឆេទថ្ងៃនេះ ឬ អាកាសធាតុថ្ងៃនេះ។"
MAIN_MENU_MESSAGE = "ម៉ឺនុយមេ។\nសូមជ្រើសរើសកាលបរិច្ឆេទថ្ងៃនេះ ឬ អាកាសធាតុថ្ងៃនេះ។"
WEATHER_MENU_MESSAGE = "សូមជ្រើសរើសទីក្រុងដើម្បីពិនិត្យអាកាសធាតុថ្ងៃនេះ។"
PROFILE_ENTRY_MESSAGE = (
    "ចាប់ផ្តើមបញ្ចូលប្រវត្តិ។\n"
    "ដំបូងសូមបញ្ចូលឈ្មោះ។"
)
CANCEL_MESSAGE = "បានបោះបង់ដំណើរការបច្ចុប្បន្ន។\nសូមប្រើ 'ចាប់ផ្តើមឡើងវិញ' ឬ /start ដើម្បីចាប់ផ្តើមម្ដងទៀត។"
BACK_LIMIT_MESSAGE = "មិនមានជំហានមុនទេ។\nសូមជ្រើសរើសម្ដងទៀតពីម៉ឺនុយមេ។"
BACK_TO_MAIN_MESSAGE = "បានត្រឡប់ទៅជំហានមុន។\nសូមជ្រើសរើសម្ដងទៀត។"
BACK_TO_WEATHER_MESSAGE = "បានត្រឡប់ទៅជំហានជ្រើសរើសអាកាសធាតុ។\nសូមជ្រើសរើសទីក្រុងម្ដងទៀត។"
BACK_GENERIC_MESSAGE = "បានត្រឡប់ទៅស្ថានភាពមុន។"
WEATHER_ERROR_MESSAGE = "មិនអាចទាញយកព័ត៌មានអាកាសធាតុបានទេ។\nសូមព្យាយាមម្ដងទៀតបន្តិចក្រោយ។"
UNKNOWN_COMMAND_MESSAGE = "ពាក្យបញ្ជានេះមិនត្រូវបានគាំទ្រទេ។\nសូមជ្រើសធាតុដែលពាក់ព័ន្ធខាងក្រោម ឬប្រើ /help។"

HELP_MESSAGE = (
    "ពាក្យបញ្ជាដែលអាចប្រើបាន៖\n"
    "- /start : ត្រឡប់ទៅចំណុចចាប់ផ្តើម\n"
    "- /help : បង្ហាញជំនួយ\n"
    "- /menu : បើកម៉ឺនុយមេ\n"
    "- /profile : ចាប់ផ្តើមបញ្ចូលប្រវត្តិ\n"
    "- /fertilizer : ចាប់ផ្តើមបញ្ចូលជី\n"
    "- /language : ប្តូរភាសា\n"
    "- ថយក្រោយ : ត្រឡប់ទៅជំហានមុន\n"
    "- បោះបង់ : បញ្ឈប់លំហូរបច្ចុប្បន្ន\n"
    "- ចាប់ផ្តើមឡើងវិញ : កំណត់សម័យឡើងវិញ"
)

FALLBACK_MESSAGES = {
    "default": "ខ្ញុំមិនទាន់យល់សំណើនេះភ្លាមៗទេ។\nសូមជ្រើសមុខងារដែលពាក់ព័ន្ធខាងក្រោមបានទេ?",
    "weather": "ខ្ញុំមិនទាន់យល់សំណើនេះភ្លាមៗទេ។\nសូមជ្រើសទីក្រុងខាងក្រោម ឬចុចថយក្រោយ។",
    "cancelled": "ការងារបច្ចុប្បន្នត្រូវបានបោះបង់។\nសូមជ្រើសមុខងារដែលពាក់ព័ន្ធខាងក្រោមដើម្បីបន្ត។",
    "profile_input": "ខ្ញុំមិនទាន់អាចដំណើរការការបញ្ចូលប្រវត្តិរូបនេះភ្លាមៗទេ។\nសូមជ្រើសធាតុប្រវត្តិរូបដែលពាក់ព័ន្ធខាងក្រោមដើម្បីបន្ត ឬកែប្រែ។",
    "profile_followup": "ត្រូវការការបញ្ជាក់បន្ថែម។\nសូមជ្រើសមុខងារដែលពាក់ព័ន្ធខាងក្រោមបានទេ?",
    "profile_confirm": "អ្នកកំពុងស្ថិតនៅជំហានបញ្ជាក់ប្រវត្តិរូប។\nសូមជ្រើសថាតើត្រូវបញ្ជាក់ ឬកែប្រែខាងក្រោម។",
    "fertilizer_input": "ខ្ញុំមិនទាន់អាចដំណើរការការបញ្ចូលជីនេះភ្លាមៗទេ។\nសូមជ្រើសធាតុជីដែលពាក់ព័ន្ធខាងក្រោមដើម្បីបន្ត ឬកែប្រែ។",
    "fertilizer_confirm": "អ្នកកំពុងស្ថិតនៅជំហានបញ្ជាក់ជី។\nសូមជ្រើសថាតើត្រូវបញ្ជាក់ ឬកែប្រែខាងក្រោម។",
}
CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE = (
    "សំណើនេះមើលទៅដូចជាការស្នើសុំជំនួយ ឬ ការគាំទ្រពីមនុស្ស។\n"
    "ផ្លូវ support.escalate មិនទាន់ភ្ជាប់ទៅការជជែកផ្ទាល់នៅឡើយទេ។\n"
    "សូមជ្រើសធាតុដែលពាក់ព័ន្ធខាងក្រោម ឬប្រើ /help។"
)
CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE = (
    "សំណើនេះមើលទៅជាករណីដែលត្រូវការការតាមដានបន្តពីអ្នកគ្រប់គ្រង។\n"
    "admin follow-up queue មិនទាន់ភ្ជាប់ទៅការជជែកផ្ទាល់នៅឡើយទេ។\n"
    "សូមជ្រើសធាតុដែលពាក់ព័ន្ធខាងក្រោមដើម្បីបន្ត។"
)
CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE = (
    "ខ្ញុំបានពិនិត្យការបញ្ចូលនេះជាច្រើនដង ប៉ុន្តែជំហាននេះពិបាកដោះស្រាយដោយស្វ័យប្រវត្តិ។\n"
    "វាស្រដៀងនឹងករណី manual_resolution_required។\n"
    "សូមជ្រើសធាតុដែលពាក់ព័ន្ធខាងក្រោម ឬចាប់ផ្តើមម្ដងទៀតដោយ /menu ឬ /start។"
)

PROFILE_CONFIRMED_MESSAGE = "បានបញ្ជាក់ការបញ្ចូល។\nបានរក្សាទុកក្នុងសម័យបច្ចុប្បន្ន។"
PROFILE_EDIT_MESSAGE = "សូមជ្រើសរើសព័ត៌មានដែលអ្នកចង់កែប្រែ។"
PROFILE_EDIT_SELECTION_CONFIRMATION_MESSAGE = "អ្នកចង់ជ្រើសរើសធាតុប្រវត្តិរូបដែលត្រូវកែម្ដងទៀតមែនទេ?\nចុច [{edit_button}] ហើយខ្ញុំនឹងបើកអេក្រង់ជ្រើសរើសការកែប្រែ។"
PROFILE_NOT_FOUND_MESSAGE = "មិនទាន់មានប្រវត្តិដែលបានរក្សាទុកទេ។\nសូមបំពេញប្រវត្តិជាមុនសិន។"
PROFILE_NAME_PROMPT = "សូមបញ្ចូលឈ្មោះ។"
PROFILE_RESIDENCE_PROMPT = "សូមបញ្ចូលទីលំនៅ។"
PROFILE_CITY_PROMPT = "សូមបញ្ចូលរាជធានី/ខេត្ត។\nឧទាហរណ៍៖ Seoul, Gyeonggi-do"
PROFILE_DISTRICT_PROMPT = "សូមបញ្ចូលខណ្ឌ/ស្រុក/ក្រុង។\nឧទាហរណ៍៖ Gangnam-gu, Bundang-gu"
PROFILE_BIRTH_YEAR_PROMPT = "សូមជ្រើសរើសឆ្នាំកំណើតតាមប៊ូតុង។"
PROFILE_BIRTH_MONTH_PROMPT = "សូមជ្រើសរើសខែកំណើតតាមប៊ូតុង។"
PROFILE_BIRTH_DAY_PROMPT = "សូមជ្រើសរើសថ្ងៃកំណើតតាមប៊ូតុង។"
PROFILE_NAME_FALLBACK = "សូមបញ្ចូលឈ្មោះម្ដងទៀត។"
PROFILE_RESIDENCE_FALLBACK = "សូមបញ្ចូលទីលំនៅម្ដងទៀត។"
PROFILE_CITY_FALLBACK = "សូមបញ្ចូលរាជធានី/ខេត្តឲ្យត្រឹមត្រូវម្ដងទៀត។"
PROFILE_DISTRICT_FALLBACK = "សូមបញ្ចូលខណ្ឌ/ស្រុក/ក្រុងឲ្យត្រឹមត្រូវម្ដងទៀត។"
PROFILE_BIRTH_YEAR_FALLBACK = "សូមជ្រើសរើសប៊ូតុងឆ្នាំកំណើត។"
PROFILE_BIRTH_MONTH_FALLBACK = "សូមជ្រើសរើសប៊ូតុងខែកំណើត។"
PROFILE_BIRTH_DAY_FALLBACK = "សូមជ្រើសរើសប៊ូតុងថ្ងៃកំណើត។"
PROFILE_CONFIRM_FALLBACK = "សូមជ្រើសរើស [បញ្ជាក់] ឬ [កែប្រែ]។"
PROFILE_EDIT_SELECT_FALLBACK = "សូមជ្រើសរើសព័ត៌មានដែលត្រូវកែប្រែតាមប៊ូតុង។"
PROFILE_REPAIR_NAME_MESSAGE = "យើងនឹងបញ្ចូលឈ្មោះម្ដងទៀត។"
PROFILE_REPAIR_RESIDENCE_MESSAGE = "យើងនឹងបញ្ចូលទីលំនៅម្ដងទៀត។"
PROFILE_REPAIR_CITY_MESSAGE = "យើងនឹងបញ្ចូលរាជធានី/ខេត្តម្ដងទៀត។"
PROFILE_REPAIR_DISTRICT_MESSAGE = "យើងនឹងបញ្ចូលខណ្ឌ/ស្រុក/ក្រុងម្ដងទៀត។"
PROFILE_REPAIR_BIRTH_MESSAGE = "យើងនឹងបញ្ចូលថ្ងៃខែឆ្នាំកំណើតម្ដងទៀត។\nសូមជ្រើសរើសឆ្នាំកំណើត។"
PROFILE_DIRECT_UPDATE_MESSAGE = "ខ្ញុំបានអនុវត្តការកែតាមភាសាធម្មជាតិហើយ។ សូមពិនិត្យហើយចុច [បញ្ជាក់]។"
LLM_REPAIR_CANDIDATE_HINT = "ខ្ញុំយល់ថាអ្នកចង់ប្ដូរទៅជា \"{candidate_value}\"។\nបើត្រឹមត្រូវ សូមចុច ចាប់ផ្តើមកែ។"
LLM_REPAIR_UNSUPPORTED_MESSAGE = "ខ្ញុំមិនទាន់អាចកំណត់ធាតុដែលត្រូវកែបានភ្លាមៗទេ។\nសូមជ្រើសរើសដោយផ្ទាល់ពីធាតុដែលពាក់ព័ន្ធខាងក្រោម។"
LLM_REPAIR_LOW_CONFIDENCE_MESSAGE = "ខ្ញុំមិនទាន់ប្រាកដគ្រប់គ្រាន់ថាអ្នកចង់កែធាតុណាទេ។\nសូមជ្រើសរើសដោយផ្ទាល់ពីធាតុដែលពាក់ព័ន្ធខាងក្រោម។"
LLM_REPAIR_HUMAN_REVIEW_MESSAGE = (
    "សំណើនេះពិបាកបង្រួមឱ្យនៅសល់តែធាតុកែប្រែមួយដោយស្វ័យប្រវត្តិ។\n"
    "វាអាចត្រូវការការពិនិត្យដោយមនុស្ស ដូច្នេះសូមជ្រើសរើសដោយផ្ទាល់ពីធាតុដែលពាក់ព័ន្ធខាងក្រោម។"
)
LLM_REPAIR_RUNTIME_FAILURE_MESSAGE = (
    "ខ្ញុំបានព្យាយាមបកស្រាយដោយស្វ័យប្រវត្តិ ប៉ុន្តែឥឡូវនេះវាមិនទាន់មានស្ថិរភាពគ្រប់គ្រាន់ទេ។\n"
    "សូមបន្តដោយជ្រើសរើសដោយផ្ទាល់ពីធាតុដែលពាក់ព័ន្ធខាងក្រោម។"
)

FERTILIZER_KIND_LABELS = {
    "compound": "ជីចម្រុះ",
    "urea": "យូរ៉េ",
    "compost": "ជីកំប៉ុស",
    "liquid": "ជីរាវ",
}
FERTILIZER_USED_LABEL_YES = "បានប្រើ"
FERTILIZER_USED_LABEL_NO = "មិនបានប្រើ"
FERTILIZER_USED_PROMPT = "តើអ្នកបានប្រើជីសម្រាប់ការងារនេះទេ?"
FERTILIZER_KIND_PROMPT = "សូមជ្រើសរើសប្រភេទជី។"
FERTILIZER_PRODUCT_PROMPT = "សូមបញ្ចូលឈ្មោះផលិតផល។"
FERTILIZER_AMOUNT_PROMPT = "សូមបញ្ចូលបរិមាណដែលបានប្រើ។\nឧទាហរណ៍៖ 20kg, one bag"
FERTILIZER_DATE_PROMPT = "សូមបញ្ចូលកាលបរិច្ឆេទប្រើប្រាស់។\nឧទាហរណ៍៖ 2026-04-21, today, yesterday"
FERTILIZER_CONFIRM_PROMPT = "សូមបញ្ជាក់ការបញ្ចូលជី។"
FERTILIZER_USED_FALLBACK = "សូមជ្រើសរើស បាទ/ចាស ឬ ទេ។"
FERTILIZER_KIND_FALLBACK = "សូមជ្រើសរើសប៊ូតុងប្រភេទជី។"
FERTILIZER_PRODUCT_FALLBACK = "សូមបញ្ចូលឈ្មោះផលិតផលម្ដងទៀត។"
FERTILIZER_AMOUNT_FALLBACK = "សូមបញ្ចូលបរិមាណម្ដងទៀត។\nឧទាហរណ៍៖ 20kg"
FERTILIZER_DATE_FALLBACK = "សូមបញ្ចូលកាលបរិច្ឆេទម្ដងទៀត។\nឧទាហរណ៍៖ 2026-04-21"
FERTILIZER_CONFIRM_FALLBACK = "សូមចុច [បញ្ជាក់] ឬថយក្រោយដើម្បីកែប្រែ។"
FERTILIZER_CONFIRMED_MESSAGE = "បានរក្សាទុកសេចក្តីព្រាងការបញ្ចូលជីក្នុងសម័យបច្ចុប្បន្ន។"
FERTILIZER_EDIT_MESSAGE = "សូមជ្រើសរើសធាតុជីដែលចង់កែប្រែ។"
FERTILIZER_EDIT_SELECTION_CONFIRMATION_MESSAGE = "អ្នកចង់ជ្រើសរើសធាតុជីដែលត្រូវកែម្ដងទៀតមែនទេ?\nចុច [{edit_button}] ហើយខ្ញុំនឹងបើកអេក្រង់ជ្រើសរើសការកែប្រែ។"
FERTILIZER_NOT_FOUND_MESSAGE = "មិនទាន់មានទិន្នន័យជីដែលបានរក្សាទុកទេ។\nសូមបំពេញការបញ្ចូលជាមុនសិន។"
FERTILIZER_REPAIR_USED_MESSAGE = "យើងនឹងបញ្ចូលស្ថានភាពប្រើជីឡើងវិញ។"
FERTILIZER_REPAIR_KIND_MESSAGE = "យើងនឹងបញ្ចូលប្រភេទជីឡើងវិញ។"
FERTILIZER_REPAIR_PRODUCT_MESSAGE = "យើងនឹងបញ្ចូលឈ្មោះផលិតផលជីឡើងវិញ។"
FERTILIZER_REPAIR_AMOUNT_MESSAGE = "យើងនឹងបញ្ចូលបរិមាណជីឡើងវិញ។"
FERTILIZER_REPAIR_DATE_MESSAGE = "យើងនឹងបញ្ចូលកាលបរិច្ឆេទប្រើជីឡើងវិញ។"
FERTILIZER_DIRECT_UPDATE_MESSAGE = "ខ្ញុំបានអនុវត្តការកែតាមភាសាធម្មជាតិហើយ។ សូមពិនិត្យហើយចុច [បញ្ជាក់]។"
YIELD_READY_PROMPT = "តើការប្រមូលផលរួចរាល់ហើយឬនៅ?"
YIELD_FIELD_PROMPT = "សូមជ្រើសរើស ឬ បញ្ចូលស្រែដែលបានប្រមូលផល។"
YIELD_AMOUNT_PROMPT = "សូមបញ្ចូលបរិមាណប្រមូលផល។\nឧទាហរណ៍៖ 320kg"
YIELD_DATE_PROMPT = "សូមបញ្ចូលកាលបរិច្ឆេទប្រមូលផល។\nឧទាហរណ៍៖ 2026-04-21"
YIELD_CONFIRM_PROMPT = "សូមបញ្ជាក់ការបញ្ចូលទិន្នផល។"
INPUT_RESOLVE_TARGET_PROMPT = "សូមជ្រើសរើសតម្លៃដែលត្រូវបញ្ជាក់ឲ្យបានច្បាស់។"
INPUT_RESOLVE_METHOD_PROMPT = "សូមជ្រើសរើសវិធីបញ្ចូល។\nអាចប្រើអត្ថបទ OCR ឬ សាកល្បងម្ដងទៀត។"
INPUT_RESOLVE_RAW_INPUT_PROMPT = "សូមបញ្ចូល ឬ ផ្ញើអត្ថបទដើមដែលត្រូវបញ្ជាក់។"
INPUT_RESOLVE_CANDIDATES_PROMPT = "សូមពិនិត្យបេក្ខភាព ហើយជ្រើសរើស 1-3 ឬ សាកល្បងម្ដងទៀត។"
INPUT_RESOLVE_DECISION_PROMPT = "សូមជ្រើសរើស បញ្ជាក់រួច សាកល្បងម្ដងទៀត ឬ ពិនិត្យដោយមនុស្ស។"


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "សូមបញ្ជាក់។\n"
        f"- ឈ្មោះ: {name}\n"
        f"- ទីលំនៅ: {residence}\n"
        f"- រាជធានី/ខេត្ត: {city}\n"
        f"- ខណ្ឌ/ស្រុក/ក្រុង: {district}\n"
        f"- ថ្ងៃខែឆ្នាំកំណើត: {birth_date}\n"
        "\nបើត្រឹមត្រូវ សូមជ្រើសរើស [បញ្ជាក់] មិនដូច្នោះទេ [កែប្រែ]។"
    )


def format_repair_confirmation(*, field_label: str, edit_button: str) -> str:
    return (
        f"អ្នកចង់កែធាតុ {field_label} មែនទេ?\n"
        f"ចុច [{edit_button}] ហើយខ្ញុំនឹងស្នើឲ្យបញ្ចូលតម្លៃនោះម្តងទៀត។"
    )


def format_change_preview(*, field_label: str, before_value: str, after_value: str) -> str:
    return (
        f"សូមពិនិត្យការផ្លាស់ប្តូរសម្រាប់ {field_label}។\n"
        f"- មុន: {before_value}\n"
        f"- ថ្មី: {after_value}"
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
        "នេះគឺជាប្រវត្តិដែលបានរក្សាទុករបស់អ្នក។\n"
        f"- ឈ្មោះ: {name}\n"
        f"- ទីលំនៅ: {residence}\n"
        f"- រាជធានី/ខេត្ត: {city}\n"
        f"- ខណ្ឌ/ស្រុក/ក្រុង: {district}\n"
        f"- ថ្ងៃខែឆ្នាំកំណើត: {birth_date}"
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
            "សូមបញ្ជាក់ការបញ្ចូលជី។\n"
            "- បានប្រើជី: ទេ\n\n"
            "បើត្រឹមត្រូវ សូមចុច [បញ្ជាក់]។"
        )
    return (
        "សូមបញ្ជាក់ការបញ្ចូលជី។\n"
        f"- បានប្រើជី: {'បាទ/ចាស' if used else '-'}\n"
        f"- ប្រភេទ: {kind_label}\n"
        f"- ផលិតផល: {product_name}\n"
        f"- បរិមាណ: {amount_text}\n"
        f"- កាលបរិច្ឆេទ: {applied_date}\n\n"
        "បើត្រឹមត្រូវ សូមចុច [បញ្ជាក់]។"
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
            "នេះគឺជាការបញ្ចូលជីដែលបានរក្សាទុក។\n"
            "- បានប្រើជី: ទេ"
        )
    return (
        "នេះគឺជាការបញ្ចូលជីដែលបានរក្សាទុក។\n"
        f"- បានប្រើជី: {'បាទ/ចាស' if used else '-'}\n"
        f"- ប្រភេទ: {kind_label}\n"
        f"- ផលិតផល: {product_name}\n"
        f"- បរិមាណ: {amount_text}\n"
        f"- កាលបរិច្ឆេទ: {applied_date}"
    )


WEATHER_CODE_LABELS = {
    0: "មេឃស្រឡះ",
    1: "ភាគច្រើនស្រឡះ",
    2: "មានពពកខ្លះ",
    3: "មានពពកច្រើន",
    45: "អ័ព្ទ",
    48: "អ័ព្ទកក",
    51: "ភ្លៀងរលឹមស្រាល",
    53: "ភ្លៀងរលឹម",
    55: "ភ្លៀងរលឹមខ្លាំង",
    56: "ភ្លៀងកកស្រាល",
    57: "ភ្លៀងកកខ្លាំង",
    61: "ភ្លៀងស្រាល",
    63: "ភ្លៀង",
    65: "ភ្លៀងខ្លាំង",
    66: "ភ្លៀងកកស្រាល",
    67: "ភ្លៀងកកខ្លាំង",
    71: "ព្រិលស្រាល",
    73: "ព្រិល",
    75: "ព្រិលខ្លាំង",
    77: "គ្រាប់ព្រិល",
    80: "ភ្លៀងបក់ស្រាល",
    81: "ភ្លៀងបក់",
    82: "ភ្លៀងបក់ខ្លាំង",
    85: "ព្រិលបក់ស្រាល",
    86: "ព្រិលបក់ខ្លាំង",
    95: "ព្យុះផ្គរ",
    96: "ព្យុះផ្គរជាមួយគ្រាប់ទឹកកកស្រាល",
    99: "ព្យុះផ្គរជាមួយគ្រាប់ទឹកកកខ្លាំង",
}


def weather_code_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"ស្ថានភាពមិនស្គាល់ ({code})")


def format_today_date(current: datetime) -> str:
    weekdays = ["ច", "អ", "ព", "ព្រ", "សុ", "ស", "អា"]
    weekday = weekdays[current.weekday()]
    return (
        "កាលបរិច្ឆេទថ្ងៃនេះ។\n"
        f"- កាលបរិច្ឆេទ: {current.strftime('%Y-%m-%d')} ({weekday})\n"
        f"- ម៉ោង: {current.strftime('%H:%M:%S')} KST"
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
        f"អាកាសធាតុបច្ចុប្បន្ននៅ {city}។\n"
        f"- ពេលសង្កេត: {observed_at.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"- ស្ថានភាព: {weather_label}\n"
        f"- សីតុណ្ហភាព: {temperature:.1f}°C\n"
        f"- មានអារម្មណ៍ដូចជា: {apparent_temperature:.1f}°C\n"
        f"- ល្បឿនខ្យល់: {wind_speed:.1f} km/h"
    )
