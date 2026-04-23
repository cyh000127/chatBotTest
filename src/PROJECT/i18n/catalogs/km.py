from datetime import datetime

BUTTON_TODAY_DATE = "កាលបរិច្ឆេទថ្ងៃនេះ"
BUTTON_TODAY_WEATHER = "អាកាសធាតុថ្ងៃនេះ"
BUTTON_PROFILE = "បញ្ចូលប្រវត្តិ"
BUTTON_FERTILIZER = "បញ្ចូលជី"
BUTTON_YIELD = "បញ្ចូលទិន្នផល"
BUTTON_MYFIELDS = "ពិនិត្យផ្ទាល់ខ្លួន"
BUTTON_INPUT_RESOLVE = "បកស្រាយតម្លៃ"
BUTTON_SUPPORT = "ជំនួយ"
BUTTON_HELP = "ជំនួយ"
BUTTON_BACK = "ថយក្រោយ"
BUTTON_CANCEL = "បោះបង់"
BUTTON_RESTART = "ចាប់ផ្តើមឡើងវិញ"
BUTTON_CONFIRM = "បញ្ជាក់"
BUTTON_EDIT = "កែប្រែ"
BUTTON_EDIT_START = "ចាប់ផ្តើមកែ"
BUTTON_KEEP_CURRENT = "ទុកដដែល"
BUTTON_APPLY_SUGGESTED_VALUE = "ប្រើតម្លៃនេះ"
BUTTON_ENTER_VALUE_DIRECTLY = "បញ្ចូលដោយដៃ"
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
BUTTON_YIELD_EDIT_READY = "ស្ថានភាពរួចរាល់"
BUTTON_YIELD_EDIT_FIELD = "ស្រែ"
BUTTON_YIELD_EDIT_AMOUNT = "បរិមាណទិន្នផល"
BUTTON_YIELD_EDIT_DATE = "ថ្ងៃប្រមូលផល"
BUTTON_PREV_YEARS = "12 ឆ្នាំមុន"
BUTTON_NEXT_YEARS = "12 ឆ្នាំបន្ទាប់"
BUTTON_FERTILIZER_KIND_COMPOUND = "ជីចម្រុះ"
BUTTON_FERTILIZER_KIND_UREA = "យូរ៉េ"
BUTTON_FERTILIZER_KIND_COMPOST = "ជីកំប៉ុស"
BUTTON_FERTILIZER_KIND_LIQUID = "ជីរាវ"

LANGUAGE_NAME = "ខ្មែរ"
LANGUAGE_MENU_MESSAGE = "សូមជ្រើសភាសា។"
LANGUAGE_CHANGED_MESSAGE = "បានប្តូរទៅភាសាខ្មែរ។"
AUTH_START_PROMPT = "សូមបញ្ចូលលេខសម្គាល់ចូល។\nឧទាហរណ៍៖ /start okccc5 ឬ okccc5"
AUTH_REQUIRED_MESSAGE = "ត្រូវចូលប្រើជាមុនសិន។\nសូមវាយ /start ហើយបញ្ចូលលេខសម្គាល់របស់អ្នក។"
AUTH_INVALID_MESSAGE = "លេខសម្គាល់មិនត្រឹមត្រូវ។ សូមបញ្ចូលម្ដងទៀត។"
AUTH_RETRY_LIMIT_MESSAGE = "បញ្ចូលខុស 2 ដងហើយ។\nសូមវាយ /start ម្តងទៀត។"
AUTH_WELCOME_MESSAGE = "សូមស្វាគមន៍ {user_name}!"
AUTH_ALREADY_LOGGED_IN_MESSAGE = "សូមស្វាគមន៍មកវិញ {user_name}!"

CITY_BUTTON_TO_KEY = {
    "សេអ៊ូល": "서울",
    "ប៊ូសាន": "부산",
    "ជេជូ": "제주",
}

START_MESSAGE = "បានចាប់ផ្តើម។\nសូមជ្រើសរើសសកម្មភាពខាងក្រោម។"
MAIN_MENU_MESSAGE = "ម៉ឺនុយមេ។\nសូមជ្រើសរើសសកម្មភាពខាងក្រោម។"
WEATHER_MENU_MESSAGE = "សូមជ្រើសទីក្រុងដើម្បីមើលអាកាសធាតុថ្ងៃនេះ។"
PROFILE_ENTRY_MESSAGE = (
    "ចាប់ផ្តើមបញ្ចូលប្រវត្តិ។\n"
    "ដំបូងសូមបញ្ចូលឈ្មោះ។"
)
CANCEL_MESSAGE = "បានចេញពីលំហូរបច្ចុប្បន្ន។\nសូមចាប់ផ្តើមឡើងវិញ ឬវាយ /start ម្តងទៀត។"
BACK_LIMIT_MESSAGE = "មិនមានជំហានមុនទេ។\nសូមជ្រើសម្តងទៀតពីម៉ឺនុយមេ។"
BACK_TO_MAIN_MESSAGE = "បានត្រឡប់ទៅជំហានមុន។\nសូមជ្រើសម្តងទៀត។"
BACK_TO_WEATHER_MESSAGE = "បានត្រឡប់ទៅជំហានជ្រើសអាកាសធាតុ។\nសូមជ្រើសទីក្រុងម្តងទៀត។"
BACK_GENERIC_MESSAGE = "បានត្រឡប់ទៅជំហានមុន។"
WEATHER_ERROR_MESSAGE = "មិនអាចយកព័ត៌មានអាកាសធាតុបាន។\nសូមព្យាយាមម្តងទៀតបន្តិចក្រោយ។"
UNKNOWN_COMMAND_MESSAGE = "ពាក្យបញ្ជានេះមិនទាន់គាំទ្រ។\nសូមជ្រើសធាតុខាងក្រោម ឬប្រើ /help។"
MYFIELDS_ENTRY_MESSAGE = "នេះគឺជាទំព័រពិនិត្យព័ត៌មានរបស់អ្នក។\nពេលនេះមានតែការមើលព័ត៌មាន និងត្រឡប់ក្រោយប៉ុណ្ណោះ។\nសូមជ្រើសសកម្មភាពខាងក្រោម ឬចាប់ផ្តើមម្ដងទៀតដោយ /start។"
INPUT_RESOLVE_ENTRY_MESSAGE = "នេះគឺជាទំព័រជួយបញ្ជាក់តម្លៃ។\nប្រព័ន្ធនឹងទាញយកតម្លៃសំខាន់ៗជាដំបូង។\nការជ្រើសចុងក្រោយ និងការពិនិត្យដោយមនុស្ស ធ្វើនៅជំហានក្រោយ។"
SUPPORT_ESCALATION_MESSAGE = "បានផ្ញើសំណើជំនួយទៅក្រុមប្រតិបត្តិការ។\nមិនបើកបង្អួចជជែកថ្មីទេ។\nអ្នកអាចបន្តក្នុងបង្អួចនេះ ឬប្រើ /help, /menu, /start។"
SUPPORT_HANDOFF_MESSAGE_RECORDED = "បានរក្សាទុកសារបន្ថែមក្នុងប្រវត្តិជំនួយ។\nអ្នកអាចបន្តទទួលការណែនាំក្នុងបង្អួចជជែកនេះ។\nប្រើ /start ប្រសិនបើចង់ចាប់ផ្តើមឡើងវិញ។"
SUPPORT_HANDOFF_CLOSED_MESSAGE = "ការជំនួយនេះបានបិទហើយ។\nបើត្រូវការ អ្នកអាចស្នើសុំម្ដងទៀតក្នុងបង្អួចជជែកនេះ។"

HELP_MESSAGE = (
    "ពាក្យបញ្ជាដែលអាចប្រើបាន៖\n"
    "- /start : ចាប់ផ្តើមពីដើម\n"
    "- /help : បង្ហាញជំនួយ\n"
    "- /menu : បើកម៉ឺនុយមេ\n"
    "- /profile : ចាប់ផ្តើមបញ្ចូលប្រវត្តិ\n"
    "- /myfields : មើលព័ត៌មានរបស់អ្នក\n"
    "- /fertilizer : ចាប់ផ្តើមបញ្ចូលជី\n"
    "- /yield : ចាប់ផ្តើមបញ្ចូលទិន្នផល\n"
    "- /resolve : ជួយបញ្ជាក់តម្លៃ\n"
    "- /support : បើកជំនួយ\n"
    "- /language : ប្តូរភាសា\n"
    "- ថយក្រោយ : ទៅជំហានមុន\n"
    "- ចាប់ផ្តើមឡើងវិញ : ចាប់ផ្តើមពីដើម"
)

FALLBACK_MESSAGES = {
    "default": "ខ្ញុំមិនទាន់យល់សំណើនេះទេ។\nសូមជ្រើសមុខងារខាងក្រោម។",
    "weather": "ខ្ញុំមិនទាន់យល់សំណើនេះទេ។\nសូមជ្រើសទីក្រុងខាងក្រោម ឬចុចថយក្រោយ។",
    "cancelled": "លំហូរនេះបានបិទហើយ។\nសូមជ្រើសមុខងារខាងក្រោមដើម្បីបន្ត។",
    "profile_input": "ខ្ញុំមិនទាន់អាចដំណើរការការបញ្ចូលប្រវត្តិនេះទេ។\nសូមជ្រើសធាតុប្រវត្តិខាងក្រោម ដើម្បីបន្ត ឬកែប្រែ។",
    "profile_followup": "ត្រូវការពិនិត្យបន្ថែម។\nសូមជ្រើសមុខងារខាងក្រោម។",
    "profile_confirm": "អ្នកនៅជំហានបញ្ជាក់ប្រវត្តិ។\nសូមជ្រើសបញ្ជាក់ ឬកែប្រែខាងក្រោម។",
    "fertilizer_input": "ខ្ញុំមិនទាន់អាចដំណើរការការបញ្ចូលជីនេះទេ។\nសូមជ្រើសធាតុជីខាងក្រោម ដើម្បីបន្ត ឬកែប្រែ។",
    "fertilizer_confirm": "អ្នកនៅជំហានបញ្ជាក់ជី។\nសូមជ្រើសបញ្ជាក់ ឬកែប្រែខាងក្រោម។",
    "yield_input": "ខ្ញុំមិនទាន់អាចដំណើរការការបញ្ចូលទិន្នផលនេះទេ។\nសូមជ្រើសជំហានខាងក្រោម ដើម្បីបន្ត។",
    "yield_confirm": "អ្នកនៅជំហានបញ្ជាក់ទិន្នផល។\nសូមជ្រើសបញ្ជាក់ ឬថយក្រោយខាងក្រោម។",
}
RECOVERY_GUIDANCE_SOFT = "ខ្ញុំនឹងពន្យល់ជាថ្មីថាត្រូវបញ្ចូលអ្វី។"
RECOVERY_GUIDANCE_GUIDED = "សូមធ្វើតាមជំហានខាងក្រោម ដើម្បីបន្ត។"
RECOVERY_GUIDANCE_ESCALATION_READY = "បើបញ្ហានេះកើតឡើងម្តងទៀត អ្នកអាចជ្រើសធាតុខាងក្រោមបាន។"
RECOVERY_MULTI_SLOT_CANDIDATE_HINT = "ខ្ញុំរកឃើញតម្លៃជាច្រើនក្នុងសារតែមួយ។ សូមពិនិត្យសេចក្តីព្រាងខាងក្រោមមុនបន្ត។"
RECOVERY_MULTI_SLOT_APPLIED_MESSAGE = "ខ្ញុំបានដាក់តម្លៃជាច្រើនទៅសេចក្តីព្រាងបច្ចុប្បន្ន។ សូមពិនិត្យខាងក្រោម។"
CHEAP_GATE_SUPPORT_ESCALATE_MESSAGE = (
    "សំណើនេះមើលទៅដូចជាការស្នើសុំជំនួយ ឬ ការគាំទ្រពីមនុស្ស។\n"
    "ខ្ញុំនឹងរក្សាទុកវាជាការបញ្ជូនទៅជំនួយ ហើយការណែនាំបន្តអាចបន្តក្នុងបង្អួចនេះ។\n"
    "សូមជ្រើសធាតុដែលពាក់ព័ន្ធខាងក្រោម ឬប្រើ /help។"
)
CHEAP_GATE_ADMIN_FOLLOWUP_MESSAGE = (
    "សំណើនេះមើលទៅជាករណីដែលត្រូវការការតាមដានបន្តពីអ្នកគ្រប់គ្រង។\n"
    "ខ្ញុំនឹងរក្សាទុកវាសម្រាប់ការត្រួតពិនិត្យប្រតិបត្តិការ ហើយការណែនាំបន្តអាចបន្តក្នុងបង្អួចនេះ។\n"
    "សូមជ្រើសធាតុដែលពាក់ព័ន្ធខាងក្រោមដើម្បីបន្ត។"
)
CHEAP_GATE_MANUAL_RESOLUTION_MESSAGE = (
    "ខ្ញុំបានពិនិត្យការបញ្ចូលនេះជាច្រើនដង ប៉ុន្តែជំហាននេះពិបាកដោះស្រាយដោយស្វ័យប្រវត្តិ។\n"
    "ខ្ញុំនឹងរក្សាទុកវាសម្រាប់ការពិនិត្យប្រតិបត្តិការដោយដៃ។\n"
    "សូមជ្រើសធាតុដែលពាក់ព័ន្ធខាងក្រោម ឬចាប់ផ្តើមម្ដងទៀតដោយ /menu ឬ /start។"
)

PROFILE_CONFIRMED_MESSAGE = "បានបញ្ជាក់ការបញ្ចូល។\nបានរក្សាទុកក្នុងសម័យនេះ។"
PROFILE_EDIT_MESSAGE = "សូមជ្រើសព័ត៌មានដែលចង់កែ។"
PROFILE_EDIT_SELECTION_CONFIRMATION_MESSAGE = "ចង់ជ្រើសធាតុប្រវត្តិម្តងទៀតមែនទេ?\nចុច [{edit_button}] ហើយខ្ញុំនឹងបើកអេក្រង់កែប្រែ។"
PROFILE_NOT_FOUND_MESSAGE = "មិនទាន់មានប្រវត្តិដែលបានរក្សាទុកទេ។\nសូមបំពេញប្រវត្តិជាមុនសិន។"
PROFILE_NAME_PROMPT = "សូមបញ្ចូលឈ្មោះ។"
PROFILE_RESIDENCE_PROMPT = "សូមបញ្ចូលទីលំនៅ។"
PROFILE_CITY_PROMPT = "សូមបញ្ចូលរាជធានី/ខេត្ត។\nឧទាហរណ៍៖ ភ្នំពេញ"
PROFILE_DISTRICT_PROMPT = "សូមបញ្ចូលខណ្ឌ/ស្រុក/ក្រុង។\nឧទាហរណ៍៖ ខណ្ឌ៧មករា, សែនសុខ"
PROFILE_BIRTH_YEAR_PROMPT = "សូមជ្រើសឆ្នាំកំណើតពីប៊ូតុង។"
PROFILE_BIRTH_MONTH_PROMPT = "សូមជ្រើសខែកំណើតពីប៊ូតុង។"
PROFILE_BIRTH_DAY_PROMPT = "សូមជ្រើសថ្ងៃកំណើតពីប៊ូតុង។"
PROFILE_NAME_FALLBACK = "សូមបញ្ចូលឈ្មោះម្ដងទៀត។"
PROFILE_RESIDENCE_FALLBACK = "សូមបញ្ចូលទីលំនៅម្ដងទៀត។"
PROFILE_CITY_FALLBACK = "សូមបញ្ចូលរាជធានី/ខេត្តឲ្យត្រឹមត្រូវម្ដងទៀត។"
PROFILE_DISTRICT_FALLBACK = "សូមបញ្ចូលខណ្ឌ/ស្រុក/ក្រុងឲ្យត្រឹមត្រូវម្ដងទៀត។"
PROFILE_BIRTH_YEAR_FALLBACK = "សូមជ្រើសឆ្នាំកំណើតពីប៊ូតុង។"
PROFILE_BIRTH_MONTH_FALLBACK = "សូមជ្រើសខែកំណើតពីប៊ូតុង។"
PROFILE_BIRTH_DAY_FALLBACK = "សូមជ្រើសថ្ងៃកំណើតពីប៊ូតុង។"
PROFILE_CONFIRM_FALLBACK = "សូមជ្រើសរើស [បញ្ជាក់] ឬ [កែប្រែ]។"
PROFILE_EDIT_SELECT_FALLBACK = "សូមជ្រើសព័ត៌មានដែលត្រូវកែពីប៊ូតុង។"
PROFILE_REPAIR_NAME_MESSAGE = "យើងនឹងបញ្ចូលឈ្មោះម្តងទៀត។"
PROFILE_REPAIR_RESIDENCE_MESSAGE = "យើងនឹងបញ្ចូលទីលំនៅម្តងទៀត។"
PROFILE_REPAIR_CITY_MESSAGE = "យើងនឹងបញ្ចូលរាជធានី/ខេត្តម្តងទៀត។"
PROFILE_REPAIR_DISTRICT_MESSAGE = "យើងនឹងបញ្ចូលខណ្ឌ/ស្រុក/ក្រុងម្តងទៀត។"
PROFILE_REPAIR_BIRTH_MESSAGE = "យើងនឹងបញ្ចូលថ្ងៃខែឆ្នាំកំណើតម្តងទៀត។\nសូមជ្រើសឆ្នាំកំណើត។"
PROFILE_DIRECT_UPDATE_MESSAGE = "បានកែតាមភាសាធម្មជាតិហើយ។ សូមពិនិត្យ ហើយចុច [បញ្ជាក់]។"
LLM_REPAIR_CANDIDATE_HINT = "ខ្ញុំគិតថាអ្នកចង់ប្ដូរទៅជា \"{candidate_value}\"។\nបើត្រឹមត្រូវ សូមចុច ចាប់ផ្តើមកែ។"
LLM_REPAIR_UNSUPPORTED_MESSAGE = "ខ្ញុំមិនទាន់ដឹងថាត្រូវកែធាតុណាទេ។\nសូមជ្រើសដោយផ្ទាល់ពីធាតុខាងក្រោម។"
LLM_REPAIR_LOW_CONFIDENCE_MESSAGE = "ខ្ញុំមិនទាន់ប្រាកដថាអ្នកចង់កែធាតុណាទេ។\nសូមជ្រើសដោយផ្ទាល់ពីធាតុខាងក្រោម។"
LLM_REPAIR_HUMAN_REVIEW_MESSAGE = (
    "សំណើនេះពិបាកកាត់ឲ្យសល់តែធាតុកែប្រែមួយដោយស្វ័យប្រវត្តិ។\n"
    "វាអាចត្រូវការមនុស្សពិនិត្យ ដូច្នេះសូមជ្រើសដោយផ្ទាល់ពីធាតុខាងក្រោម។"
)
LLM_REPAIR_RUNTIME_FAILURE_MESSAGE = (
    "ខ្ញុំបានព្យាយាមបកស្រាយដោយស្វ័យប្រវត្តិ ប៉ុន្តែឥឡូវនេះមិនទាន់ស្ថិតស្ថេរល្អទេ។\n"
    "សូមបន្តដោយជ្រើសដោយផ្ទាល់ពីធាតុខាងក្រោម។"
)

FERTILIZER_KIND_LABELS = {
    "compound": "ជីចម្រុះ",
    "urea": "យូរ៉េ",
    "compost": "ជីកំប៉ុស",
    "liquid": "ជីរាវ",
}
FERTILIZER_USED_LABEL_YES = "បានប្រើ"
FERTILIZER_USED_LABEL_NO = "មិនបានប្រើ"
FERTILIZER_USED_PROMPT = "តើបានប្រើជីឬនៅ?"
FERTILIZER_KIND_PROMPT = "សូមជ្រើសប្រភេទជី។"
FERTILIZER_PRODUCT_PROMPT = "សូមបញ្ចូលឈ្មោះផលិតផល។"
FERTILIZER_AMOUNT_PROMPT = "សូមបញ្ចូលបរិមាណដែលបានប្រើ។\nឧទាហរណ៍៖ 20kg, 1 ថង់"
FERTILIZER_DATE_PROMPT = "សូមបញ្ចូលថ្ងៃប្រើជី។\nឧទាហរណ៍៖ 2026-04-21, ថ្ងៃនេះ, ម្សិលមិញ"
FERTILIZER_CONFIRM_PROMPT = "សូមពិនិត្យការបញ្ចូលជី។"
FERTILIZER_USED_FALLBACK = "សូមជ្រើសរើស បាទ/ចាស ឬ ទេ។"
FERTILIZER_KIND_FALLBACK = "សូមជ្រើសប្រភេទជីពីប៊ូតុង។"
FERTILIZER_PRODUCT_FALLBACK = "សូមបញ្ចូលឈ្មោះផលិតផលម្ដងទៀត។"
FERTILIZER_AMOUNT_FALLBACK = "សូមបញ្ចូលបរិមាណម្ដងទៀត។\nឧទាហរណ៍៖ 20kg"
FERTILIZER_DATE_FALLBACK = "សូមបញ្ចូលថ្ងៃប្រើជីម្ដងទៀត។\nឧទាហរណ៍៖ 2026-04-21"
FERTILIZER_CONFIRM_FALLBACK = "សូមចុច [បញ្ជាក់] ឬថយក្រោយ ដើម្បីកែប្រែ។"
FERTILIZER_CONFIRMED_MESSAGE = "បានរក្សាទុកសេចក្តីព្រាងជីក្នុងសម័យនេះ។"
FERTILIZER_EDIT_MESSAGE = "សូមជ្រើសធាតុជីដែលចង់កែ។"
FERTILIZER_EDIT_SELECTION_CONFIRMATION_MESSAGE = "អ្នកចង់ជ្រើសធាតុជីម្តងទៀតមែនទេ?\nចុច [{edit_button}] ហើយខ្ញុំនឹងបើកអេក្រង់កែប្រែ។"
FERTILIZER_NOT_FOUND_MESSAGE = "មិនទាន់មានទិន្នន័យជីដែលបានរក្សាទុកទេ។\nសូមបំពេញការបញ្ចូលជាមុនសិន។"
FERTILIZER_REPAIR_USED_MESSAGE = "យើងនឹងបញ្ចូលស្ថានភាពប្រើជីម្តងទៀត។"
FERTILIZER_REPAIR_KIND_MESSAGE = "យើងនឹងបញ្ចូលប្រភេទជីម្តងទៀត។"
FERTILIZER_REPAIR_PRODUCT_MESSAGE = "យើងនឹងបញ្ចូលឈ្មោះផលិតផលជីម្តងទៀត។"
FERTILIZER_REPAIR_AMOUNT_MESSAGE = "យើងនឹងបញ្ចូលបរិមាណជីម្តងទៀត។"
FERTILIZER_REPAIR_DATE_MESSAGE = "យើងនឹងបញ្ចូលថ្ងៃប្រើជីម្តងទៀត។"
FERTILIZER_DIRECT_UPDATE_MESSAGE = "បានកែតាមភាសាធម្មជាតិហើយ។ សូមពិនិត្យ ហើយចុច [បញ្ជាក់]។"
YIELD_READY_PROMPT = "តើបានប្រមូលផលរួចហើយឬនៅ?"
YIELD_FIELD_PROMPT = "សូមជ្រើស ឬបញ្ចូលស្រែដែលបានប្រមូលផល។"
YIELD_AMOUNT_PROMPT = "សូមបញ្ចូលបរិមាណប្រមូលផល។\nឧទាហរណ៍៖ 320kg"
YIELD_DATE_PROMPT = "សូមបញ្ចូលថ្ងៃប្រមូលផល។\nឧទាហរណ៍៖ 2026-04-21, ថ្ងៃនេះ, ម្សិលមិញ"
YIELD_CONFIRM_PROMPT = "សូមពិនិត្យការបញ្ចូលទិន្នផល។"
YIELD_READY_FALLBACK = "សូមជ្រើសរើស បាទ/ចាស ឬ ទេ។"
YIELD_FIELD_FALLBACK = "សូមបញ្ចូលស្រែដែលបានប្រមូលផលម្ដងទៀត។"
YIELD_AMOUNT_FALLBACK = "សូមបញ្ចូលបរិមាណប្រមូលផលម្ដងទៀត។\nឧទាហរណ៍៖ 320kg"
YIELD_DATE_FALLBACK = "សូមបញ្ចូលថ្ងៃប្រមូលផលម្ដងទៀត។\nឧទាហរណ៍៖ 2026-04-21, ថ្ងៃនេះ, ម្សិលមិញ"
YIELD_CONFIRM_FALLBACK = "សូមចុច [បញ្ជាក់] ឬថយក្រោយ ដើម្បីកែប្រែ។"
YIELD_EDIT_MESSAGE = "សូមជ្រើសធាតុទិន្នផលដែលចង់កែ។"
YIELD_EDIT_SELECT_FALLBACK = "សូមជ្រើសធាតុដែលត្រូវកែ ឬ ចុច [ចាប់ផ្តើមកែ] ឬថយក្រោយ។"
YIELD_CONFIRMED_MESSAGE = "បានរក្សាទុកសេចក្តីព្រាងទិន្នផលក្នុងសម័យនេះ។"
INPUT_RESOLVE_TARGET_PROMPT = "សូមជ្រើសតម្លៃដែលចង់បញ្ជាក់។"
INPUT_RESOLVE_METHOD_PROMPT = "សូមជ្រើសវិធីបញ្ចូល។\nអាចប្រើអក្សរពីរូបភាព ឬសាកល្បងម្តងទៀត។"
INPUT_RESOLVE_RAW_INPUT_PROMPT = "សូមបញ្ចូល ឬផ្ញើអត្ថបទដើមដែលចង់ពិនិត្យ។"
INPUT_RESOLVE_CANDIDATES_PROMPT = "សូមពិនិត្យជម្រើស ហើយជ្រើស 1-3 ឬសាកល្បងម្តងទៀត។"
INPUT_RESOLVE_DECISION_PROMPT = "សូមជ្រើស បញ្ជាក់រួច សាកល្បងម្តងទៀត ឬឲ្យមនុស្សពិនិត្យ។"


def format_profile_confirmation(
    *,
    name: str,
    birth_date: str,
    city: str,
    district: str,
    residence: str,
) -> str:
    return (
        "សូមពិនិត្យទិន្នន័យ។\n"
        f"- ឈ្មោះ: {name}\n"
        f"- ទីលំនៅ: {residence}\n"
        f"- រាជធានី/ខេត្ត: {city}\n"
        f"- ខណ្ឌ/ស្រុក/ក្រុង: {district}\n"
        f"- ថ្ងៃខែឆ្នាំកំណើត: {birth_date}\n"
        "\nបើត្រឹមត្រូវ សូមចុច [បញ្ជាក់]។ បើមិនត្រឹមត្រូវ សូមចុច [កែប្រែ]។"
    )


def format_repair_confirmation(*, field_label: str, edit_button: str) -> str:
    return (
        f"ចង់កែធាតុ {field_label} មែនទេ?\n"
        f"ចុច [{edit_button}] ហើយខ្ញុំនឹងស្នើឲ្យបញ្ចូលម្តងទៀត។"
    )


def format_change_preview(*, field_label: str, before_value: str, after_value: str) -> str:
    return (
        f"សូមពិនិត្យការផ្លាស់ប្តូរ {field_label}។\n"
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
        "នេះជាប្រវត្តិដែលបានរក្សាទុក។\n"
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
            "សូមពិនិត្យការបញ្ចូលជី។\n"
            "- បានប្រើជី: ទេ\n\n"
            "បើត្រឹមត្រូវ សូមចុច [បញ្ជាក់]។"
        )
    return (
        "សូមពិនិត្យការបញ្ចូលជី។\n"
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
            "នេះជាការបញ្ចូលជីដែលបានរក្សាទុក។\n"
            "- បានប្រើជី: ទេ"
        )
    return (
        "នេះជាការបញ្ចូលជីដែលបានរក្សាទុក។\n"
        f"- បានប្រើជី: {'បាទ/ចាស' if used else '-'}\n"
        f"- ប្រភេទ: {kind_label}\n"
        f"- ផលិតផល: {product_name}\n"
        f"- បរិមាណ: {amount_text}\n"
        f"- កាលបរិច្ឆេទ: {applied_date}"
    )


def format_yield_confirmation(
    *,
    ready: bool | None,
    field_name: str,
    amount_text: str,
    harvest_date: str,
) -> str:
    return (
        "សូមពិនិត្យការបញ្ចូលទិន្នផល។\n"
        f"- រួចរាល់ឬនៅ: {'រួចរាល់' if ready else 'មិនទាន់រួចរាល់' if ready is False else '-'}\n"
        f"- ស្រែ: {field_name}\n"
        f"- បរិមាណ: {amount_text}\n"
        f"- កាលបរិច្ឆេទប្រមូលផល: {harvest_date}\n\n"
        "បើត្រឹមត្រូវ សូមចុច [បញ្ជាក់]។"
    )


def format_support_admin_reply(*, admin_message: str) -> str:
    return (
        "ចម្លើយពីក្រុមប្រតិបត្តិការ។\n"
        f"{admin_message}\n\n"
        "បើត្រូវការ សូមបន្តសរសេរក្នុងបង្អួចនេះ។"
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
    weekdays = ["ច", "អ", "ព", "ព្រហ", "សុ", "សៅ", "អាទិ"]
    weekday = weekdays[current.weekday()]
    return (
        "ថ្ងៃនេះ។\n"
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
