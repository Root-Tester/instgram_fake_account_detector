from typing import Any, List, Tuple

PROFILE_EXAMPLE = {
    "username": "sample_user",
    "full_name": "Sample User",
    "biography": "This account has a real profile and a short biography.",
    "external_url": "https://example.com",
    "profile_pic_url": "https://example.com/profile.jpg",
    "followers": 150,
    "followees": 180,
    "mediacount": 25,
    "posts_count": 25,
    "stories_count": 3,
    "is_private": False,
    "is_verified": False,
}

NUMERIC_FIELDS = ["followers", "followees", "mediacount", "posts_count", "stories_count"]
BOOLEAN_FIELDS = ["is_private", "is_verified"]


def normalize_bool(value: Any) -> int:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return 1
        if lowered in {"false", "0", "no", "n"}:
            return 0
    return int(bool(value))


def is_numeric(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_profile_data(profile_data: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(profile_data, dict):
        errors.append("JSON payload must be an object with profile fields.")
        return errors, warnings

    if not str(profile_data.get("username", "")).strip():
        warnings.append("Missing or empty username. The prediction will continue with a placeholder username.")

    for field in NUMERIC_FIELDS:
        if field not in profile_data or profile_data[field] is None or profile_data[field] == "":
            warnings.append(f"Field `{field}` is missing or empty and will default to 0.")
        elif not is_numeric(profile_data[field]):
            warnings.append(f"Field `{field}` is not numeric and will be converted to 0.")

    for field in BOOLEAN_FIELDS:
        value = profile_data.get(field)
        if value is None or value == "":
            warnings.append(f"Field `{field}` is missing and will default to False.")
        elif isinstance(value, str) and value.strip().lower() not in {"true", "false", "1", "0", "yes", "no", "y", "n"}:
            warnings.append(f"Field `{field}` has an unrecognized boolean value and will default to False.")

    return errors, warnings
