USER_DIRECTORY = {
    "okccc5": "최윤혁",
}


def authenticate_login_id(login_id: str) -> dict | None:
    normalized = login_id.strip()
    if not normalized:
        return None
    user_name = USER_DIRECTORY.get(normalized)
    if user_name is None:
        return None
    return {
        "login_id": normalized,
        "user_name": user_name,
    }
