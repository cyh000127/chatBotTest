from PROJECT.conversations.profile_intake import parser


def test_parse_profile_text_extracts_name_birth_and_residence():
    draft = parser.parse_profile_text("김민수 서울 강남 1998년 4월 20일")
    assert draft.name_candidate == "김민수"
    assert draft.birth_date_candidate == "1998-04-20"
    assert draft.city_candidate == "서울특별시"
    assert draft.district_candidate == "강남구"
    assert draft.parse_status == parser.PARSE_PARSED


def test_parse_profile_text_requests_followup_for_ambiguous_district():
    draft = parser.parse_profile_text("박서연 고양 일산 살아요")
    assert draft.name_candidate == "박서연"
    assert draft.city_candidate == "경기도"
    assert draft.district_candidate is None
    assert draft.pending_slot == "district_choice"
    assert draft.followup_options == ("고양시 일산동구", "고양시 일산서구")


def test_apply_followup_response_resolves_ambiguous_district():
    draft = parser.parse_profile_text("박서연 고양 일산 살아요")
    updated = parser.apply_followup_response(draft, "일산동구")
    assert updated.district_candidate == "고양시 일산동구"
    assert updated.parse_status == parser.PARSE_PARSED
