from dataclasses import dataclass


CITY_ALIASES = {
    "서울시": "서울특별시",
    "서울 특별시": "서울특별시",
    "서울": "서울특별시",
    "부산시": "부산광역시",
    "부산": "부산광역시",
    "대구시": "대구광역시",
    "대구": "대구광역시",
    "인천시": "인천광역시",
    "인천": "인천광역시",
    "광주시": "광주광역시",
    "광주": "광주광역시",
    "대전시": "대전광역시",
    "대전": "대전광역시",
    "울산시": "울산광역시",
    "울산": "울산광역시",
    "세종시": "세종특별자치시",
    "세종": "세종특별자치시",
    "경기도": "경기도",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주도": "제주특별자치도",
    "제주": "제주특별자치도",
}


@dataclass(frozen=True)
class DistrictRule:
    trigger: str
    city: str
    district: str | None = None
    ask_city_when_missing: bool = False
    ambiguous_options: tuple[str, ...] = ()


DISTRICT_RULES = [
    DistrictRule("서울 강남", "서울특별시", "강남구"),
    DistrictRule("서울 서초", "서울특별시", "서초구"),
    DistrictRule("서울 송파", "서울특별시", "송파구"),
    DistrictRule("강남", "서울특별시", "강남구", ask_city_when_missing=True),
    DistrictRule("서초", "서울특별시", "서초구", ask_city_when_missing=True),
    DistrictRule("송파", "서울특별시", "송파구", ask_city_when_missing=True),
    DistrictRule("수원 영통", "경기도", "수원시 영통구"),
    DistrictRule("영통", "경기도", "수원시 영통구", ask_city_when_missing=True),
    DistrictRule("수원 장안", "경기도", "수원시 장안구"),
    DistrictRule("장안", "경기도", "수원시 장안구", ask_city_when_missing=True),
    DistrictRule("성남 분당", "경기도", "성남시 분당구"),
    DistrictRule("분당", "경기도", "성남시 분당구"),
    DistrictRule("성남 수정", "경기도", "성남시 수정구"),
    DistrictRule("수정", "경기도", "성남시 수정구"),
    DistrictRule("고양 일산동", "경기도", "고양시 일산동구"),
    DistrictRule("일산동", "경기도", "고양시 일산동구"),
    DistrictRule("고양 일산서", "경기도", "고양시 일산서구"),
    DistrictRule("일산서", "경기도", "고양시 일산서구"),
    DistrictRule("고양 일산", "경기도", ambiguous_options=("고양시 일산동구", "고양시 일산서구")),
    DistrictRule("일산", "경기도", ambiguous_options=("고양시 일산동구", "고양시 일산서구")),
    DistrictRule("안양 동안", "경기도", "안양시 동안구"),
    DistrictRule("동안", "경기도", "안양시 동안구"),
    DistrictRule("안양 만안", "경기도", "안양시 만안구"),
    DistrictRule("만안", "경기도", "안양시 만안구"),
]


DISTRICT_EXAMPLES_BY_CITY = {
    "서울특별시": ["강남구", "서초구", "송파구"],
    "경기도": ["성남시 분당구", "수원시 영통구", "고양시 일산동구"],
}


def detect_city_alias(normalized_text: str) -> str | None:
    for alias in sorted(CITY_ALIASES, key=len, reverse=True):
        if alias in normalized_text:
            return CITY_ALIASES[alias]
    return None


def detect_district_rule(normalized_text: str) -> DistrictRule | None:
    for rule in sorted(DISTRICT_RULES, key=lambda item: len(item.trigger), reverse=True):
        if rule.trigger in normalized_text:
            return rule
    return None


def district_examples_for_city(city: str) -> list[str]:
    return DISTRICT_EXAMPLES_BY_CITY.get(city, ["강남구", "서초구", "송파구"])
